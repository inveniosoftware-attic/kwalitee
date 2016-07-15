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

"""Test of author checking."""

import os
import shutil
import subprocess
import tempfile

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_length

from kwalitee.kwalitee import check_author


@pytest.fixture
def repository_with_author_commits():
    """A fixture creating test repository with some author commits."""
    cmds = (
        "git init",
        "git config user.name 'Jürg Müller'",
        "git config user.email juerg.mueller@example.org",
        "touch AUTHORS.rst",
        "echo 'John Doe <john.doe@example.org>' >> AUTHORS.rst",
        "echo 'Jane Doe <jane.doe@example.org>' >> AUTHORS.rst",
        "git add AUTHORS.rst",
        "git commit --allow-empty -m xxx "
        " --author 'John Doe <john.doe@example.org>'",
        "git commit --allow-empty -m xxx "
        " --author 'Jimmy Doe <jimmy.doe@example.org>'",
        "git commit --allow-empty -m xxx "
        " --author 'Jane Doe <john.doe@example.org>'",
    )

    path = tempfile.mkdtemp()
    cwd = os.getcwd()
    os.chdir(path)
    for command in cmds:
        proc = subprocess.Popen(command,
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


def test_check_authors_author_present_pygit2(repository_with_author_commits):
    """Test checking present authors, with pygit2."""
    pytest.importorskip("pygit2")
    options = dict(authors=["AUTHORS.rst", ],
                   path=repository_with_author_commits)
    errors = check_author('John Doe <john.doe@example.org>', **options)
    assert_that(errors, has_length(0))
    errors = check_author('Jane Doe <jane.doe@example.org>', **options)
    assert_that(errors, has_length(0))


def test_check_authors_author_present_gitpython(
    repository_with_author_commits
):
    """Test checking present authors, with GitPython."""
    pytest.importorskip("git")
    options = dict(authors=["AUTHORS.rst", ],
                   path=repository_with_author_commits)
    errors = check_author('John Doe <john.doe@example.org>', **options)
    assert_that(errors, has_length(0))
    errors = check_author('Jane Doe <jane.doe@example.org>', **options)
    assert_that(errors, has_length(0))


def test_check_authors_author_missing_pygit2(repository_with_author_commits):
    """Test checking missing authors, with pygit2."""
    pytest.importorskip("pygit2")
    options = dict(authors=["AUTHORS.rst", ],
                   path=repository_with_author_commits)
    errors = check_author('Jimmy Doe <jimmy.doe@example.org>', **options)
    assert_that(errors, has_length(1))
    assert_that(errors[0], contains_string('A102'))


def test_check_authors_author_missing_gitpython(
    repository_with_author_commits
):
    """Test checking missing authors, with GitPython."""
    pytest.importorskip("git")
    options = dict(authors=["AUTHORS.rst", ],
                   path=repository_with_author_commits)
    errors = check_author('Jimmy Doe <jimmy.doe@example.org>', **options)
    assert_that(errors, has_length(1))
    assert_that(errors[0], contains_string('A102'))


def test_check_authors_author_excluded_pygit2(repository_with_author_commits):
    """Test checking missing authors, with pygit2."""
    pytest.importorskip("pygit2")
    options = dict(authors=["AUTHORS.rst", ],
                   exclude_author_names=['Jimmy Doe <jimmy.doe@example.org>'],
                   path=repository_with_author_commits)
    errors = check_author('Jimmy Doe <jimmy.doe@example.org>', **options)
    assert_that(errors, has_length(0))
    errors = check_author('Jackie Doe <jackie.doe@example.org>', **options)
    assert_that(errors, has_length(1))
    assert_that(errors[0], contains_string('A102'))


def test_check_authors_author_excluded_gitpython(
    repository_with_author_commits
):
    """Test checking missing authors, with GitPython."""
    pytest.importorskip("git")
    options = dict(authors=["AUTHORS.rst", ],
                   exclude_author_names=['Jimmy Doe <jimmy.doe@example.org>'],
                   path=repository_with_author_commits)
    errors = check_author('Jimmy Doe <jimmy.doe@example.org>', **options)
    assert_that(errors, has_length(0))
    errors = check_author('Jackie Doe <jackie.doe@example.org>', **options)
    assert_that(errors, has_length(1))
    assert_that(errors[0], contains_string('A102'))


def test_check_authors_file_missing_pygit2(repository_with_author_commits):
    """Test checking missing authors, with pygit2."""
    pytest.importorskip("pygit2")
    options = dict(authors=["AUTHORS.md", ],
                   path=repository_with_author_commits)
    errors = check_author('John Doe <john.doe@example.org>', **options)
    assert_that(errors, has_length(1))
    assert_that(errors[0], contains_string('A101'))
    errors = check_author('Jimmy Doe <jimmy.doe@example.org>', **options)
    assert_that(errors, has_length(1))
    assert_that(errors[0], contains_string('A101'))


def test_check_authors_file_missing_gitpython(repository_with_author_commits):
    """Test checking missing authors, with GitPython."""
    pytest.importorskip("git")
    options = dict(authors=["AUTHORS.md", ],
                   path=repository_with_author_commits)
    errors = check_author('John Doe <john.doe@example.org>', **options)
    assert_that(errors, has_length(1))
    assert_that(errors[0], contains_string('A101'))
    errors = check_author('Jimmy Doe <jimmy.doe@example.org>', **options)
    assert_that(errors, has_length(1))
    assert_that(errors[0], contains_string('A101'))
