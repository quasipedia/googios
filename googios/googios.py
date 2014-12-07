#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Manage your Nagios on-call roster with Google apps.

Usage:
    googios  setup

Options:
    -h --help        Show this screen.
    --version        Show version.
'''

from docopt import docopt

import wizard


def main():
    cli = docopt(__doc__, version='0.1')
    if cli['setup']:
        from pprint import pprint
        pprint(wizard.wizard())


if __name__ == '__main__':
    main()
