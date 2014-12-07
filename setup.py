from setuptools import setup, find_packages

long_description = '''
GooGios
=======

GooGios allows to use Google apps (calendar, contacts) to manage a roster of
on-call people.  The script keeps in sync a local cache of the on-call shifts
and it can be queried to output information like who is the current person on
duty, what's their telephone number and email address, as well as getting the
complete roster between date X and Y.

Documentation can be found on the public `repository on GitHub`_:

.. _repository on GitHub: https://github.com/quasipedia/googios
'''

setup(
    # Project details
    name='googios',
    version='0.1',
    description='Manage your Nagios on-call roster with Google apps',
    long_description=long_description,
    url='https://github.com/quasipedia/googios',

    # Author details
    author='Mac Ryan',
    author_email='quasipedia@gmail.com',
    license='GPLv3+',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',  # 5 - Production/Stable
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later',
        'Intended Audience :: Developers',
        'Topic :: System :: Monitoring',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.2',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
    ],

    keywords='nagios google google-apps system-monitoring uptime alarms',

    packages=find_packages(),

    install_requires=[
        'docopt==0.6.2',
        'google-api-python-client==1.3.1',
        'gdata==2.0.18',
        'pycrypto==2.6.1',
        'unicodecsv==0.9.4',
        'pytz==2014.10',
        'python-dateutil==2.3',
    ],

    # extras_require = {
    #     'dev': ['profile'],
    #     'test': ['coverage', 'nose'],
    # },

    # package_data={
    #     'googios': ['setup-questions.json'],
    # },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages.
    # see http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    entry_points={
        'console_scripts': [
            'googios=googios:main',
        ],
    },
)
