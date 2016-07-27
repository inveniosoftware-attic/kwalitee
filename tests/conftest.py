# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014, 2016 CERN.
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

"""Configuration for py.test."""

import shutil
import subprocess
import tempfile

import pytest


@pytest.fixture(scope="function")
def git(request):
    """Create a git repository."""
    repo = tempfile.mkdtemp()

    commands = (("git", "init"),
                ("git", "config", "user.name", "Herp Derpson"),
                ("git", "config", "user.email", "herp.derpson@example.org"),
                ("touch", "README.rst"),
                ("git", "add", "README.rst"),
                ("git", "commit", "-m", "empty README"),
                ("git", "checkout", "-b", "testbranch"),
                ("touch", "TODO"),
                ("git", "add", "TODO"),
                ("git", "commit", "-m", "global: kikoo\n\nBy: bob <a@b.org>"),
                ("git", "checkout", "master"),
                ("git", "checkout", "-b", "utf8"),
                ("touch", "líščí.txt"),
                ("git", "add", "líščí.txt"),
                ("git", "commit", "-m", "global: líščí\n\n"
                    "* Příliš žluťoučký kůň úpěl ďábelské ódy.\n\nSigned-off-by: Motörhead <a@b.org>"),
                ("git", "checkout", "master"))

    for command in commands:
        status = subprocess.Popen(command,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  cwd=repo).wait()
        assert 0 == status, " ".join(command)

    def teardown():
        try:
            shutil.rmtree(repo)
        except Exception:
            pass

    request.addfinalizer(teardown)
    return repo
