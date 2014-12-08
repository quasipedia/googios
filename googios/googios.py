#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Manage your Nagios on-call roster with Google apps.

Usage:
    googios setup
    googios <roster> current [start end name email phone] [--echo]
    googios <roster> query [--start=<start> --end=<end>  | --at=<at>] [--echo]
    googios <roster> report [<fuzzy> | --start=<start> --end=<end>] [--echo]
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
    query    All shifts between <start> and <end>, or at the <at> moment.
    report   Similar to query, but with shifts grouped by working day
             (uses the time_shift value from the configuration).  By default it
             output the report of the previous month, but this can be altered
             with either the <start> and <end> parameters or with <magic>,
             which try to fuzzy-match expressions like "october" or "apr 2012".
    update   Force to rebuild the cache with live data.
    runway   Return the number of *full* days for which the roster is covered.
    status   Perform a sanity check of the roster.  Print stats and - in case
             of problems - exit with a non-zero status.
'''
import os
import json
import datetime

import pytz
from docopt import docopt

from roster import Roster, Shift
from wizard.wizard import run_wizard
from utils import (
    log,
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


def modify_logger(configuration):
    '''Modify the logger so as '''
    log.error('Logging modification yet implemented')


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


def current(roster, cli):
    # roster.current return a *list* of all the people on duty
    shifts = roster.current
    if len(shifts) == 1:
        [current] = shifts
    elif len(shifts) == 0:
        log.error('Nobody is on duty.')
        now = datetime.datetime.now(tz=pytz.UTC)
        current = Shift(now, now, 'Fallback Team',
                        cli['fallback.email'], cli['fallback.phone'])
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


def query(roster, cli):
    start = cli['--start'] or cli['--at']
    end = cli['--end'] or cli['--at']
    if end < start:
        msg = 'Tried to query roster for a negative timespan ({} to {})'
        log.error(msg.format(start, end))
        exit(os.EX_DATAERR)
    for shift in roster.query(start, end):
        print '\t'.join(shift.as_string_tuple)


def report(roster, cli):
    raise NotImplementedError()


def runway(roster, cli):
    raise NotImplementedError()


def status(roster, cli):
    raise NotImplementedError()


def main():
    cli = docopt(__doc__, version='0.1')
    for key in ('--start', '--end', '--at'):
        cli[key] = None if cli[key] is None else dtfy(cli[key])
    print cli
    if cli['setup']:
        run_wizard()
        exit(os.EX_OK)
    config = load_config(cli['<roster>'])
    modify_logger(config)
    roster = get_roster(config)
    if cli['current'] is True:
        current(roster, cli)
    elif cli['query'] is True:
        query(roster, cli)
    elif cli['report'] is True:
        report(roster, cli)
    elif cli['update']:
        roster.update_cache()
    elif cli['runway'] is True:
        runway(roster, cli)
    elif cli['status'] is True:
        status(roster, cli)
    else:
        log.critical('Something is odd, you should never hit this point...')
        exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    main()
