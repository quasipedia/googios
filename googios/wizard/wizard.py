#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
All the functions and utilities needed to run the wizard of GooGios.
'''
from __future__ import print_function

import os
import json
import string
from collections import namedtuple
from functools import partial

from clint.textui import prompt, puts, colored, indent
from clint.textui.validators import ValidationError

from strings import STRINGS, FINAL_DISCLAIMER
from ..utils import get_calendar_service
from ..calendars import get_available_calendars

Question = namedtuple('Question', 'text default validator')

QUESTIONS = {
    'oauth.directory': Question(
        'Enter a directory', os.getcwd(), 'validate_oauth_directory'),
    'roster.name': Question(
        'Name your roster', None, 'validate_simple_string'),
    'cache.timeout': Question(
        'Enter the timeout in minutes.', '10', 'validate_positive'),
    'cache.past': Question(
        'Number of days to cache in the past', '0', 'validate_positive'),
    'cache.future': Question(
        'Number of days to cache in the future', '', 'validate_positive'),
    'cache.directory': Question(
        'Enter a directory', os.getcwd(), 'validate_directory'),
    'fallback.email': Question(
        'Enter a valid email address', None, 'trust'),
    'fallback.phone': Question(
        'Enter a valid phone number', None, 'trust'),
    'log.directory': Question(
        'Enter a a directory', os.getcwd(), 'validate_directory'),
}

red = lambda text: puts(colored.red(text))
green = lambda text: puts(colored.green(text))
yellow = lambda text: puts(colored.yellow(text))


class Wizard(object):

    '''A wizard that will guide the user in creating a configuration file.'''

    def __init__(self):
        self.current_step = 0
        self.wizard_lenght = len(STRINGS)
        self.config = {}

    def validate_oauth_directory(self, string_):
        '''Validate the directory of the OAuth files.'''
        string_ = self.validate_directory(string_)
        for fname in ('2-legged.oauth', '3-legged.oauth'):
            full = os.path.join(string_, fname)
            if not os.path.exists(full):
                msg = 'At least one of the two required OAuth files is missing'
                raise ValidationError(msg)
        return os.path.realpath(string_)

    def validate_positive(self, string_):
        '''Validation for integers'''
        if string_ is '':
            return None
        try:
            converted = int(string_)
        except ValueError:
            raise ValidationError('Could not convert to integer')
        if converted < 0:
            raise ValidationError('Negative values are not allowed')
        return converted

    def validate_simple_string(self, string_):
        '''Validate a string of only ASCII, digits and -._'''
        allowed = string.ascii_letters + string.digits + '_-.'
        if set(string_).issubset(allowed):
            return string_
        raise ValidationError('Non-legal characters detected')

    def validate_options(self, string_, options):
        '''Validate a value among a set of allowed options.'''
        # Given the `options` parameter this is to be used as a closure
        if string_ not in options:
            raise ValidationError('{} is not a valid option'.format(string_))
        return string_

    def validate_directory(self, string_):
        '''Validation for directories.'''
        try:
            path = os.path.realpath(string_)
        except ValueError:
            raise ValidationError('Not a valid path')
        if not os.path.exists(path):
            raise ValidationError('The directory does not exist')
        if not os.access(path, os.W_OK | os.X_OK):
            raise ValidationError('The directory is not writable')
        return path

    def validate_log_level(self, string_):
        string_ = string_.upper()
        if string_ in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            return string_
        raise ValidationError('Must use one of the 5 logging levels')

    def trust(self, string_):
        '''Skip validation entirely, but output a message.'''
        yellow('I will trust you on that one, as it is too complex to check!')
        return string_

    def pre_flight_checks(self):
        '''Verify the wizard is runnable.'''
        self.current_dir = os.getcwd()
        if not self.validate_directory(self.current_dir):
            red('Attempt to run the wizard from a non-writable directory')
            exit(os.EX_IOERR)

    def pick_calendar(self):
        '''Save the ID of the chosen calendar and its locale'''
        self.current_step += 1
        cal_service = get_calendar_service()
        available = get_available_calendars(cal_service)
        options = {}
        lines = []
        for counter, (cid, description) in enumerate(available.items(), 1):
            options[str(counter)] = cid
            lines.append('{:<3}: {}'.format(counter, description))
        bullet_list = '\n'.join(lines)
        self.display('roster.cid', [bullet_list])
        question = 'Pick a number between 1 and {}'.format(counter)
        validator = partial(self.validate_options, options=options.keys())
        selection = prompt.query(question, None, [validator])
        cid = options[selection]
        cal_metadata = cal_service.calendars().get(calendarId=cid).execute()
        self.config['roster.cid'] = cid
        self.config['roster.time_zone'] = cal_metadata['timeZone']

    def pick_time_shift(self):
        '''Save the time-shift for the roster.'''
        self.current_step += 1
        self.display('roster.time_shift', ())
        options = list(map(str, range(24)))
        question = 'Choose a number of hours (integer between 0 and 23)'
        validator = partial(self.validate_options, options=options)
        choice = prompt.query(question, '0', [validator])
        self.config['roster.time_shift'] = int(choice)

    def pick_log_level(self):
        '''Save the log level for the roster.'''
        self.current_step += 1
        self.display('log.level', ())
        options = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        question = 'Select one of the 5 allowed values'
        validator = partial(self.validate_options, options=options)
        choice = prompt.query(question, 'INFO', [validator])
        self.config['log.level'] = choice

    def finish(self):
        '''Save the configuration and generate the 3-legged token.'''
        # Save the configuration
        self.current_step += 1
        self.display('credentials', ())
        name = self.config['roster.name']
        self.config_fname = '{}.config'.format(name)
        with open(self.config_fname, 'w') as file_:
            json.dump(self.config, file_, sort_keys=True, indent=4)
        # Generate the credentials
        from ..googios import get_roster  # Avoid circular import
        get_roster(self.config).update_cache()

    def display(self, string_id, msg_args):
        '''Display a step messages'''
        header = '\n===== STEP {} of {} ' + '=' * 80
        green(header.format(self.current_step, self.wizard_lenght))
        full_text = STRINGS[string_id].format(*msg_args).strip()
        with indent(4):
            puts('\n{}\n'.format(full_text))

    def ask(self, string_id):
        '''Ask a step question.'''
        question = QUESTIONS.get(string_id, None)
        if question is None:
            return
        self.config[string_id] = prompt.query(
            question.text, default=question.default,
            validators=[getattr(self, question.validator)])

    def step(self, string_id, msg_args=(), vlidators=None):
        self.current_step += 1
        self.display(string_id, msg_args)
        self.ask(string_id)

    def run(self):
        '''Run the complete wizard.'''
        self.pre_flight_checks()
        self.step('oauth.directory')
        self.pick_calendar()
        self.step('roster.name')
        name = self.config['roster.name']
        self.pick_time_shift()
        self.step('cache.timeout')
        self.step('cache.past')
        self.step('cache.future')
        self.step('cache.directory', msg_args=[name])
        self.step('fallback.email')
        self.step('fallback.phone')
        self.step('log.directory', msg_args=[name])
        self.pick_log_level()
        self.finish()
        self.step('done', msg_args=[name])
        red('{}\n'.format(FINAL_DISCLAIMER.format(name=name)))
