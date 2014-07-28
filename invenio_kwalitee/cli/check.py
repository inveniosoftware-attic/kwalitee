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

"""Command-line tools for checking commits."""

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import sys
import colorama

from flask import current_app
from flask.ext.script import Manager

manager = Manager(usage='check commits')


def _git_commits(commit, repository):
    import git
    cwd = os.getcwd()
    os.chdir(repository)
    g = git.Repo('.')
    kwargs = {'with_keep_cwd': True}
    if '..' not in commit:
        kwargs['max_count'] = 1
    commits = list(g.iter_commits(commit, **kwargs))

    os.chdir(cwd)
    return commits


def _pygit2_commits(commit, repository):
    from pygit2 import Repository, GIT_SORT_TOPOLOGICAL
    g = Repository(repository)

    if '..' in commit:
        tail, head = commit.split('..', 2)
    else:
        head = commit
        tail = commit + '^'

    walker = g.walk(g.revparse_single(head).oid, GIT_SORT_TOPOLOGICAL)

    try:
        walker.hide(g.revparse_single(tail).oid)
    except KeyError:
        pass

    return walker


@manager.option('repository', default='.', nargs='?', help='repository path')
@manager.option('commit', metavar='<sha or branch>', nargs='?',
                default='HEAD', help='an integer for the accumulator')
def message(commit='HEAD', repository='.'):
    """Check the messages of the commits."""
    from ..kwalitee import check_message, get_options
    options = get_options(current_app.config)

    if options.get('colors') is not False:
        colorama.init(autoreset=True)
        reset = colorama.Style.RESET_ALL
        yellow = colorama.Fore.YELLOW
        green = colorama.Fore.GREEN
        red = colorama.Fore.RED
    else:
        reset = yellow = green = red = ''

    try:
        sha = "oid"
        commits = _pygit2_commits(commit, repository)
    except ImportError:
        try:
            sha = "hexsha"
            commits = _git_commits(commit, repository)
        except ImportError:
            print('To use this feature, please install pygit2. GitPython will '
                  'also work but is not recommended (python <= 2.7 only).',
                  file=sys.stderr)
            return 2

    template = '{0}commit {{commit.{1}}}{2}\n\n'.format(yellow, sha, reset)
    template += '{message}{errors}'

    count = 0
    ident = "    "
    re_line = re.compile('^', re.MULTILINE)
    for commit in commits:
        message = commit.message
        errors = check_message(message, **options)
        message = re.sub(re_line, ident, message)
        if errors:
            count += 1
            errors.insert(0, red)
        else:
            errors = [green, 'Everything is OK.']
        errors.append(reset)

        print(template.format(commit=commit,
                              message=message,
                              errors='\n'.join(errors)))

    return min(count, 1)
