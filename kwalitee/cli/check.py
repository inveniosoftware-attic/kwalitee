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

"""Command-line tools for checking commits."""

from __future__ import absolute_import, print_function, unicode_literals

import colorama
import os
import re
import shutil
import sys

from flask import current_app
from flask_script import Manager

from tempfile import mkdtemp

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
        head = head or 'HEAD'
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
    from ..hooks import _read_local_kwalitee_configuration
    options = get_options(current_app.config)
    options.update(_read_local_kwalitee_configuration(directory=repository))

    if options.get('colors') is not False:
        colorama.init(autoreset=True)
        reset = colorama.Style.RESET_ALL
        yellow = colorama.Fore.YELLOW
        green = colorama.Fore.GREEN
        red = colorama.Fore.RED
    else:
        reset = yellow = green = red = ''

    try:
        sha = 'oid'
        commits = _pygit2_commits(commit, repository)
    except ImportError:
        try:
            sha = 'hexsha'
            commits = _git_commits(commit, repository)
        except ImportError:
            print('To use this feature, please install pygit2. GitPython will '
                  'also work but is not recommended (python <= 2.7 only).',
                  file=sys.stderr)
            return 2

    template = '{0}commit {{commit.{1}}}{2}\n\n'.format(yellow, sha, reset)
    template += '{message}{errors}'

    count = 0
    ident = '    '
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


@manager.option('repository', default='.', nargs='?', help='repository path')
@manager.option('commit', metavar='<sha or branch>', nargs='?',
                default='HEAD', help='an integer for the accumulator')
def files(commit='HEAD', repository='.'):
    """Check the files of the commits."""
    from ..kwalitee import check_file, get_options, SUPPORTED_FILES
    from ..hooks import run, _read_local_kwalitee_configuration
    options = get_options(current_app.config)
    options.update(_read_local_kwalitee_configuration(directory=repository))

    if options.get('colors') is not False:
        colorama.init(autoreset=True)
        reset = colorama.Style.RESET_ALL
        yellow = colorama.Fore.YELLOW
        green = colorama.Fore.GREEN
        red = colorama.Fore.RED
    else:
        reset = yellow = green = red = ''

    try:
        sha = 'oid'
        commits = _pygit2_commits(commit, repository)
    except ImportError:
        try:
            sha = 'hexsha'
            commits = _git_commits(commit, repository)
        except ImportError:
            print('To use this feature, please install pygit2. GitPython will '
                  'also work but is not recommended (python <= 2.7 only).',
                  file=sys.stderr)
            return 2

    template = '{0}commit {{commit.{1}}}{2}\n\n'.format(yellow, sha, reset)
    template += '{message}{errors}\n'

    error_template = '\n{0}{{filename}}\n{1}{{errors}}{0}'.format(reset, red)
    no_errors = ['\n{0}Everything is OK.{1}'.format(green, reset)]
    msg_file_excluded = '\n{0}{{filename}} excluded.{1}'.format(yellow, reset)

    def _get_files_modified(commit):
        """Get the list of modified files that are Python or Jinja2."""
        cmd = "git show --no-commit-id --name-only --diff-filter=ACMRTUXB {0}"
        _, files_modified, _ = run(cmd.format(commit))

        extensions = [re.escape(ext)
                      for ext in list(SUPPORTED_FILES) + [".rst"]]
        test = "(?:{0})$".format("|".join(extensions))
        return list(filter(lambda f: re.search(test, f), files_modified))

    def _ensure_directory(filename):
        dir_ = os.path.dirname(filename)
        if not os.path.exists(dir_):
            os.makedirs(dir_)

    def _format_errors(args):
        filename, errors = args
        if errors is None:
            return msg_file_excluded.format(filename=filename)
        else:
            return error_template.format(filename=filename, errors='\n'.join(
                errors if len(errors) else no_errors))

    count = 0
    ident = '    '
    re_line = re.compile('^', re.MULTILINE)
    for commit in commits:
        message = commit.message
        commit_sha = getattr(commit, sha)
        tmpdir = mkdtemp()
        errors = {}
        try:
            for filename in _get_files_modified(commit):
                cmd = "git show {commit_sha}:{filename}"
                _, out, _ = run(cmd.format(commit_sha=commit_sha,
                                           filename=filename),
                                raw_output=True)

                destination = os.path.join(tmpdir, filename)
                _ensure_directory(destination)

                with open(destination, 'w+') as f:
                    f.write(out)

                errors[filename] = check_file(destination, **options)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        message = re.sub(re_line, ident, message)
        if len(errors):
            count += 1
            errors = map(_format_errors, errors.items())
        else:
            errors = no_errors

        print(template.format(commit=commit,
                              message=message,
                              errors='\n'.join(errors)))

    return min(count, 1)
