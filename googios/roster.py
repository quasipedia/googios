#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Manage the Shifts, combining information from both calendar and contacts.
'''
import os
from datetime import datetime, timedelta

import pytz
import dateutil.parser
import unicodecsv as csv
from utils import log, dtfy
from calendars import Calendar
from contacts import Person


class Shift(object):

    '''A single Shift in the Roster.

    The class has a "smart" initialisation that can accept both textual data
    as well as native Python objects'''

    def __init__(self, start, end, name, email, phone):
        start = dtfy(start)
        end = dtfy(end)
        self.start = start
        self.end = end
        self.name = name
        self.email = email or None
        self.phone = phone or None

    def __repr__(self):
        return 'Shift({} {} {} {} {})'.format(*self.as_tuple)

    @property
    def as_tuple(self):
        return(self.start, self.end, self.name, self.email, self.phone)

    @property
    def as_string_tuple(self):
        return(self.start.isoformat(), self.end.isoformat(), self.name,
               self.email, self.phone)


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
                log.debug('File {} does not exists'.format(self.cache_fname))
                self.update_cache()
            except ValueError:
                log.debug('First event in cache begins after min_end')
                self.update_cache()

    def _get_from_google(self, start=None, end=None):
        '''Load data by querying Google APIs.'''
        log.info('Building roster for "{}" from live data'.format(self.name))
        try:
            if not self._connected:
                cal_service = self.cal_service_clbk()
                self.ppl_client = self.ppl_client_clbk()
                self.calendar = Calendar(self.cid, cal_service, self.min_end,
                                         self.max_start, self.all_day_offset)
        except Exception as e:
            log.error('Fatal error while retrieving data from Google')
            log.exception(e.message)
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
                raise ValueError('Cache is empty.')
            if data[0].start > self.min_end:
                raise ValueError('Cache may lack early records.')
            self._data = data

    def update_cache(self):
        '''Update the Roster with live data.'''
        try:
            data = self._get_from_google()
        except Exception as e:
            log.error('Fatal error while retrieving data from Google')
            log.exception(e.message)
        else:
            self._data = data
            self._save_cache()

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

    # Hic sunt leones

    def daterange(self, start_date, end_date):
        '''Generate a rangeg of dates'''
        for n in range(int((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)


    def report(self, date_from, date_to):
        '''Download calendar and show shifts during specific time period.

        Returns:
            List with date and shift name.'''
        start_split = date_from.split("-")
        end_split = date_to.split("-")
        start_date = datetime.datetime(int(start_split[0]), int(start_split[1]), int(start_split[2]), (int(self.ade_offset_hours) + 3), 0, 0, 0, UTC())
        end_date = datetime.datetime(int(end_split[0]), int(end_split[1]), int(end_split[2]), (int(self.ade_offset_hours) + 3), 0, 0, 0, UTC())
        result = {}

        try:
            client = self.get_calendar_client()
            query = gdata.calendar.client.CalendarEventQuery()
            query.start_min = date_from
            query.start_max = date_to
            query.max_results = 200
            event_feed = client.GetCalendarEventFeed(uri=self.calendar_url, q=query)

            shifts = []
            for event in event_feed.entry:
                shifts.append(Shift(
                    event.title.text.encode("utf-8"),
                    parse_date(self.parse_shift_date(event.when[0].start)),
                    parse_date(self.parse_shift_date(event.when[0].end))
                ))

            ordered_shifts = sorted(shifts, key=attrgetter('start'))
            current_shift = None

            for current_date in self.daterange(start_date, end_date):
                current_shift = None
                for shift in ordered_shifts:
                    if current_date >= shift.start and current_date <= shift.end:
                        current_shift = shift
                        break
                name = None
                if current_shift:
                    name = current_shift.title
                result["%s" % current_date] = name

            return result

        except Exception, e:
            log.exception(e)
            return {}

    def get_last_shift(self):
        '''Return the Shift object that is last in current calendar. Will sync if we haven't already.'''
        if not self.have_synced:
            self.sync()
        last_shift = None
        last_shift = self.shifts.pop()
        if last_shift is None:
            log.error("Was asked for last shift, but there are no shifts!")
        return last_shift

    def get_current_person(self):
        '''Return the Person object associated with the Shift that is considered current. Will sync if haven't already.'''
        if not self.have_synced:
            self.sync()
        current_shift = self.get_current_shift()
        if current_shift is None:
            log.error("Asked for on call person, but no current shift! Trying 24 hours ago.")
            current_shift = self.get_current_shift("1 day")
            if current_shift is None:
                log.error("Asked for on call person, but no current shift!")
                return None
        return self.get_person(current_shift.title)
