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

import sys

import click
import pytest
import yaml
from click.testing import CliRunner
from hamcrest import assert_that, equal_to, has_item, has_items

from kwalitee.cli.check import Repo, check

try:
    import pygit2  # noqa
    pygit = True
except ImportError:
    pygit = False

skip = pytest.mark.skipif(sys.version_info > (3, 0) and not pygit,
                          reason="no pygit2 and not GitPython")


@skip
def test_check_head(capsys, git):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test.yml', 'w') as f:
            yaml.dump({
                'colors': False,
            }, stream=f)
        result = runner.invoke(check, ['-r', git, '-c', 'test.yml',
                                       'message', 'HEAD'])

        assert_that(result.exit_code != 0)
        assert_that(result.output.split("\n"),
                    has_items("1: M110 missing component name",
                              "1: M101 signature is missing",
                              "1: M100 needs more reviewers"))


@skip
def test_check_branch(capsys, git):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test.yml', 'w') as f:
            yaml.dump({
                'trusted': ('a@b.org', ),
                'signatures': ('By', ),
                'components': ('global', ),
                'colors': False,
            }, stream=f)
        result = runner.invoke(check, ['-r', git, '-c', 'test.yml',
                                       'message', 'master..testbranch'])
        assert_that(result.exit_code, equal_to(0))
        assert_that(result.output.split("\n"), has_item("Everything is OK."))


@skip
def test_check_branch_wrong_side(capsys, git):
    runner = CliRunner()
    result = runner.invoke(check, ['-r', git, 'message', 'testbranch..master'])
    assert_that(result.exit_code, equal_to(0))
    assert_that(result.output.split("\n"), equal_to([""]))
