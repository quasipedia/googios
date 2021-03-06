#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import logging
import datetime
from collections import namedtuple
from itertools import takewhile

import pytz
import dateutil.parser
import httplib2
import dateutil.relativedelta
from gdata.gauth import OAuth2Token
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from gdata.contacts.client import ContactsClient
from oauth2client.client import (
    OAuth2WebServerFlow,
    SignedJwtAssertionCredentials)
from apiclient.discovery import build

MockArgparseFlags = namedtuple(
    'MockArgparseFlags',
    'logging_level noauth_local_webserver'
)

ON_SCREEN_LOGGING_LEVEL = logging.DEBUG  # Used only when `googios ... --echo`
AGENT_NAME = 'GooGios'
SCOPES = {
    'calendar': 'https://www.googleapis.com/auth/calendar.readonly',
    'contacts': 'https://www.googleapis.com/auth/contacts.readonly',
}

# The logger default configuration is to log to console.  This is generally
# Overridden by logging to a file, when googios is ran as a script...
log_format = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
log_stream_handler = logging.StreamHandler()
log_stream_handler.setFormatter(log_format)
log = logging.getLogger('googios')
log.addHandler(log_stream_handler)
log.setLevel(ON_SCREEN_LOGGING_LEVEL)

# Store cached values of the service/client once initialised
__cal_service = None
__ppl_client = None


class TwoLeggedOauth(object):

    '''This is just a namespace container for 2-legged Oauths.

    2-legged Oauth is the Oauth flow that does not require human interaction,
    and relies on a cryptographically signed key for obtaining the tokens.
    It is the *correct way* of authorising a server-to-server application.
    '''

    @staticmethod
    def get_http_auth(conf_fname):
        '''Return an authenticated HTTP connector.'''
        log.debug('Getting a 2-legged authenticated HTTP client...')
        configuration = json.load(open(conf_fname))
        kwargs = {
            'service_account_name': configuration['client_email'],
            'private_key': configuration['private_key'],
            'scope': list(SCOPES.values()),
            'user_agent': AGENT_NAME,
        }
        credentials = SignedJwtAssertionCredentials(**kwargs)
        return credentials.authorize(httplib2.Http())

    @staticmethod
    def get_service(name, version, http_auth):
        '''Return a fully functional and authorised Google service.'''
        log.debug('Building a "{}" service'.format(name))
        return build(name, version, http=http_auth)


class ThreeLeggedOauth(object):

    '''This is just a namespace container for 3-legged Oauths.

    3-legged Oauth is the Oauth flow that require a human to authorize the
    generation of a token with a variable set of permissions.
    It is the *wrong way* of authorising a server-to-server application, but
    it is apparently the only way Google Apps accepts for the contacts API.
    Hopefully the contacts API will be ported to a service in the near future.
    '''

    @staticmethod
    def get_credentials(conf_fname):
        '''Run interactive OAuth 2.0 setup dance and return True on success.'''
        log.debug('Getting 3-legged credentials...')
        configuration = json.load(open(conf_fname))['installed']
        creds_fname = '{}.credentials'.format(os.path.splitext(conf_fname)[0])
        storage = Storage(creds_fname)
        credentials = storage.get()
        if credentials is None:
            log.info('Generating new 3-legged token')
            kwargs = {
                'client_id': configuration['client_id'],
                'client_secret': configuration['client_secret'],
                'scope': [SCOPES['contacts']],
                'user_agent': AGENT_NAME,
                'xoauth_displayname': AGENT_NAME,
            }
            flow = OAuth2WebServerFlow(**kwargs)
            log_level_string = logging.getLevelName(log.level)
            flags = MockArgparseFlags(log_level_string, True)
            credentials = run_flow(flow, storage, flags)
            storage.put(credentials)
        elif credentials.access_token_expired:
            credentials.refresh(httplib2.Http())
            storage.put(credentials)
        return credentials

    @staticmethod
    def get_contacts_client(credentials):
        '''Return a gdata.contacts.client.ContactsClient instance.'''
        log.debug('Instantiating the contact client...')
        token_object = OAuth2Token(
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scope=[SCOPES['contacts']],
            user_agent=credentials.user_agent,
            access_token=credentials.access_token,
            refresh_token=credentials.refresh_token)
        client = ContactsClient(
            source=AGENT_NAME,
            auth_token=token_object)
        return client


def get_people_client(oauth_dir=''):
    '''Ruturn a client for the contacts API.'''
    global __ppl_client
    oauth_fname = os.path.join(oauth_dir, '3-legged.oauth')
    if __ppl_client is None:
        log.debug('Generating "contacts" client...')
        credentials = ThreeLeggedOauth.get_credentials(oauth_fname)
        if credentials.invalid:
            log.critical('Invalid 3-legged credentials')
            exit(os.EX_CONFIG)
        __ppl_client = ThreeLeggedOauth.get_contacts_client(credentials)
    return __ppl_client


def get_calendar_service(oauth_dir=''):
    '''Ruturn a service for the calendar API.'''
    global __cal_service
    oauth_fname = os.path.join(oauth_dir, '2-legged.oauth')
    if __cal_service is None:
        log.debug('Generating the "calendar" service...')
        http_auth = TwoLeggedOauth.get_http_auth(oauth_fname)
        __cal_service = TwoLeggedOauth.get_service('calendar', 'v3', http_auth)
    return __cal_service


def dtfy(something, tz=None, as_iso_string=False):  # tdfy = datetime-fy
    '''If possible, transform "something" in a datetime, tzone-aware object.'''
    if something is None:
        return None
    if not isinstance(something, datetime.datetime):
        try:
            something = dateutil.parser.parse(something)
        except Exception as e:
            log.error('Cannot convert "{}" to datetime'.format(something))
            log.exception(e.message)
            raise
    if something.tzinfo is None:
        if tz is None:
            something = pytz.utc.localize(something)
        else:
            something = pytz.timezone(tz).localize(something)
    if as_iso_string:
        return something.isoformat()
    return something


def plus_one_day(aware_dtime):
    '''Compute the datetime of the following day accounting for DTS.'''
    tz = aware_dtime.tzinfo
    tomorrow = aware_dtime.replace(tzinfo=None) + datetime.timedelta(days=1)
    plus_day = tz.localize(tomorrow, is_dst=aware_dtime.dst())
    return tz.normalize(plus_day)  # to detect non-existent times


def merge_intervals(intervals):
    '''Given a series intervals merge together the overlapping ones.'''
    sorted_intervals = sorted(intervals)
    new_intervals = []
    while sorted_intervals:
        old = sorted_intervals.pop()
        for counter, new in enumerate(new_intervals):
            if old[0] <= new[0] <= old[1] or old[0] <= new[1] <= old[1]:
                merged = (min(old[0], new[0]), max(old[1], new[1]))
                new_intervals[counter] = merged
                break
        else:
            new_intervals.append(old)
    new_intervals.sort()
    if intervals == new_intervals:
        return new_intervals
    else:
        return merge_intervals(new_intervals)


def find_overlaps(intervals):
    '''Given a series of intervals, find what are the overlapping zones.'''
    sorted_intervals = sorted(intervals)
    overlaps = []
    analysed = sorted_intervals.pop(0)
    while True:
        overlapping = takewhile(lambda i: i[0] < analysed[1], sorted_intervals)
        for interval in overlapping:
            overlaps.append((interval[0], min(interval[1], analysed[1])))
        if not sorted_intervals:
            break
        analysed = sorted_intervals.pop(0)
    return merge_intervals(overlaps)
