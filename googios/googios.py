#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Manage your Nagios on-call roster with Google apps.

Usage:
    googios  setup

Options:
    -h --help        Show this screen.
    --version        Show version.
    --dir=<DIR>      Take credentials and configuration from DIR instead of
                     current directory.
'''
from docopt import docopt

from wizard.wizard import run_wizard


def main():
    cli = docopt(__doc__, version='0.1')
    if cli['setup']:
        run_wizard()


if __name__ == '__main__':
    main()
