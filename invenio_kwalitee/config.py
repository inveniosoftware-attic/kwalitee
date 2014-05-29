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

"""
Invenio-Kwalitee base configuration.

To change it, put a config.py into your instance.
"""

# Context for the Github statuses.
#
# See: https://developer.github.com/v3/repos/statuses/
CONTEXT = "invenio-kwalitee"
# Github urls
GITHUB = "https://github.com/"
GITHUB_REPO = GITHUB + "{account}/{repository}/"

# Allows anyone to add its repository by setting up the webhook on Github.
# Disable this to force manual creation. Default to False
#AUTO_CREATE = False

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
    'authorids',
    'authorprofiles',
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

SIGNATURES = 'Signed-off-by', 'Tested-by', 'Reviewed-by'
ALT_SIGNATURES = 'Reported-by',

# RQ default timeout is 180 seconds
WORKER_TIMEOUT = 300

TRUSTED_DEVELOPERS = []

# Checks run on the files
#
# Default values, uncomment to change:
#CHECK_COMMIT_MESSAGES = True
#CHECK_WIP = False
#CHECK_LICENSE = True
#CHECK_PEP8 = True
#CHECK_PEP257 = True
#CHECK_PYFLAKES = True # PyFlakes requires PEP8

# You may ignore some codes from PEP8, PEP257 and
# the license checks as well.
IGNORE = ['E123', 'E226', 'E24', 'E501', 'E265']
#SELECT = []

# Apply the tests only to the files matching those criteria.
PEP257_MATCH = "(?!test_).*\.py"
PEP257_MATCH_DIR = "[^\.].*"

# Labels applied to the pull request in case we are in the following states:
# - wip, the wip label has been found in the title
# - review, some commit need more reviewers
# - ready, none of the above
#
# Default values, uncomment to change:
#LABEL_WIP = "in_work"
#LABEL_REVIEW = "in_review"
#LABEL_READY = "in_integration"


COMMIT_MSG_TEMPLATE = """{component}: description (max 50 chars, using nouns)

* Detailed description formatted as a bullet list (using present tense).

Signed-off-by: {author}
{extra}"""


HOOK_TEMPLATE = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from invenio_kwalitee.hooks import {hook}

if __name__ == "__main__":
    sys.exit({hook}(sys.argv))
"""
