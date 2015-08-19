# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2015 CERN.
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

"""Test of merge commit detection."""

from __future__ import unicode_literals

import os
import shutil
import subprocess
import tempfile

from hamcrest import (assert_that, equal_to)

from kwalitee.cli.check import _git_commits, _is_merge_commit, _pygit2_commits

import pytest


@pytest.fixture
def repository_with_merge_commits():
    """A fixture creating test repository with merge commits."""
    cmds = (
        "git init",
        "git config user.name 'Jürg Müller'",
        "git config user.email juerg.mueller@example.org",
        "touch master.py",
        "git add master.py",
        "git commit -m master",
        "git checkout -b test",
        "touch test.py",
        "git add test.py",
        "git commit -m test",
        "git checkout master",
        "touch master2.py",
        "git add master2.py",
        "git commit -m master2",
        "git merge test",
    )

    path = tempfile.mkdtemp()
    cwd = os.getcwd()
    os.chdir(path)
    for command in cmds:
        proc = subprocess.Popen(command.encode("utf-8"),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True,
                                cwd=path)
        (stdout, stderr) = proc.communicate()
        assert_that(proc.returncode, equal_to(0),
                    "{0}: {1}".format(command, stderr))

    def teardown():
        shutil.rmtree(path)
        os.chdir(cwd)

    return path


def test_merge_commit_detection_pygit2(repository_with_merge_commits):
    """Test detection of merge and non-merge commits with PyGit2."""
    pytest.importorskip("pygit2")
    commits = _pygit2_commits('HEAD^..', repository_with_merge_commits)
    first_commit, second_commit = commits
    assert _is_merge_commit(commits[0])
    assert not _is_merge_commit(commits[1])


def test_merge_commit_detection_git(repository_with_merge_commits):
    """Test detection of merge and non-merge commits with GitPython."""
    pytest.importorskip("git")
    commits = _git_commits('HEAD^..', repository_with_merge_commits)
    assert _is_merge_commit(commits[0])
    assert not _is_merge_commit(commits[1])


def test_commit_log_history_pygit2(repository_with_merge_commits):
    """Test detection of commit log messages with PyGit2."""
    pytest.importorskip("pygit2")
    commits = _pygit2_commits('HEAD^^..HEAD', repository_with_merge_commits)
    assert commits.message == "Merge branch 'test'\n"
    assert commits.message == "master2\n"
    assert commits.message == "test\n"


def test_commit_log_history_git(repository_with_merge_commits):
    """Test detection of commit log messages with GitPython."""
    pytest.importorskip("git")
    commits = _git_commits('HEAD^^..HEAD', repository_with_merge_commits)
    assert commits[0].message == "Merge branch 'test'\n"
    assert commits[1].message == "master2\n"
    assert commits[2].message == "test\n"
