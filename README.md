GooGios
=======

Manage your Nagios on-call roster with Google apps


What
----

GooGios allows to use Google apps (calendar, contacts) to manage a roster of
on-call people.  The script keeps in sync a local cache of the on-call shifts
and it can be queried to output information like who is the current person on
duty, what's their telephone number and email address, as well as getting the
complete roster between date X and Y.


Why
---

Because my employer used [NaGCal](https://github.com/martinmelin/NaGCal) which
is now unmaintained and uses a Google API that has been deprecated (i.e.: it is
not anymore working).


Limitations
-----------

This project is new (hopefully good) code implementing an old, flawed idea.

Google calendar and google contacts have been designed with humans in mind, not
machines, and they do not enforce restrictions on the data you can insert, so
it is very possible (in fact happens all the time) that the name of a person
get misspelled, or that their contact information is wrong, or that the person
assigned to a shift is not in one of the accessible contact lists, etc...

GooGios tries to be graceful around these problems, providing fall-back
options, but a workaround is still only a workaround, and can't fix a design
problem.


Installation
------------

```python
pip install googios
```

One of GooGios dependencies is `pycrypto`.  This may require compilation of C
code, so you may have to install a few binaries in order for this to work
(for example you may have to install `gcc`, `libff-devel`, `openssl-devel` and
others).


Google setup
------------

Google is in the process of porting their API from an old `gdata` framework to
a newer and better designed `service` one.  Unluckily at the time of coding
this (December 2014) `calendars` has been ported (and the old version
terminated) while `contacts` has not.

Bottom-line: you will have to generate two different sets of OAuth credentials
from you Google "Developer Console" on Google:

- a 2-legged-Oauth signed key (i.e. "service account") for `calendars`
- a 3-legged-Oauth set of credentials (i.e. "native application") for `contacts`

Export them as `2-legged.oauth` and `3-legged.oauth` respectively.

While I won't delve into this here (Google is your friend!), keep in mind that
you will have to activate both APIs from your control panel and perform a
domain-wise delegation for the 2-legged "user".

The scopes you will have to use are:

    https://www.googleapis.com/auth/calendar.readonly
    https://www.googleapis.com/auth/contacts.readonly


GooGios setup
-------------

Move to the directory where your OAuth data is stored and type:

    googios setup

Follow the on-screen instructions.


Cronjob setup
-------------

Googios will autonomously attempt to refresh the cache when it becomes stale,
but this only happens when the script is invoked (for example by Nagios wishing
to contact somebody because of a problem).  However one of the problems
detected may well be lack of connectivity, so you should have a cronjob
explicitly updating the cache from time to time.

    googios update <your-roster-name>


Nagios setup
------------

### Notifications

For each Nagios contact definition, you can provide a notification_command
that is executed to notify that particular contact.

You can use the default Nagios notification command, but instead of piping to
/bin/mail you pipe to /usr/bin/mail-to-oncall.

The mail-to-oncall script runs GooGios to get the current on-call person's
contact details.

### Monitoring GooGios

As anything is software development, GooGios may well encounter an unforeseen
condition that will break it.  This is why you should set up a Nagios task that
monitors GoogGios' logs and raises an alarm in case of messages with a log
level of WANING, ERROR or CRITICAL.

There are many off-the-shelf Nagios plugins for checking log files for
precisely this conditions.


Acknowledgments
---------------

The idea and the overall design of GooGios comes from Martin Melin's NagCal.
