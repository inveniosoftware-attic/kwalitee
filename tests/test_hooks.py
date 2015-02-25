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

from __future__ import unicode_literals

import os
import sys
import pytest
import shutil
import tempfile
import subprocess
from io import StringIO
from unittest import TestCase
from mock import patch, mock_open, MagicMock
from hamcrest import (assert_that, equal_to, has_length, has_item, has_items,
                      is_not, contains_string)

from kwalitee.hooks import (_get_component, _get_components,
                                    _get_git_author, _get_files_modified,
                                    _pre_commit, _prepare_commit_msg,
                                    post_commit_hook, pre_commit_hook)


class GetComponentTest(TestCase):
    """Testing _get_component and _get_components."""

    def test_get_component(self):
        files = {
            "invenio/base/factory.py": "base",
            "invenio/modules/oauthclient/utils.py": "oauthclient",
            "zenodo/modules/deposit/__init__.py": "deposit",
            "invenio/legacy/bibupload/engine.py": "bibupload",
            "invenio/ext/sqlalchemy/__init__.py": "sqlalchemy",
            "docs/index.rst": "docs",
            "grunt/app.js": "grunt",
            "setup.py": "global",
        }

        for filename, expected in files.items():
            assert_that(_get_component(filename), equal_to(expected), filename)

    def test_get_components(self):
        components = _get_components(("setup.py", "test.py", "grunt/app.js"))
        assert_that(components, has_length(2))
        assert_that(components, has_items("global", "grunt"))


class PreCommitTest(TestCase):
    """Testing the pre-commit actions."""

    options = {"ignore": ("D100",)}

    def test_pre_commit(self):
        errors = _pre_commit((("__init__.py", b""),
                              ("a/b/c/d/e/f/g/test.py", b""),
                              ("i/j/k/error.py", b"import os")),
                             self.options)

        assert_that(
            errors,
            has_items(
                "i/j/k/error.py: 1: L101 copyright is missing",
                "i/j/k/error.py: 1:1: F401 'os' imported but unused"))


class PrepareCommitMsgTest(TestCase):
    """Testing the preparation of commit message."""

    def _mock_open(self, data=""):
        """Creates a mock for a file with the given data and returns the mock
        and the file handler.

        NB: everytime the file is reopened, it's trucated. To be used in
        read or read then write operations.
        """
        mock = mock_open()
        filehandler = StringIO(data)

        def _open():
            if filehandler.tell() > 0:
                filehandler.truncate(0)
                filehandler.seek(0)
            return filehandler

        mock.return_value = MagicMock(spec=StringIO)
        mock.return_value.__enter__.side_effect = _open
        return mock, filehandler

    def test_prepare_commit_msg(self):
        commit_msg = "# this is a comment"
        mock, tmp_file = self._mock_open(commit_msg)
        with patch("kwalitee.hooks.open", mock, create=True):
            _prepare_commit_msg("mock", "John",
                                template="{component}: {author}")

            tmp_file.seek(0)
            new_commit_msg = "\n".join(tmp_file.readlines())

            assert_that(new_commit_msg, equal_to("unknown: John"))

    def test_prepare_commit_msg_with_one_component(self):
        commit_msg = "# this is a comment"
        mock, tmp_file = self._mock_open(commit_msg)
        with patch("kwalitee.hooks.open", mock, create=True):
            _prepare_commit_msg("mock", "John",
                                ("setup.py", "test.py"),
                                "{component}")

            tmp_file.seek(0)
            new_commit_msg = "\n".join(tmp_file.readlines())

            assert_that(new_commit_msg, equal_to("global"))

    def test_prepare_commit_msg_with_many_components(self):
        commit_msg = "# this is a comment"
        mock, tmp_file = self._mock_open(commit_msg)
        with patch("kwalitee.hooks.open", mock, create=True):
            _prepare_commit_msg("mock", "John",
                                ("setup.py",
                                 "grunt/foo.js",
                                 "docs/bar.rst"),
                                "{component}")

            tmp_file.seek(0)
            new_commit_msg = "\n".join(tmp_file.readlines())

            assert_that(new_commit_msg, contains_string("global"))
            assert_that(new_commit_msg, contains_string("grunt"))
            assert_that(new_commit_msg, contains_string("docs"))

    def test_prepare_commit_msg_aborts_if_existing(self):
        commit_msg = "Lorem ipsum"
        mock, tmp_file = self._mock_open(commit_msg)
        with patch("kwalitee.hooks.open", mock, create=True):
            _prepare_commit_msg("mock", "John")

            tmp_file.seek(0)
            new_commit_msg = "\n".join(tmp_file.readlines())

            assert_that(new_commit_msg, equal_to(commit_msg))


@pytest.fixture(scope="function")
def github(app, session, request):
    commit_msg = "dummy: test\n\n" \
                 "* foo\n" \
                 "  bar\n\n" \
                 "Signed-off-by: John Doe <john.doe@example.org>"
    cmds = (
        "git init",
        "git config user.name 'Jürg Müller'",
        "git config user.email juerg.mueller@example.org",
        "touch empty.py",
        "git add empty.py",
        "git commit -m '{0}'".format(commit_msg),
        "touch README.rst",
        "git add README.rst",
        "mkdir -p invenio/modules/testmod1/",
        "mkdir invenio/modules/testmod2/",
        "echo pass > invenio/modules/testmod1/test.py",
        "echo pass > invenio/modules/testmod2/test.py",
        "touch invenio/modules/testmod1/script.js",
        "touch invenio/modules/testmod1/style.css",
        "git add invenio/modules/testmod1/test.py",
        "git add invenio/modules/testmod2/test.py",
        "git add invenio/modules/testmod1/script.js",
        "git add invenio/modules/testmod1/style.css",
    )

    config = app.config

    app.config.update({
        "COMPONENTS": ["dummy"],
        "TRUSTED_DEVELOPERS": ["john.doe@example.org"]
    })

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
        app.config = config

    request.addfinalizer(teardown)
    return path


def test_get_files_modified(github):
    assert_that(_get_files_modified(), is_not(has_item("empty.py")))
    assert_that(_get_files_modified(),
                has_items("README.rst",
                          "invenio/modules/testmod1/test.py",
                          "invenio/modules/testmod2/test.py",
                          "invenio/modules/testmod1/script.js",
                          "invenio/modules/testmod1/style.css"))


def test_get_git_author(github):
    assert_that(_get_git_author(),
                equal_to("Jürg Müller <juerg.mueller@example.org>"))


def test_post_commit_hook(github):
    """Hook: post-commit doesn't fail"""
    stderr = sys.stderr

    sys.stderr = StringIO()
    assert_that(post_commit_hook() == 0)
    sys.stderr.seek(0)
    output = "\n".join(sys.stderr.readlines())
    sys.stderr = stderr

    assert_that(output, has_length(0))


def test_pre_commit_hook(github):
    """Hook: pre-commit fails because some copyrights are missing"""
    stderr = sys.stderr

    sys.stderr = StringIO()
    assert_that(pre_commit_hook() == 1)
    sys.stderr.seek(0)
    output = "\n".join(sys.stderr.readlines())
    sys.stderr = stderr

    assert_that(output, contains_string("kwalitee errors"))
