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

from kwalitee.models import (Account, Repository, CommitStatus,
                                     BranchStatus)
from kwalitee.cli.account import add, remove, list as list_


def test_add(capsys, session):
    add("invenio", "invenio@example.org", "123")
    _, err = capsys.readouterr()
    assert_that(err, contains_string("invenio"))
    assert_that(Account.query.filter_by(name="invenio",
                                        email="invenio@example.org",
                                        token="123").count(),
                equal_to(1))


def test_add_existing(session):
    add("invenio", "test@example.org", "123")
    add("invenio", "invenio@example.org")
    add("invenio", token="456")
    assert_that(Account.query.filter_by(name="invenio",
                                        email="invenio@example.org",
                                        token="456").count(),
                equal_to(1))


def test_remove(session):
    """remove {account} drops everything tied to it"""
    add("invenio")

    acc = Account.query.filter_by(name="invenio").first()
    rep = Repository.find_or_create(acc, "foo")
    commit = CommitStatus(rep, "1", "http://")
    session.add(commit)
    session.commit()
    bs = BranchStatus(commit, "1", "http://")
    session.add(bs)
    session.commit()

    remove("invenio")

    assert_that(Account.query.filter_by(name="invenio").count(),
                equal_to(0))
    assert_that(Repository.query.filter_by(name="foo").count(),
                equal_to(0))
    assert_that(CommitStatus.query.filter_by(repository_id=rep.id).count(),
                equal_to(0))
    assert_that(BranchStatus.query.filter_by(commit_id=commit.id).count(),
                equal_to(0))


def test_double_remove(session):
    add("invenio")
    remove("invenio")
    remove("invenio")
    assert_that(Account.query.filter_by(name="invenio").count(),
                equal_to(0))


def test_list(capsys, session):
    repos = ["a", "bc", "def", "ghijklmop"]
    for i in range(len(repos)):
        add(repos[-i])
    add("test", "test@тест.укр")
    list_()
    out, _ = capsys.readouterr()
    assert_that(out, string_contains_in_order(*repos))
    assert_that(out, contains_string("test@тест.укр"))
