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

import sys
import pytest
from hamcrest import assert_that, equal_to, has_item, has_items

from kwalitee.cli.check import message

try:
    import pygit2  # noqa
    pygit = True
except ImportError:
    pygit = False

skip = pytest.mark.skipif(sys.version_info > (3, 0) and not pygit,
                          reason="no pygit2 and not GitPython")


@skip
def test_check_head(capsys, session, app, git):
    app.config['COLORS'] = False

    assert_that(message("HEAD", repository=git), equal_to(1))

    out, _ = capsys.readouterr()
    assert_that(out.split("\n"),
                has_items("1: M110 missing component name",
                          "1: M101 signature is missing",
                          "1: M100 needs more reviewers"))


@skip
def test_check_branch(capsys, session, app, git):
    app.config['TRUSTED_DEVELOPERS'] = ('a@b.org',)
    app.config['SIGNATURES'] = ('By',)
    app.config['COMPONENTS'] = ('global',)
    app.config['COLORS'] = False

    assert_that(message("master..testbranch", repository=git), equal_to(0))

    out, _ = capsys.readouterr()
    assert_that(out.split("\n"), has_item("Everything is OK."))


@skip
def test_check_branch_wrong_side(capsys, session, app, git):
    app.config['COLORS'] = False

    assert_that(message("testbranch..master", repository=git), equal_to(0))

    out, _ = capsys.readouterr()
    assert_that(out.strip(), equal_to(""))
