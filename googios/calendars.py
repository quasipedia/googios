#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Interface with Google calendar service.

The module should really be called "calendar", not "calendars", but due to how
[poorly] imports are done by Google python API, that would generate an name
conflict.
'''
import datetime
from collections import namedtuple

import pytz

from utils import log


Event = namedtuple('Event', 'start end fuzzy_name')


class Calendar(object):

    '''
    A Google calendar interface.

    Arguments:
        cid: The `CalendarId` to use
    '''

    def __init__(self, cid, service, min_end, max_start, all_day_offset=0):
        self.cid = cid
        self.service = service
        self.min_end = min_end
        self.max_start = max_start
        self.all_day_offset = all_day_offset

    def __iter__(self):
        '''Iterate on all the events in the calendar.'''
        events = self.get_events(min_end=self.min_end)
        for event in events:
            start = event['start']['dateTime']
            end = event['end']['dateTime']
            fuzzy_name = event['summary']
            yield start, end, fuzzy_name

    def get_events(self):
        '''Retrieve a list of events for a given timespan

        Arguments:
            min_end:   the minimum finishing ISO datetime for requested events.
            max_start: the maximum starting ISO datetime for requested events.
        '''
        log.debug('Retrieving events for calendar "{}"...'.format(self.cid))
        events = self.service.events().list(
            calendarId=self.cid,
            singleEvents=True,
            timeMin=self.min_end,
            timeMax=self.max_start,
            orderBy='startTime')
        data = events.execute()
        ret = []
        fix = self.fix_all_day_long_events
        for event in data['items']:
            ret.append(Event(fix(event['start']),
                             fix(event['end']),
                             event['summary']))
        return ret

    def fix_all_day_long_events(self, something):
        '''Shift start date of "all day long" events to match correct start.'''
        # All-day events have start and ending dates missing the time part
        if isinstance(something, dict):
            something = something.get('dateTime', None) or something['date']
        elif not isinstance(something, (str, unicode)):
            raise ValueError('Can\'t process "{}"'.format(something))
        if len(something) == 10:
            point_in_time = datetime.datetime.strptime(something, '%Y-%m-%d')
            delta = datetime.timedelta(hours=self.all_day_offset)
            return (pytz.utc.localize(point_in_time) + delta).isoformat()
        else:
            return something


def get_available_calendars(service):
    '''Return a dictionary with all available calendars.'''
    log.debug('Rtrieving available calendars...')
    data = service.calendarList().list(showHidden=True).execute()
    return {cal['id']: cal['summary'] for cal in data['items']}
