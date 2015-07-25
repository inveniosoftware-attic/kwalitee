# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014, 2015 CERN.
#
# kwalitee is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# kwalitee is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kwalitee; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Kwalitee is a tool that runs static analysis checks on Git repository."""

import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


install_requires = [
    'alembic',
    'colorama',
    'Flask',
    'Flask-Script',
    'Flask-SQLAlchemy',
    'pep8',
    'pep8-naming',
    'pep257>=0.5.0',
    'pyflakes',
    'flake8-import-order',
    'flake8-blind-except',
    'pytest',
    'requests',
    'rq>=0.4.6',
    'PyYAML',
]

if tuple(sys.version_info) < (3, 0):
    # If pygit2 is not installed, grab GitPython instead.
    try:
        import pygit2
    except ImportError:
        install_requires.append('GitPython>=0.3.2.RC1')

test_requires = [
    'pytest-cov',
    'httpretty',
    'mock',
    'pyhamcrest'
]


# Get the version string.  Cannot be done with import!
version = {}
with open(os.path.join('kwalitee', 'version.py'), 'r') as fp:
    exec(fp.read(), version)


class PyTest(TestCommand):

    """PyTest test runner.

    See: http://pytest.org/latest/goodpractises.html?highlight=setuptools
    """

    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        """Initialize test options."""
        TestCommand.initialize_options(self)
        self.pytest_args = ["tests"]

    def finalize_options(self):
        """Finalize options."""
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        """Run listed tests."""
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='kwalitee',
    version=version['__version__'],
    url='https://github.com/inveniosoftware/kwalitee',
    license='GPLv2',
    author='Invenio collaboration',
    author_email='info@invenio-software.org',
    description=__doc__,
    long_description=open('README.rst').read(),
    packages=['kwalitee'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=install_requires,
    tests_require=test_requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points={
        'console_scripts': [
            'kwalitee = kwalitee.cli:main',
        ],
    },
    cmdclass={
        'test': PyTest
    },
)
