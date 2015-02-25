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

from hamcrest import (assert_that, equal_to, contains_string,
                      string_contains_in_order)
from kwalitee.models import Account, Repository
from kwalitee.cli.repository import add, remove, list as list_


def test_add(capsys, session):
    add("invenio/kwalitee")
    _, err = capsys.readouterr()
    assert_that(err, contains_string("invenio/kwalitee"))
    assert_that(Account.query.filter_by(name="invenio").count(),
                equal_to(1))
    assert_that(Repository.query.filter_by(name="kwalitee").count(),
                equal_to(1))


def test_add_existing(session):
    add("invenio/kwalitee")
    add("invenio/kwalitee")
    assert_that(Account.query.filter_by(name="invenio").count(),
                equal_to(1))
    assert_that(Repository.query.filter_by(name="kwalitee").count(),
                equal_to(1))


def test_add_invalid_name(capsys, session):
    assert_that(add("foo"), equal_to(1))
    _, err = capsys.readouterr()
    assert_that(err, contains_string("foo is not a valid repository"))


def test_remove(session):
    add("invenio/kwalitee")
    remove("invenio/kwalitee")
    remove("invenio/kwalitee")
    remove("kwalitee/kwalitee")
    assert_that(Account.query.filter_by(name="invenio").count(),
                equal_to(1))
    assert_that(Repository.query.filter_by(name="kwalitee").count(),
                equal_to(0))


def test_remove_invalid_name(capsys, session):
    assert_that(remove("foo"), equal_to(1))
    _, err = capsys.readouterr()
    assert_that(err, contains_string("foo is not a valid repository"))


def test_list(capsys, session):
    repos = ["a/a", "bcd/def", "foo-bar/spam-and-eggs", "foo-bar/zoo"]
    for i in range(len(repos)):
        add(repos[-i])
    list_()
    out, _ = capsys.readouterr()
    assert_that(out, string_contains_in_order(*repos))
