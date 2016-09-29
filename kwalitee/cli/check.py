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

"""Command-line tools for checking commits."""

from __future__ import absolute_import, print_function

import os
import re
import shutil
from tempfile import mkdtemp

import click
import colorama
import yaml

from . import utils
from ..hooks import _read_local_kwalitee_configuration
from ..kwalitee import get_options


class Repo(object):
    """Hold information about repository."""

    def __init__(self, repository='.', config=None):
        """Store information about repository and get kwalitee options."""
        self.repository = repository
        self.options = get_options()
        self.options.update(_read_local_kwalitee_configuration(
            directory=repository))
        if config:
            self.options.update(
                yaml.load(config.read())
            )
        self._template = None

        if self.options.get('colors') is not False:
            colorama.init(autoreset=True)
            self.colors = {
                'reset': colorama.Style.RESET_ALL,
                'yellow': colorama.Fore.YELLOW,
                'green': colorama.Fore.GREEN,
                'red': colorama.Fore.RED,
            }
        else:
            self.colors = {'reset': '', 'yellow': '', 'green': '', 'red': ''}

    def iter_commits(self, commit, skip_merge_commits=True):
        """Yield git commits from current repository."""
        try:
            self.sha = 'oid'
            commits = utils._pygit2_commits(commit, self.repository)
        except ImportError:
            try:
                self.sha = 'hexsha'
                commits = utils._git_commits(commit, self.repository)
            except ImportError:
                raise click.ClickException(
                    'To use this feature, please install pygit2. '
                    'GitPython will also work but is not recommended '
                    '(python <= 2.7 only).'
                )
        for commit in commits:
            if skip_merge_commits and utils._is_merge_commit(commit):
                continue
            yield commit

    @property
    def template(self):
        """Return preformatted message template."""
        if self._template:
            return self._template

        self._template = (
            '{yellow}commit {{commit.{sha}}}{reset}\n\n'
            '{{message}}{{errors}}'.format(
                sha=self.sha, **self.colors
            )
        )
        return self._template

pass_repo = click.make_pass_decorator(Repo)
processors = []


def validate_processors(ctx, param, value):
    """Validate processor names."""
    names = set(value.split(',')) if value else {}

    def _processors():
        """Yield valid processors."""
        for processor in processors:
            if names and processor.__name__ not in names:
                raise click.BadParameter(
                    'Invalid processor "{0}"'.format(processor.__name__),
                    ctx=ctx, param=param
                )
            yield processor

    return list(_processors())


@click.command()
@click.option('-r', '--repository', envvar='KWALITEE_REPO', default='.')
@click.option('-c', '--config', type=click.File('rb'), default=None)
@click.option('-s', '--skip-merge-commits', is_flag=True,
              help='skip merge commits')
@click.option('--select', metavar='<rule>', callback=validate_processors)
@click.argument(
    'commit_range', metavar='<sha or branch>',
    default=lambda: utils.travis_commit_range() or utils.local_commit_range(),
)
def check(repository, config, skip_merge_commits, select, commit_range):
    """Check commits."""
    obj = Repo(repository=repository, config=config)

    count = 0
    ident = '    '
    re_line = re.compile('^', re.MULTILINE)
    for commit in obj.iter_commits(commit_range, skip_merge_commits):
        errors = []
        for processor in select:
            errors += processor(obj, commit)

        message = re.sub(re_line, ident, commit.message).encode('utf-8')

        if errors:
            count += 1
            errors.insert(0, obj.colors['red'])
        else:
            errors = [obj.colors['green'], 'Everything is OK.']
        errors.append(obj.colors['reset'])

        click.echo(obj.template.format(
            commit=commit,
            message=message,
            errors='\n'.join(errors),
        ))

    if min(count, 1):
        raise click.Abort


@processors.append
def message(repo, commit):
    """Check the messages of the commits."""
    from ..kwalitee import check_message

    return check_message(commit.message, **repo.options)


@processors.append
def authors(repo, commit):
    """Check the authors of the commits."""
    from ..kwalitee import check_author

    author = u'{0.author.name} <{0.author.email}>'.format(
        commit).encode('utf-8')
    return check_author(author, **repo.options)


@processors.append
def files(repo, commit):
    """Check the files of the commits."""
    from ..kwalitee import check_file, SUPPORTED_FILES
    from ..hooks import run

    obj = repo
    options = repo.options

    error_template = '\n{reset}{{filename}}\n{red}{{errors}}{reset}'.format(
        **obj.colors)
    no_errors = ['{green}Everything is OK.{reset}'.format(**obj.colors)]
    msg_file_excluded = '\n{yellow}{{filename}} excluded.{reset}'.format(
        **obj.colors)

    def _get_files_modified(commit):
        """Get the list of modified files that are Python or Jinja2."""
        cmd = "git show --no-commit-id --name-only --diff-filter=ACMRTUXB {0}"
        _, files_modified, _ = run(cmd.format(commit))

        extensions = [
            re.escape(ext) for ext in list(SUPPORTED_FILES) + [".rst"]
        ]
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

    commit_sha = getattr(commit, obj.sha)
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

    if len(errors):
        errors = map(_format_errors, errors.items())

    return errors
