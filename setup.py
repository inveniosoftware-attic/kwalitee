# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014, 2015, 2016 CERN.
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

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
    'httpretty>=0.8.14',
    'mock>=2.0.0',
    'pyhamcrest>=1.9.0'
]

extras_require = {
    'docs': [
        'Sphinx>=1.4.2',
        'sphinxcontrib-issuetracker>=0.11',
    ],
    'gitpython': [
        'GitPython>=0.3.2.RC1',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for key, reqs in extras_require.items():
    if key == 'gitpython':
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'pytest-runner>=2.6.2',
]

install_requires = [
    'colorama>=0.3.7',
    'click>=5.0',
    'pep8>=1.7.0',
    'pep8-naming>=0.3.3',
    'pydocstyle>=1.0.0',
    'pyflakes>=1.0.0,<1.1.0',
    'flake8>=2.5.4',
    'flake8-isort>=1.2,<2.0',
    'flake8-blind-except>=0.1.0',
    'PyYAML>=3.11',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('kwalitee', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='kwalitee',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    license='GPLv2',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/kwalitee',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': [
            'kwalitee = kwalitee.cli:main',
            'kwalitee-pre-commit = kwalitee.hooks:pre_commit_hook',
            'kwalitee-prepare-commit-msg = kwalitee.hooks'
            ':prepare_commit_msg_hook',
            'kwalitee-post-commit = kwalitee.hooks:post_commit_hook',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
