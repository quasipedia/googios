#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Manage your Nagios on-call roster with Google apps.

Usage:
    googios setup
    googios <roster> current [start end name email phone] [--echo]
    googios <roster> query [--start=<start> --end=<end>  | --at=<at>] [--echo]
    googios <roster> report [<fuzzy> | <start> <end>] [--echo]
    googios <roster> update [--echo]
    googios <roster> runway [--echo]
    googios <roster> status [--echo]

Options:
    -h --help          Show this screen.
    --version          Show version.
    -e --echo          Log to stdout/stderr rather than to the usual file.
    -a --at=<at>       Moment (UTC) in time
    -f --start=<start>   Minimum ending (UTC) of a shift.
    -t --end=<end>       Maximum starting (UTC) of a shift.

The roster:

    The roster can either be the roster's human-friendly name (if the script
    is ran from the directory with its configuration file) or the full path
    to the configuration file.

Sub- commands:

    setup    Run a wizard for the configuration file generation.

    current  Information on the current person on duty.  It is possible to
             limit what information is given by white-listing any number of the
             5 fields (start, end, name, email, phone).

    query    All shifts between <start> and <end>, or at the <at> moment. All
             parameters are datetime.

    report   Similar to query, but meant for human consumption and with shifts
             grouped by working day (uses the time_shift value from the
             configuration).
                By default it output the report of the previous month, but this
             can be altered with either the <start> and <end> parameters or
             with <fuzzy>, which try to fuzzy-match expressions like "october"
             or "apr 2012".
                `report` groups shifts by day, taking in account the
             "roster.time_shift" parameter in the configuration file.

    update   Force to rebuild the cache with live data.

    runway   Return the number of full days for which shifts have been
             *cached* from now onwards.  Note that this subcommand operates on
             the cache (i.e.: not on the live data), the rationale being that
             `runaway` should tell you what you can count on, even in case of
             loss of connectivity.
                 If the time series has "holes" in it, `runway` will return
             the number of full cached days until the first hole, even if more
             shifts have been scheduled afterwards.

    status   Perform a sanity check of the roster.  Print stats and - in case
             of problems - exit with a non-zero status.
'''
import os
import json
import logging
import datetime
from collections import defaultdict

import pytz
from dateutil.relativedelta import relativedelta
from docopt import docopt

from roster import Roster, Shift
from wizard.wizard import run_wizard
from utils import (
    log,
    log_format,
    log_stream_handler,
    get_calendar_service,
    get_people_client,
    dtfy
)


def load_config(string_):
    '''Load configuration from file.'''
    try:
        with open('{}.conf'.format(string_)) as file_:
            return json.load(file_)
    except IOError:
        pass
    try:
        with open(string_) as file_:
            return json.load(file_)
    except IOError:
        # The following will always be logged on screen, obviously...
        log.critical('Could not open configuration for "{}"'.format(string_))
        exit(os.EX_DATAERR)


def modify_logger(cli, config):
    '''Modify the logger so as '''
    if cli['--echo']:
        return
    log.removeHandler(log_stream_handler)
    log_level = config['log.level']
    log_dir = config['log.directory']
    log_fname = os.path.join(log_dir, '{}.log'.format(config['roster.name']))
    log_file_handler = logging.FileHandler(log_fname)
    log_file_handler.setFormatter(log_format)
    log.addHandler(log_file_handler)
    log.setLevel(log_level)


def get_roster(config):
    '''Return the roster to perform script operations on.'''
    now = datetime.datetime.now(tz=pytz.UTC)
    min_end = (now - datetime.timedelta(days=config['cache.back'])).isoformat()
    if config['cache.forward'] is not None:
        max_start = now + datetime.timedelta(days=config['cache.forward'])
        max_start = max_start.isoformat()
    else:
        max_start = None
    return Roster(
        name=config['roster.name'],
        cid=config['roster.cid'],
        cal_service_clbk=get_calendar_service,
        ppl_client_clbk=get_people_client,
        min_end=min_end,
        max_start=max_start,
        all_day_offset=config['roster.time_shift'],
        cache_timeout=config['cache.timeout'],
        cache_directory=config['cache.directory']
    )


def current(roster, cli, config):
    '''Print information on the current shift in the roster.'''
    # roster.current return a *list* of all the people on duty
    shifts = roster.current
    if len(shifts) == 1:
        [current] = shifts
    elif len(shifts) == 0:
        log.error('Nobody is on duty.')
        now = datetime.datetime.now(tz=pytz.UTC)
        current = Shift(now, now, 'Fallback Team',
                        config['fallback.email'], config['fallback.phone'])
    else:
        log.error('Several people where on duty, picking the first one.')
        for counter, shift in enumerate(shifts, 1):
            log.error('On duty #{}: {}'.format(counter, shift))
        current = shifts[0]
    # Compute what fields to output
    fields = ('start', 'end', 'name', 'email', 'phone')
    mask = []
    for attr_name in fields:
        mask.append(cli[attr_name])
    if not any(mask):
        mask = [True] * 5  # No explicit field, means all fields
    bits = [val for val, flag in zip(current.as_string_tuple, mask) if flag]
    print('\t'.join(bits))


def query(roster, cli, config):
    '''Print a roster query result.'''
    start = cli['--start'] or cli['--at']
    end = cli['--end'] or cli['--at']
    if end < start:
        msg = 'Tried to query roster for a negative timespan ({} to {})'
        log.critical(msg.format(start, end))
        exit(os.EX_DATAERR)
    for shift in roster.query(start, end):
        print '\t'.join(shift.as_string_tuple)


def report(roster, cli, config):
    '''Print a human-friendly report about a time-slice of the roster.'''
    time_zone = config['roster.time_zone']
    # We use datetimes even if the ultimate goal is operate at date level as
    # we need to preserve the timezone information all along
    fuzzy = cli['<fuzzy>']
    # Fuzzy should be interpreted as always indicating a month.
    if fuzzy:
        try:
            start = fuzzy.replace(day=1)
            end = start + relativedelta(months=1, days=-1)
        except Exception as e:
            log.critical('Cannot parse <fuzzy> parameter "{}"'.format(fuzzy))
            log.exception(e.message)
            raise
    # A range can be whatever
    elif cli['<start>']:
        start = cli['<start>']
        end = cli['<end>']
        if start > end:
            msg = 'Tried to generate a report for negative timespan ({} to {})'
            log.critical(msg.format(start, end))
            exit(os.EX_DATAERR)
    else:
        now = datetime.datetime.now(tz=pytz.timezone(time_zone))
        start = now.replace(day=1) + relativedelta(months=-1)
        end = start + relativedelta(months=1, days=-1)
    data = roster.report(start, end)
    weekdays = defaultdict(int)
    weekends = defaultdict(int)
    for day, people in data:
        target = weekdays if day.weekday() < 5 else weekends
        for person in people:
            target[person] += 1
    print('\n             O N - C A L L   R O S T E R')
    print('=====================================================')
    print('              {} - {}\n\n'.format(start.strftime('%d %b %Y'),
                                             end.strftime('%d %b %Y')))
    for row in data:
        print('  {:<20}{}'.format(row[0].strftime('%d %b %Y, %a'),
                                  ', '.join(row[1])))
    print('\n\n                      SUMMARY')
    print('-----------------------------------------------------')
    print('  Name                    Weekdays  Weekends  Total')
    print('-----------------------------------------------------')
    names = sorted(list(set(weekends.keys() + weekdays.keys())))
    template = '  {:<26}{:>3}{:>10}{:>8}'
    for name in names:
        wd = weekdays[name]
        we = weekends[name]
        print(template.format(name, wd or '-', we or '-', wd + we))
    print('-----------------------------------------------------\n')


def runway(roster, cli, config):
    '''Print the number of days in the future before a shift-less moment.'''
    print (roster.runway - datetime.datetime.now(tz=pytz.UTC)).days


def status(roster, cli, config):
    '''Print statistics on the roster.  Exit with error code if problems.'''
    stats = roster.stats()
    human_friendly = lambda td: (None if td is None
                                 else td.isoformat()[:16].replace('T', ' '))
    min_end = human_friendly(stats['roster.min_end'])
    max_start = human_friendly(stats['roster.max_start'])
    cache_age = datetime.datetime.now(tz=pytz.UTC) - stats['cache.timestamp']
    cache_age = int(cache_age.total_seconds() / 60)
    cache_size = stats['cache.size']
    cache_end = human_friendly(stats['cache.end'])
    if stats['cache.fragments'] == 1:
        integrity = 'OK'
        exit_status = os.EX_OK
    elif stats['cache.fragments'] == 0:
        integrity = 'Empty'
        exit_status = os.EX_DATAERR
    else:
        integrity = 'Broken in {}'.format(stats['cache.fragments'])
        exit_status = os.EX_DATAERR
    if stats['cache.end'] == stats['cache.first_hole']:
        first_hole = 'n/a'
    elif stats['cache.first_hole'] < datetime.datetime.now(tz=pytz.UTC):
        first_hole = 'Right now'
    else:
        first_hole = human_friendly(stats['cache.first_hole'])
    print('\n          R O S T E R   S T A T I S T I C S')
    print('=====================================================\n\n')
    print('  `min_end` query parameter    :  {}'.format(min_end))
    print('  `max_start` query parameter  :  {}'.format(max_start))
    print('  Cache age                    :  {} mins'.format(cache_age))
    print('  Cache size                   :  {} shifts'.format(cache_size))
    print('  Cache upper limit            :  {}'.format(cache_end))
    print('  Cache integrity              :  {}'.format(integrity))
    print('  Cache first hole             :  {}\n'.format(first_hole))
    exit(exit_status)


def main():
    cli = docopt(__doc__, version='0.1')
    if cli['setup']:
        run_wizard()
        exit(os.EX_OK)
    config = load_config(cli['<roster>'])
    for key in ('--start', '--end', '--at', '<start>', '<end>', '<fuzzy>'):
        if cli[key] is not None:
            cli[key] = dtfy(cli[key], tz=config['roster.time_zone'])
    modify_logger(cli, config)
    roster = get_roster(config)
    if cli['current'] is True:
        current(roster, cli, config)
    elif cli['query'] is True:
        query(roster, cli, config)
    elif cli['report'] is True:
        report(roster, cli, config)
    elif cli['update']:
        roster.update_cache()
    elif cli['runway'] is True:
        runway(roster, cli, config)
    elif cli['status'] is True:
        status(roster, cli, config)
    else:
        log.critical('Something is odd, you should never hit this point...')
        exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    main()
