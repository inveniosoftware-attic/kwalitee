# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014 CERN.
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

"""Configuration for py.test in views."""

import pytest

from kwalitee.models import Repository, CommitStatus, BranchStatus


@pytest.fixture(scope="function")
def repositories(owner, session, request):
    """Create a couple of repositories for a test."""
    repos = []
    names = "invenio", "test", "bob"
    for name in names:
        repos.append(Repository.find_or_create(owner, name))

    def teardown():
        for repo in repos:
            session.delete(repo)
        session.commit()

    request.addfinalizer(teardown)
    return repos


@pytest.fixture(scope="function")
def commits(owner, repository, session, request):
    """Create a couple of commits for a test."""
    cs = [
        {"sha": "ef01234"},
        {"sha": "789abcd"},
        {"sha": "0123456"},
    ]
    url_template = "https://github.com/commits/{sha}"

    commits = []
    for commit in cs:
        cs = CommitStatus(repository,
                          commit["sha"],
                          url_template.format(**commit),
                          {"message": [], "files": None})
        commits.append(cs)
        session.add(cs)
    session.commit()

    def teardown():
        for commit in commits:
            session.delete(commit)
        session.commit()

    request.addfinalizer(teardown)
    return commits


@pytest.fixture(scope="function")
def branch(owner, repository, commits, session, request):
    """Create a branch status for a test."""
    branch_name = "test:wip/my-branch"

    bs = BranchStatus(commits[-1],
                      branch_name,
                      "https://github.com/pulls/1",
                      {"commits": commits, "files": {}})
    session.add(bs)
    session.commit()

    def teardown():
        session.delete(bs)
        session.commit()

    request.addfinalizer(teardown)
    return bs
