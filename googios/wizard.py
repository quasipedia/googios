#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
All the functions and utilities needed to run the wizard of GooGios.
'''
from __future__ import print_function

import os
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


def display(string_id, *args):
    '''Helper for printing out wizard questions.'''
    print(STRINGS[string_id].format(*args).strip(), '\n')
    if string_id in DEFAULTS:
        print('Default is {}'.format(DEFAULTS[string_id]))


def ask(question, validator):
    '''Helper for keep asking the same question until a valid answer.'''
    while True:
        answer = raw_input(question + ' ')
        if validator(answer):
            return answer


def pick_calendar():
    '''Return the ID of the chosen calendar'''
    cal_service = get_calendar_service()
    available = get_available_calendars(cal_service)
    display('pick_calendar')
    choices = {}
    for counter, (cid, description) in enumerate(available.items(), 1):
        choices[str(counter)] = cid
        print('{:<2}: {}'.format(counter, description))
    print()
    selected = ask('Pick a number between 1 and {}'.format(counter),
                   lambda x: x in choices)
    return choices[selected]


def wizard():
    '''Run the complete wizard.'''
    logging.disable(logging.ERROR)
    print()
    display('welcome')
    config = {
        'cid': pick_calendar()
    }
    logging.disable(logging.NOTSET)
    return config
