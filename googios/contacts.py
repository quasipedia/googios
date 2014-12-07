#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Interface with Google contacts service.
'''
import os

from gdata.contacts.client import ContactsQuery

from utils import log


class Person(object):

    '''A Person responsible for jour.'''

    def __init__(self, client, fuzzy_name):
        # Because the inconsistent way we store names in our contacts (some
        # person has a "name" field, some other has not), we have to look up
        # a person by fuzzy-matching a "name string" onto some of the data in
        # the person record.
        self.client = client
        self.name = fuzzy_name
        self._execute_query()

    def __repr__(self):
        return '\t'.join((self.name, self.email, self.phone))

    def _get_primary_email(self, contact):
        '''Return the primary email for a contact.'''
        for email in contact.email:
            if email.primary == 'true':
                return email.address

    def _execute_query(self):
        '''Query Google and hope to get one (and only one!) match.'''
        query = ContactsQuery(text_query=self.name)
        feed = self.client.GetContacts(q=query)
        if not feed.entry:
            msg = 'Unable to find anybody matching "{}"'.format(self.name)
            log.error(msg)
            raise ValueError(msg)
        if len(feed.entry) > 1:
            msg = 'Several contacts match the name "{}"'.format(self.name)
            log.error(msg)
            msg = 'Candidate #{}: {}'
            for counter, entry in enumerate(feed.entry, 1):
                email = self._get_primary_email(entry)
                log.info(msg.format(counter, email))
            raise ValueError(msg)
        contact = feed.entry[0]
        self.email = self._get_primary_email(contact)
        # While we can rely on the existence of a primary mail for the contact,
        # we can't do that for phone numbers, so we *must* be strict...
        if len(contact.phone_number) != 1:
            msg_many = 'Too many phone numbers for user "{}"'
            msg_few = 'There is no phone for user "{}"'
            msg = msg_many if self.phone_number > 1 else msg_few
            log.error(msg.format(self.name))
            exit(os.EX_DATAERR)
        self.phone = contact.phone_number[0].text
        self._loaded = True
