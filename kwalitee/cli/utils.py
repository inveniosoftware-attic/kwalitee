# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2016 CERN.
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

"""Git range detections."""

import os
import traceback

import click
import pkg_resources
import requests


def open_entry_point(group_name):
    """Open entry point."""
    def loader(dummy_ctx, param, value):
        """Load entry point from group name based on given value."""
        entry_points = list(pkg_resources.iter_entry_points(
            group_name, value
        ))
        assert len(entry_points) == 1
        return entry_points[0].load()
    return loader


def with_plugins(group_name):
    """Register external CLI commands."""
    def decorator(group):
        """Attach loaded commands to the group."""
        if not isinstance(group, click.Group):
            raise TypeError(
                'Plugins can only be attached to an instance of click.Group.'
            )
        for entry_point in pkg_resources.iter_entry_points(group_name):
            try:
                group.add_command(entry_point.load())
            except Exception:
                click.echo('Command {0} could not be loaded. \n\n{1}'.format(
                    entry_point.name, traceback.format_exc()
                ))
        return group
    return decorator


#
# Default commit range detection.
#
def travis_commit_range():
    """Return commit range used in current PR or push."""
    commit_range = os.getenv('TRAVIS_COMMIT_RANGE')
    pull_request = os.getenv('TRAVIS_PULL_REQUEST')
    if pull_request and pull_request != 'false':
        url = 'https://github.com/{TRAVIS_REPO_SLUG}/pull/{TRAVIS_PULL_REQUEST}.patch'.format(
            TRAVIS_REPO_SLUG=os.getenv('TRAVIS_REPO_SLUG'),
            TRAVIS_PULL_REQUEST=pull_request,
        )
        header = next(requests.get(url).iter_lines())
        first_sha1 = header.split(' ')[1]
        commit_range = '{0}^..{1}'.format(
            first_sha1, os.getenv('TRAVIS_COMMIT')
        )
    return commit_range


def local_commit_range():
    """Return commit range of a topical branch."""
    return 'HEAD'


#
# Git compatibility layer.
#
def _git_commits(commit, repository):
    """Find git commits using ``git`` library."""
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
    """Find git commits using ``pygit2`` library."""
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


def _is_merge_commit(commit):
    """Test whether the commit is a merge commit or not."""
    if len(commit.parents) > 1:
        return True
    return False
