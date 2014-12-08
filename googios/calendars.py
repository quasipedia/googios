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

from utils import log, dtfy


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

    def get_events(self, min_end=None, max_start=None):
        '''Retrieve a list of events for a given timespan

        Arguments:
            min_end:   the minimum finishing ISO datetime for requested events.
            max_start: the maximum starting ISO datetime for requested events.
        '''
        min_end = dtfy(min_end or self.min_end, as_iso_string=True)
        max_start = dtfy(max_start or self.max_start, as_iso_string=True)
        msg = 'Querying calendar for range: {} to {}'
        log.debug(msg.format(min_end, max_start))
        events = self.service.events().list(
            calendarId=self.cid,
            singleEvents=True,
            timeMin=min_end,
            timeMax=max_start,
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
        # All-day events have start and ending dates filed under the key 'date'
        # rather than 'dateTime'.
        if something['dateTime'] is not None:
            return dtfy(something['dateTime'])
        else:
            date = dtfy(something['date'])
            return date + datetime.timedelta(hours=self.all_day_offset)


def get_available_calendars(service):
    '''Return a dictionary with all available calendars.'''
    log.debug('Rtrieving available calendars...')
    data = service.calendarList().list(showHidden=True).execute()
    return {cal['id']: cal['summary'] for cal in data['items']}
