#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Manage your Nagios on-call roster with Google apps.

Usage:
    googios setup
    googios <roster> who [from to name email phone --at=<at>  --echo]
    googios <roster> query [--from=<from> --to=<to>  --echo]
    googios <roster> report [<fuzzy> | --from=<from> --to=<to>] [--echo]
    googios <roster> runway [--echo]
    googios <roster> check [--echo]

Options:
    -h --help          Show this screen.
    --version          Show version.
    -e --echo          Log to stdout/stderr rather than to the usual file.
    -a --at=<at>       Moment in time (datetime)
    -f --from=<from>   Minimum ending datetime of a shift.
    -t --to=<to>       Maximum starting datetime of a shift.

The roster:

    The roster can either be the roster's human-friendly name (if the script
    is ran from the directory with its configuration file) or the full path
    to the configuration file.

Sub- commands:

    setup    Run a wizard for the configuration file generation.
    who      Information on the current person(s) on duty.  It is possible to
             limit what information is given by white-listing any number of the
             5 fields (from, to, name, email, phone).  It is also possible to
             specify a different moment in time with <at>.
    query    All shifts between <from> and <to>.
    report   Similar to query, but with shifts grouped by working day
             (uses the time_shift value from the configuration).  By default it
             output the report of the previous month, but this can be altered
             with either the <from> and <to> parameters or with <magic>, which
             try to fuzzy-match expressions like "october" or "apr 2012".
    runway   Return the number of *full* days for which the roster is covered.
    check    Perform a sanity check of the roster.  Print an informative
             message and - in case of problems - exit with a non-zero status.
'''
import os
import json

from docopt import docopt

from roster import Roster
from wizard.wizard import run_wizard
from utils import (
    log,
    get_calendar_service,
    get_people_client,
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
    log.error('Not yet implemented')


def get_roster(config):
    '''Return the roster to perform script operations on.'''
    print('fooo')
    exit()
    roster = Roster(config['name'], config[''])


def who(roster, cli):
    raise NotImplementedError()


def query(roster, cli):
    raise NotImplementedError()


def report(roster, cli):
    raise NotImplementedError()


def runway(roster, cli):
    raise NotImplementedError()


def check(roster, cli):
    raise NotImplementedError()


def main():
    cli = docopt(__doc__, version='0.1')
    if cli['setup']:
        run_wizard()
        exit(os.EX_OK)
    configuration = load_config(cli['<roster>'])
    modify_logger(configuration)
    roster = get_roster()
    if cli['who'] is True:
        who(roster)
    elif cli['query'] is True:
        query(roster)
    elif cli['report'] is True:
        report(roster)
    elif cli['runway'] is True:
        runway(roster)
    elif cli['check'] is True:
        check(roster)
    else:
        log.critical('Something is odd, you should never hit this point...')
        exit(os.EX_SOFTWARE)


if __name__ == '__main__':
    main()
