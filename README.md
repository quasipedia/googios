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
is now unmaintained and uses a Google API that has been deprecated years ago
and now shut down for good.


How
---

A few examples, imagining having a roster called "dev":

    # Update the local cache
    googios dev update

    # Print out the name and phone number of the person currently on duty
    googios dev current name phone

    # Print out all information about who was/will be on call today, at 12:30
    googios dev query --at='12:30'

    # Print out all information on all roster shifts between "start" and "end"
    googios dev query --start='1 nov' --end='5 nov'

    # Print out a fancy, human-friendly report of who was on-call last august
    googios dev report august

    # Print out the number of days between now and the last inserted shift
    googios dev runway

    # Print out statistics and perform sanity checks on the local cache
    googios dev status



Installation
------------

    pip install googios

One of GooGios dependencies is `pycrypto`.  This may require compilation of C
code, so you may have to install a few binaries in order for this to work (for
example you may have to install `python-devel`, `gcc`, `libff-devel`, `openssl-
devel` and others).


Setup
-----

In order to take full advantage of what GooGios has to offer, there are four
steps required:

- Generation of the OAuth "stuff" on Google.
- Setting up the different rosters in GooGios.
- Adding relevant GooGios jobs to crontab.
- Adding relevant nagios checks in... well, Nagios!


### Google setup

Google is in the process of porting their API from an old `gdata` framework to
a newer and better designed `service` one.  Unluckily at the time of coding
GooGios (December 2014) `calendars` has been ported (and the old version
terminated) while `contacts` has not.

Bottom-line: you will have to generate two different sets of OAuth credentials
from your Google "Developer Console" on Google:

- a 2-legged-Oauth signed key (i.e. "service account") for `calendars`
- a 3-legged-Oauth set of credentials (i.e. "native application") for `contacts`

Export them as `2-legged.oauth` and `3-legged.oauth` respectively.

While I won't delve into this here (Google is your friend!), keep in mind that
you will have to activate both APIs from your control panel and perform a
domain-wise delegation for the 2-legged "user".

The scopes you will have to use in that process will be:

    https://www.googleapis.com/auth/calendar.readonly
    https://www.googleapis.com/auth/contacts.readonly


### GooGios setup

Move to the directory where you want to generate your configuration file and
type:

    googios setup

Follow the on-screen instructions.  Easy! :)


### Crontab setup

Googios will autonomously attempt to refresh the cache when it becomes stale,
but this only happens when the script is invoked (for example by Nagios wishing
to contact somebody because of a problem).  However one of the problems
detected may well be lack of connectivity, so you should have a cronjob
explicitly updating the cache from time to time.

    googios <your-roster-config-file> update


### Nagios setup

#### Notifications

For each Nagios contact definition, you can provide a notification_command
that is executed to notify that particular contact.

You can use the default Nagios notification command, but instead of piping to
/bin/mail you pipe to /usr/bin/mail-to-oncall.

The mail-to-oncall script runs GooGios to get the current on-call person's
contact details.

#### Monitoring GooGios

There are three Nagios checks that is advisable to implement:

- A **`googios <your-roster> runway`** test to raise an alarm when the first
  day of the roster without anybody assigned to it is approaching.
- A **`googios <your-roster> status`** that to raise an alarm in case the
  content of the roster is problematic (overlapping shifts, missing data...)
- A test on GooGios logs as explained below.

As anything is software development, GooGios may well encounter an unforeseen
condition that will break it.  This is why you should set up a Nagios task that
monitors GoogGios' logs and raises an alarm in case of messages with a log
level of WARNING, ERROR or CRITICAL.

There are many off-the-shelf Nagios plugins for checking log files for
precisely this conditions.


Limitations
-----------

This project is a new (hopefully good) implementation of an idea that wasn't
really thought through well, namely managing an on-call roster by mean of free-
type the name of the on-call staff member as "event name" in a Google calendar.

There are a number of problems with this architecture.

For one, Google calendar and Google contacts have been designed with humans in
mind, and they do not offer any validation on the title of an event.  This
means that is possible to insert (and in fact happens all the times) a
misspelled name or an ambiguous one or even that of somebody whom contact
details are not available by the user owning the roster calendar.

Secondly, having your master emergency data on a remote server obliges you to
keep a local cache, given that one of the problems your server may encounter is
lack of connectivity.

GooGios tries to be graceful around these problems, providing fall-back
options, but a workaround is still only a workaround, and can't fix a design
problem.


Acknowledgments
---------------

The basic functionality of GooGios is somehow a reimplementation of Martin
Melin's [NagCal](https://github.com/martinmelin/NaGCal).
