#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Manage the Shifts, combining information from both calendar and contacts.
'''
import os
from datetime import datetime, timedelta

import pytz
import unicodecsv as csv

from utils import (
    log,
    dtfy,
    plus_one_day,
    merge_intervals,
)
from calendars import Calendar
from contacts import Person


class Shift(object):

    '''A single Shift in the Roster.

    The class has a "smart" initialisation that can accept both textual data
    as well as native Python objects'''

    def __init__(self, start, end, name=None, email=None, phone=None):
        start = dtfy(start)
        end = dtfy(end)
        self.start = start
        self.end = end
        self.name = name.encode('utf-8')
        self.email = email.encode('utf-8') or None
        self.phone = phone or None

    def __repr__(self):
        return u'Shift({} {} {} {} {})'.format(*self.as_tuple)

    @property
    def as_tuple(self):
        return(self.start, self.end, self.name, self.email, self.phone)

    @property
    def as_string_tuple(self):
        return(self.start.isoformat(), self.end.isoformat(), self.name,
               self.email or '<n/a>', self.phone or '<n/a>')


class Roster(object):

    '''Manage building, loading and caching of a Roster.

    A Roster is the collated information from both a given Google calendar and
    the contacts used in it.  The mechanism with callbacks is there to have
    avoid invocking the API prematurely, if the cache will suffice.

    Arguments:
        name             : a human-friendly name for the calendar
        cid              : the `CalendarId` as on Google
        cal_service_clbk : a callback returning a google calendar service
        ppl_client_clbk  : a callback returning a google contacts client
        min_end          : the minimum finishing ISO datetime for polled shifts
                           [Defaults to "now"]
        max_start        : the maximum starting ISO datetime for polled shifts
                           [Defaults to "no limit"]
        all_day_offset   : offset in hours for "all-day-long" events
                           [Defaults to 0]
        cache_timeout    : cache timeout in minutes [Defaults to 30 minutes]
    '''

    def __init__(self, name, cid, cal_service_clbk, ppl_client_clbk,
                 min_end=None, max_start=None, all_day_offset=0,
                 cache_timeout=30, cache_directory=None):
        # Transfer params to class instance
        self.name = name
        self.cid = cid
        self.cal_service_clbk = cal_service_clbk
        self.ppl_client_clbk = ppl_client_clbk
        self.min_end = dtfy(min_end or self.now.isoformat())
        self.max_start = dtfy(max_start)
        self.all_day_offset = all_day_offset
        self.cache_timeout = cache_timeout
        # Initialised other properties
        self.cal_service = None
        self.ppl_client = None
        self.calendar = None
        self._connected = False
        if cache_directory is None:
            cache_directory = os.getcwd()
        self.cache_fname = '{}/{}.cache'.format(cache_directory, name)
        self.cache_fname = os.path.realpath(self.cache_fname)
        self._data = None

    def __iter__(self):
        return self.data

    def _init_data(self):
        '''Initialise the data in the Roster.'''
        if self.stale:
            log.debug('Cache is stale.')
            self.update_cache()
        else:
            try:
                self.load_cache()
            except IOError:
                msg = 'Cannot load cache file "{}", try updating.'
                log.debug(msg.format(self.cache_fname))
                self.update_cache()
            except ValueError:
                log.debug('Trying to update the cache.')
                self.update_cache()

    def _retrieve_live(self, start, end):
        '''Load data by querying Google APIs.'''
        log.info('Retrieving live data for roster: "{}"'.format(self.name))
        if not self._connected:
            cal_service = self.cal_service_clbk()
            self.ppl_client = self.ppl_client_clbk()
            self.calendar = Calendar(self.cid, cal_service, self.min_end,
                                     self.max_start, self.all_day_offset)
        events = self.calendar.get_events(start, end)
        ppl_names = set([event.fuzzy_name for event in events])
        ppl_cache = {}
        for name in ppl_names:
            try:
                ppl_cache[name] = Person(self.ppl_client, name)
            except ValueError:
                pass
        rows = []
        for event in events:
            row = list(event)
            person = ppl_cache.get(event.fuzzy_name, None)
            contacts = (person.email, person.phone) if person else (None, None)
            row.extend(contacts)
            rows.append(Shift(*row))
        msg = 'Retrieved {} shifts for "{}" roster'
        log.debug(msg.format(len(rows), self.name))
        return rows

    def _get_from_google(self, start=None, end=None):
        '''A wrapper that catches any I/O exception and keep going.'''
        try:
            return self._retrieve_live(start, end)
        except Exception as e:
            msg = 'Fatal error while retrieving data from Google: {}'
            log.error(msg.format(e.__class__.__name__))

    def _save_cache(self):
        '''Save a local copy of all the future shifts in the roster.'''
        with open(self.cache_fname, 'wb') as file_:
            log.info('Saving cache for "{}"'.format(self.name))
            writer = csv.writer(file_, delimiter='\t', quoting=csv.QUOTE_NONE)
            writer.writerows([shift.as_tuple for shift in self._data])

    def load_cache(self):
        '''Load data from the local cache.'''
        with open(self.cache_fname, 'rb') as file_:
            log.info('Building roster for "{}" from cache'.format(self.name))
            reader = csv.reader(file_, delimiter='\t', quoting=csv.QUOTE_NONE)
            data = [Shift(*row) for row in reader]
            if not data:
                log.error('Cache is empty')
                raise ValueError('Cache is empty.')
            self._data = data

    def update_cache(self):
        '''Update the Roster with live data.'''
        data = self._get_from_google()
        # If the previous operation fails, use cached data.
        if data:
            self._data = data
            self._save_cache()
        else:
            log.warning('Cache update failed, using stale cache instead.')
            try:
                self.load_cache()
            except (IOError, ValueError):
                msg = 'Cannot connect to Google nor load cache. Panic!'
                log.critical(msg)
                exit(os.EX_IOERR)

    def query(self, start, end):
        '''Return all shifts in a given time bracket.'''
        if start < self.min_end or (self.max_start and end > self.max_start):
            msg = 'Range "{} to {}"" is outside of cache scope "{} to {}".'
            data = (start, end, self.min_end, self.max_start)
            args = [dtfy(x) for x in data]
            log.warning(msg.format(*args))
            shifts = self._get_from_google(start, end)
        else:
            func = lambda s: s.end > start and s.start < end
            shifts = [shift for shift in self.data if func(shift)]
        return shifts

    def report(self, start, end):
        '''Return a report in the form [(date, [persA, persB, ...]), ...]'''
        # `report` works with dates/days not times, so we discard time info...
        start = start.tzinfo.normalize(start)
        end = end.tzinfo.normalize(end)
        offset = timedelta(hours=self.all_day_offset)
        datify = lambda x: datetime(x.year, x.month, x.day,
                                    tzinfo=x.tzinfo) + offset
        start = datify(start)
        # We want the report to be inclusive of both start and end, so end +1
        end = datify(end)
        lines = []
        while start <= end:
            day_end = plus_one_day(start)
            shifts = self.query(start, day_end)
            lines.append((start.date(), [shift.name for shift in shifts]))
            start = day_end
        return lines

    def stats(self):
        '''Return statistics on the roster.'''
        intervals = merge_intervals([(s.start, s.end) for s in self.data])
        stats = {
            'roster.min_end': self.min_end,
            'roster.max_start': self.max_start,
            'cache.size': len(self.data),
            'cache.fragments': len(intervals),
            'cache.first_hole': self.runway,
            # The cache end is the max end of any interval
            'cache.end': sorted(intervals, key=lambda tup: tup[1])[-1][1],
            'cache.timestamp': self.cache_timestamp,
        }
        return stats

    @property
    def runway(self):
        '''Return the the first future hole in the cache or its end.'''
        frozen = self.now
        future_shifts = [s for s in self.data if s.end > frozen]
        intervals = merge_intervals([(s.start, s.end) for s in future_shifts])
        if intervals[0][0] > self.now:
            return self.now
        return intervals[0][1]

    @property
    def now(self):
        '''Return the datetime of now.'''
        return datetime.now(tz=pytz.UTC)

    @property
    def cache_timestamp(self):
        '''Return the datetime of the moment the cache was built.'''
        if not os.path.exists(self.cache_fname):
            return None
        mtime = os.path.getmtime(self.cache_fname)
        return datetime.utcfromtimestamp(mtime).replace(tzinfo=pytz.UTC)

    @property
    def stale(self):
        '''True if the cache is stale.'''
        if self.cache_timestamp is None:
            return True
        max_delta = timedelta(minutes=self.cache_timeout)
        return (self.now - self.cache_timestamp) > max_delta

    @property
    def data(self):
        '''Return the roster data in form of a list of lists.'''
        if self._data is None:
            self._init_data()
        return self._data

    @property
    def table(self):
        '''Return the roster data in form of a formatted string (a table).'''
        if self.data is None:
            return ''
        # The mapping below is to properly handle "None"
        return '\n'.join(
            ('\t'.join(map(unicode, row.as_tuple)) for row in self.data))

    @property
    def current(self):
        '''Return *all* shift objects that are currently on duty.'''
        frozen_instant = self.now
        ret = []
        for shift in self.data:
            if shift.start <= frozen_instant <= shift.end:
                ret.append(shift)
        return ret
        log.error('No active shifts @ {}'.format(frozen_instant))
        return None
