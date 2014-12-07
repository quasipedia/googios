#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
All the functions and utilities needed to run the wizard of GooGios.
'''
from __future__ import print_function

import os
import string
import logging

import pytz
import dateutil.parser

from strings import STRINGS
from utils import get_calendar_service
from calendars import get_available_calendars


DEFAULTS = {
    'time_shift': 0,
    'cache.timeout': 10,
    'cache.back': 0,
    'cache.forward': None,
    'cache.directory': os.getcwd(),
    'log.directory': os.getcwd(),
    'log.level': 'INFO',
}


def validate_positive(string_):
    '''Validation for integers'''
    try:
        ret = int(string_)
    except ValueError:
        return False
    return ret if ret >= 0 else False


def validate_simple_string(string_):
    '''Validate a string of only ASCII, digits and -._'''
    allowed = string.ascii_letters + string.digits + '_-.'
    if set(string_).issubset(allowed):
        return string_
    return False


def validate_datetime(string_):
    '''Validations for dates/times.'''
    try:
        date = dateutil.parser.parse(string_)
    except ValueError:
        return False
    return date.replace(tzinfo=pytz.UTC).isoformat()


def validate_directory(string_):
    '''Validation for directories.'''
    try:
        path = os.path.realpath(string_)
    except ValueError:
        print('That does not look like a valid path')
        return False
    if not os.path.exists(path):
        print('The directory does not exist')
        return False
    if not os.access(path, os.W_OK | os.X_OK):
        print('The directory is not writable')
        return False
    return path


def validate_log_level(string_):
    string_ = string_.upper()
    if string_ in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        return string_
    return False


def trust(string_):
    '''Skip validation entirely, but output a message.'''
    print('\n***********************************************************')
    print('I will trust you on that one, as it is too complex to check!')
    print('***********************************************************')
    return string_


def ask(string_id, question=None, validator=None, msg_args=()):
    '''Helper for display messages/asking questions.'''
    print('\n', STRINGS[string_id].format(*msg_args).strip(), '\n')
    if question is None:
        return
    if string_id in DEFAULTS:
        question = '{} [{}]'.format(question, DEFAULTS[string_id])
    while True:
        answer = raw_input(question + '  ').strip()
        if answer:
            validated = validator(answer)
            if validated is not False:
                return validated
        if not answer and string_id in DEFAULTS:
            return DEFAULTS[string_id]


def pick_calendar():
    '''Return the ID of the chosen calendar'''
    cal_service = get_calendar_service()
    available = get_available_calendars(cal_service)
    choices = {}
    lines = []
    for counter, (cid, description) in enumerate(available.items(), 1):
        choices[str(counter)] = cid
        lines.append('{:<3}: {}'.format(counter, description))
    msg_args = '\n'.join(lines)
    question = 'Pick a number between 1 and {}'.format(counter)
    validator = lambda x: x if x in choices else False
    selected = ask('cid', question, validator, [msg_args])
    return choices[selected]


def pick_time_shift():
    '''Ruturn the time-shift for the roster.'''
    allowed = list(map(str, range(24)))
    return ask('time_shift', 'Choose an integer value between 0 and 23',
               lambda x: x if x in allowed else False)


def wizard():
    '''Run the complete wizard.'''
    logging.disable(logging.ERROR)
    ask('welcome')
    config = {
        'cid': pick_calendar(),
        'name': ask('name', 'Choose a name', validate_simple_string),
        'time_shift': pick_time_shift(),
        'cache.timeout': ask('cache.timeout',
                             'Choose an integer amount of minutes',
                             validate_positive),
        'cache.back': ask('cache.back', 'Choose an integer number of days',
                          validate_positive),
        'cache.forward': ask('cache.forward',
                             'Choose an integer number of days',
                             validate_positive),
        'cache.directory': ask('cache.directory', 'Choose a directory',
                               validate_directory),
        'fallback.email': ask('fallback.email', 'Enter a valid email address',
                              trust),
        'fallback.phone': ask('fallback.phone',
                              'Enter a valid telephone number',
                              trust),
        'log.directory': ask('log.directory', 'Choose a directory',
                             validate_directory),
        'log.level': ask('log.level', 'Choose a level', validate_log_level),
    }
    ask('done', msg_args=[config['name'], os.getcwd()])
    logging.disable(logging.NOTSET)
    return config
