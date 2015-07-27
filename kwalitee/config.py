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

"""
kwalitee base configuration.

To change it, put a config.py into your instance.

.. py:data:: CONTEXT

    Context for Github.

    .. seealso::

        `Github API Statuses
        <https://developer.github.com/v3/repos/statuses/>`_


.. py:data:: COMPONENTS

    List of supported components.

    .. seealso:: :func:`.kwalitee.check_message`

.. py:data:: ACCESS_TOKEN

    Github access token. Used to post statuses and comments. It MUST be set.

.. py:data:: AUTO_CREATE

    Allow anyone to add its repository by setting up the webhook on Github.

    **Default:** ``False``

.. py:data:: CHECK_COMMIT_MESSAGES

    Enable the :func:`commit message checks <.kwalitee.check_message>`.

    **Default:** ``True``

.. py:data:: CHECK_WIP

    Enable the *work-in-progress* pull requests checks. Disabled by default.

    **Default:** ``False``

.. py:data:: CHECK_LICENSE

    Enable the :func:`license checks <.kwalitee.check_license>`.

    **Default:** ``True``

.. py:data:: CHECK_PEP8

    Enable the :func:`PEP8 checks <.kwalitee.check_pep8>`.

    **Default:** ``True``

.. py:data:: CHECK_PEP257

    Enable the :func:`PEP257 checks <.kwalitee.check_pep257>`.

    **Default:** ``True``

.. py:data:: CHECK_PYFLAKES

    Enable the PyFlakes checks. PEP8 checks are required.

    **Default:** ``True``

.. py:data:: IGNORE

    Error codes to ignore.

    **Default:** ``['E123', 'E226', 'E24', 'E501', 'E265']``

.. py:data:: SELECT

    Error codes to specially enable.

    **Default:** ``[]``

.. py:data:: WORKER_TIMEOUT

    Background worker job time window.

    Any job taking longer than that will be killed.

    RQ default timeout is 180 seconds

.. py:data:: MIN_REVIEWERS

    Minimum number of reviewers for py:func:`message check
    <.kwalitee.check_message>`.

    **Default:** 3

.. py:data:: LABEL_WIP

    Label to apply for a *work-in-progress* pull request.

    **Default:** ``"in_work"``

.. py:data:: LABEL_REVIEW

    Label to apply for a pull request that needs more reviewers.

    **Default:** ``"in_review"``

.. py:data:: LABEL_READY

    Label to apply for a pull request that passes all the checks.

    **Default:** ``"in_integration"``

.. py:data:: EXCLUDES

    List of regex of excluded files.

    **Default:** ``[]``

"""

COMPONENTS = [
    'base',
    'celery',
    'global',
    'grunt',
    'installation',
    'utils',
    # modules
    'access',
    'accounts',
    'alerts',
    'apikeys',
    'authorlist',
    'authors',
    'baskets',
    'bulletin',
    'circulation',
    'classifier',
    'cloudconnector',
    'comments',
    'communities',
    'converter',
    'dashboard',
    'deposit',
    'documentation',
    'documents',
    'editor',
    'encoder',
    'export',
    'exporter',
    'formatter',
    'groups',
    'indexer',
    'jsonalchemy',
    'knowledge',
    'linkbacks',
    'matcher',
    'merger',
    'messages',
    'oaiharvester',
    'oairepository',
    'pidstore',
    'previewer',
    'previews',
    'ranker',
    'record_editor',
    'records',
    'redirector',
    'refextract',
    'scheduler',
    'search',
    'sequencegenerator',
    'sorter',
    'statistics',
    'submit',
    'sword',
    'tags',
    'textminer',
    'tickets',
    'upgrader',
    'uploader',
    'workflows',
]

CONTEXT = "kwalitee"


GITHUB = "https://github.com/"
"""Github base URL."""
GITHUB_REPO = GITHUB + "{account}/{repository}/"
"""Github repository URL template."""

# Background worker
# -----------------
# WORKER_TIMEOUT = 180

# Checks run on the files
# -----------------------
#
# Default values, uncomment to change:
# CHECK_COMMIT_MESSAGES = True
# CHECK_WIP = False
# CHECK_LICENSE = True
# CHECK_PEP8 = True
# CHECK_PEP257 = True
# CHECK_PYFLAKES = True # PyFlakes requires PEP8

# You may ignore some codes from PEP8, PEP257 and
# the license checks as well.
IGNORE = ['E123', 'E226', 'E24', 'E501', 'E265']
# SELECT = []

# Apply the tests only to the files matching those criteria.
PEP257_MATCH = "(?!test_).*\.py"
"""Files checked for PEP257 conformance."""
PEP257_MATCH_DIR = "[^\.].*"
"""Directories checkes for PEP257 conformance."""

# Minimal number of reviewers needed to accept a commit.
#
# Default value, uncomment to change:
# MIN_REVIEWERS = 3

TRUSTED_DEVELOPERS = []
"""Super developers who's code never fail."""

# List of recognized signatures
#
#
SIGNATURES = ('Signed-off-by', 'Co-authored-by', 'Tested-by', 'Reviewed-by',
              'Acked-by')
"""Authors and reviewers signatures."""
ALT_SIGNATURES = 'Reported-by',
"""Alternative signatures recognized but not counted as reviewers."""


# Labels applied to the pull request in case we are in the following states:
# - wip, the wip label has been found in the title
# - review, some commit need more reviewers
# - ready, none of the above
#
# Default values, uncomment to change:
# LABEL_WIP = "in_work"
# LABEL_REVIEW = "in_review"
# LABEL_READY = "in_integration"

# Hooks
# -----

COMMIT_MSG_TEMPLATE = """{component}: description (max 50 chars, using nouns)

* Detailed description formatted as a bullet list (using present tense).

Signed-off-by: {author}
{extra}"""
"""Template used to generate the commit message from the git hook."""


HOOK_TEMPLATE = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from kwalitee import create_app
from kwalitee.hooks import {hook}

if __name__ == "__main__":
    with create_app().app_context():
        sys.exit({hook}(sys.argv))
"""
"""Template used to generate the git hooks, customize at will."""


COMMIT_MSG_LABELS = (
    ('SECURITY', 'Security fixes'),
    ('INCOMPATIBLE', 'Incompatible changes'),
    ('NEW', 'New features'),
    ('BETTER', 'Improved features'),
    ('FIX', 'Bug fixes'),
    ('NOTE', 'Notes'),
    ('AMENDS', None),
)
