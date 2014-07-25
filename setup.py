# -*- coding: utf-8 -*-
##
## This file is part of Invenio-Kwalitee
## Copyright (C) 2014 CERN.
##
## Invenio-Kwalitee is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio-Kwalitee is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio-Kwalitee; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
##
## In applying this licence, CERN does not waive the privileges and immunities
## granted to it by virtue of its status as an Intergovernmental Organization
## or submit itself to any jurisdiction.

"""Invenio-Kwalitee setuptools configuration."""

import os
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


install_requires = [
    'alembic',
    'Flask',
    'Flask-Script',
    'Flask-SQLAlchemy',
    'pep8',
    'pep257',
    'pyflakes',
    'pytest',
    'requests',
    'rq>=0.4.6'
]
if tuple(sys.version_info) < (2, 7):
    install_requires.append('argparse')
    install_requires.append('importlib')
if tuple(sys.version_info) < (3, 0):
    install_requires.append('GitPython>=0.3.2.RC1')

test_requires = [
    'pytest-cov',
    'httpretty',
    'mock',
    'pyhamcrest'
]


# Get the version string.  Cannot be done with import!
version = {}
with open(os.path.join('invenio_kwalitee', 'version.py'), 'r') as fp:
    exec(fp.read(), version)


class PyTest(TestCommand):

    """
    PyTest test runner.

    See: http://pytest.org/latest/goodpractises.html?highlight=setuptools
    """

    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ["tests"]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='Invenio-Kwalitee',
    version=version['__version__'],
    url='https://github.com/inveniosoftware/invenio-kwalitee',
    license='GPLv2',
    author='Invenio collaboration',
    author_email='info@invenio-software.org',
    description='Invenio-Kwalitee is tool for checking quality of '
                'Invenio commits.',
    long_description=open('README.rst').read(),
    packages=['invenio_kwalitee'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=install_requires,
    tests_require=test_requires,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points={
        'console_scripts': [
            'kwalitee = invenio_kwalitee.cli:main',
        ],
    },
    cmdclass={
        'test': PyTest
    },
)
