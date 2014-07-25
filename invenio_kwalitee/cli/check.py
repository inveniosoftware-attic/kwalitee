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
##g
## You should have received a copy of the GNU General Public License
## along with Invenio-Kwalitee; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
##
## In applying this licence, CERN does not waive the privileges and immunities
## granted to it by virtue of its status as an Intergovernmental Organization
## or submit itself to any jurisdiction.

"""Command-line tools for checking commits."""

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys

from flask import current_app
from flask.ext.script import Manager

manager = Manager(usage="check commits")


@manager.option('commit', metavar='<sha or branch>', nargs='?',
                default='HEAD', help='an integer for the accumulator')
def message(commit='HEAD', repo='.'):
    """Check the messages of the commits.

    :param commit: commit to check
    :param repo: where is the repository to check
    """
    import git
    from ..kwalitee import check_message, get_options
    options = get_options(current_app.config)
    cwd = os.getcwd()
    os.chdir(repo)
    g = git.Repo('.')
    kwargs = {'with_keep_cwd': True}
    if '..' not in commit:
        kwargs['max_count'] = 1
    commits = list(g.iter_commits(commit, **kwargs))
    template = "{commit.summary}\ncommit {commit.hexsha}\n\n{errors}\n"

    count = 0
    for commit in g.iter_commits(commit, **kwargs):
        errors = check_message(commit.message, **options)
        if errors:
            count += 1
        else:
            errors = ['Everything is OK.']

        print(template.format(commit=commit, errors='\n'.join(errors)))

    os.chdir(cwd)
    return min(count, 1)
