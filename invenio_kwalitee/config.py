"""
Invenio-Kwalitee base configuration.

To change it, put a config.py into your instance.
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

TRUSTED_DEVELOPERS = []

REPO_URL = 'https://github.com/inveniosoftware/invenio/'

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
