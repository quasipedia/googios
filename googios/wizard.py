#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
All the functions and utilities needed to run the wizard of GooGios.
'''
from __future__ import print_function

import os
import string
import logging

from strings import STRINGS
from utils import get_calendar_service, first_day_of_previous_month
from calendars import get_available_calendars


DEFAULTS = {
    'time_shift': 0,
    'cache.timeout': 10,
    'cache.min_end': first_day_of_previous_month().isoformat(),
    'cache.max_start': None,
    'cache.directory': os.getcwd(),
    'log.directory': os.getcwd(),
    'log.level': 'INFO',
}


def ask(string_id, question=None, validator=None, msg_args=()):
    '''Helper for display messages/asking questions.'''
    print('\n', STRINGS[string_id].format(*msg_args).strip(), '\n')
    if question is None:
        return
    if string_id in DEFAULTS:
        question = '{} [{}]'.format(question, DEFAULTS[string_id])
    while True:
        answer = raw_input(question + '  ').strip()
        if validator(answer):
            return answer
        if string_id in DEFAULTS and answer == '':
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
    validator = lambda x: x in choices
    selected = ask('cid', question, validator, [msg_args])
    return choices[selected]


def pick_name():
    '''Return the human-friendly name for the roster.'''
    allowed = string.ascii_letters + string.digits + '_-.'
    return ask('name', 'Choose a name', lambda x: all(l in allowed for l in x))


def pick_time_shift():
    '''Ruturn the time-shift for the roster.'''
    allowed = list(map(str, range(24)))
    return int(ask('time_shift', 'Choose an integer value between 0 and 23',
                   lambda x: x in allowed))


def wizard():
    '''Run the complete wizard.'''
    logging.disable(logging.ERROR)
    ask('welcome')
    config = {
        'cid': pick_calendar(),
        'name': pick_name(),
        'time_shift': pick_time_shift(),
    }
    logging.disable(logging.NOTSET)
    return config
