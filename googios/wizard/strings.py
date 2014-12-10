STRINGS = {

    'oauth.directory':
'''
Welcome to GooGios!

This wizard will help you create a configuration file for your GooGios project.
In order to access your data on Google, GooGios need to read the OAuth
credentials.  Where are the two OAuth files mentioned in the GooGios
documentation?
''',

    'roster.cid':
'''
The following is a list of the rosters (Google calendars) visible with the
OAuth credential given.  What roster would you like to configure?

{}
''',

    'roster.name':
'''
Choose a short name for the roster.  Only ASCII letters, digits and ".", "-",
"_" are allowed.
''',

    'roster.time_shift':
'''

Sometimes people register shifts as 'all-day-long' events.  Google interprets
these shifts as beginning at 00:00 and lasting 24 hours.  You can adjust the
starting time of these shifts by offsetting their beginning and end by a fixed
number of hours.

For example: would your shifts begin at 2 p.m., you should enter `14`.
''',

    'cache.timeout':
'''
For how many minutes should your cache be considered fresh?  [GooGios will
auto-update its cache with fresh data from Google if the cache will become
stale]
''',

    'cache.past':
'''
How many *past* days of the roster would you like to keep in the cache? [Only
useful if you produce reports or query GooGios for past events]
''',

    'cache.future':
'''
How many *future* days of the roster would you like to keep in the cache?
[The `None` default means all future events (or at least as many as the Google
API will return in a single query) will be cached]
''',

    'cache.directory':
'''
In what directory should your CVS `{}.cache` file be saved?
''',

    'fallback.email':
'''
What is the fall-back *email() that should be contacted as a last resource
should everything else fail?
''',

    'fallback.phone':
'''
What is the fall-back *phone number* that should be contacted as a last
resource should everything else fail?
''',

    'log.directory':
'''
In what directory should your `{}.log` log file be saved?
''',

    'log.level':
'''
What is the minimum level of messages that you would like to log?
Possible choices are DEBUG, INFO, WARNING, ERROR, CRITICAL
''',

    'done':
'''
Congratulations!  GooGios is now ready to roll.  You can now check everything
is working by issuing:

    googios {} status
'''
}

FINAL_DISCLAIMER = '''
*******************************************************************************
    Remember to add the cache-downloading job to your crontab!

        `googios {} update`

    You may also wish to create nagios tasks for monitoring:
    - The return value of `googios {} runway`
    - The exit code of `googios {} status`
*******************************************************************************
'''
