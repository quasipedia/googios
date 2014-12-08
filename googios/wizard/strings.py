STRINGS = {

    'welcome':
'''
Welcome to GooGios.  This script will guide you through the configuration
process.  It assumes that both the `2-legged.oauth` and `3-legged.oauth` files
are in the working directory you launched the script from.
''',

    'roster.cid':
'''
GooGios operates on a single roster at a time (what roster to operate on
is communicated as a command line parameter).  The following is a list of the
rosters (Google calendars) visible with the OAuth credential given.  Enter the
number corresponding to the calendar you would like to generate the
configuration script for.

{}
''',

    'roster.name':
'''
Choose a short name for the roster.  This name will be used for file naming
too, so only ASCII letters and numbers (plus `.-_`) are allowed
''',

    'roster.time_shift':
'''
Sometimes people register shifts as 'all-day-long' events, or events
spanning multiple days at a time.  By default these events span from midnight
to midnight; if you would like to adjust them to match your organization's
rules enter the number of hours the event should be shifted forward.  For
example: if your shifts are from 9am to 9am, enter `9`.
''',

    'cache.timeout':
'''
Insert the cache timeout in minutes.  GooGios will auto-update its cache
with fresh data from Google if the cache will become stale (older than this
timeout).  The cache should however be explicitly update with a cron job
`googios update`.
''',

    'cache.back':
'''
By default the cache contains all shifts from the one active at the time of
cache creation to the last available on Google.  You can override this by
selecting the numbers of days in both past and future that you would like to
be cached.  Let's start from the past...
''',

    'cache.forward':
'''...and now the future.''',

    'cache.directory':
'''
Data from the roster is cached as CVS files.  By default the cache lives in
the same directory than the oauth and configuration files.  If you wish to
override this behaviour enter an alternative directory here.  Cache files are
named `<roster-name>.cache`, so be mindful not to call two rosters with the
same name, if you are using the same directory for their cache.
''',

    'fallback.email':
'''
Sometimes it may be impossible to retrieve the contact details of a person,
or there might be a period of time for which nobody has been assigned.  Enter
a fallback email address to be used in such cases (suggestion: use a mail alias
that contacts more than one person for this).
''',

    'fallback.phone':
'''
Enter a fallback phone number.
''',

    'log.directory':
'''
And finally for GooGios logs...  As for the cache, the default behaviour is
using the same directory where the OAuth and configuration files are stored.
If you'd like to use a different one enter that below.  The log file will
be called `<roster-name>.log`
''',

    'log.level':
'''
Select what minimum log level you would like to generate messages for.
Possible choices are DEBUG, INFO, WARNING, ERROR, CRITICAL
''',

    'done':
'''
Congratulations!  GooGios is now ready.  You can now test that the
configuration works by issuing:

    googios {} status

*******************************************************************************
Remember to add the cache-downloading job to your crontab!

    `googios {} update`

You may also wish to create nagios tests for:
- The runaway of the log (number of assigned days left in the roster)
- The status of the cache
*******************************************************************************
''',

}
