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

import os
import sys
import shutil
import tempfile
from unittest import TestCase
import six

from invenio_kwalitee import hooks


class MessageTest(TestCase):
    def test_commit_message(self):
        assert hooks.check_commit_message("") == 0
        assert hooks.check_commit_message("  ") == 0
        assert hooks.check_commit_message(" \n  \n  ") == 0
        assert hooks.check_commit_message("some message") == 3


class CheckFilesTest(TestCase):
    def setUp(self):
        self.path = tempfile.mkdtemp()
        fixtures = os.path.join(os.path.dirname(__file__), "fixtures")
        self.valid = os.path.join(self.path, "valid.py")
        self.invalid = os.path.join(self.path, "invalid.py")
        shutil.copyfile(
            os.path.join(fixtures, "valid.py.test"),
            self.valid
        )
        shutil.copyfile(
            os.path.join(fixtures, "invalid.py.test"),
            self.invalid
        )

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_check_filles(self):
        report = hooks.check_files([self.valid, self.invalid])
        assert report['count'] == 10


class GitHooksTest(TestCase):
    def setUp(self):
        self.path = tempfile.mkdtemp()

        os.chdir(self.path)

        cmds = [
            "git init",
            "git config user.name 'Test user'",
            "git config user.email 'info@invenio-software.org'",
            "touch empty.py",
            "git add empty.py",
            "git commit -m 'test'",
            "mkdir -p invenio/modules/testmod1/",
            "mkdir -p invenio/modules/testmod2/",
            "echo 'pass' > invenio/modules/testmod1/test.py",
            "echo 'pass' > invenio/modules/testmod2/test.py",
            "git add invenio/modules/testmod1/test.py",
            "git add invenio/modules/testmod2/test.py",
        ]

        for c in cmds:
            os.system("cd %s && %s" % (self.path, c))

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_post_commit_hook(self):
        assert hooks.post_commit_hook() == 3

    def test_pre_commit_hook(self):
        assert hooks.pre_commit_hook() == 2

    def test_prepare_commit_msg_hook(self):
        # Assert that the no message is prepared if file already have contents
        sys.argv[1] = tempfile.mkstemp(text=True)[1]
        with open(sys.argv[1], 'w') as fh:
            fh.write(six.u("Some content"))
        assert hooks.prepare_commit_msg_hook() == 0
        with open(sys.argv[1], 'r') as fh:
            assert fh.read() == "Some content"
        os.remove(sys.argv[1])

        sys.argv[1] = tempfile.mkstemp(text=True)[1]
        hooks.prepare_commit_msg_hook()
        assert hooks.commit_msg_hook() == 2
        os.remove(sys.argv[1])
