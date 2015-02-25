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

from hamcrest import assert_that, equal_to, contains_string


def test_get_account(app, owner, repositories):
    """GET /{account} displays the repositories."""

    tester = app.test_client()
    response = tester.get("/{0}/".format(owner.name))

    assert_that(response.status_code, equal_to(200))
    for repository in repositories:
        assert_that(response.get_data(as_text=True),
                    contains_string("/{0}/{1}/".format(owner.name,
                                                       repository.name)))


def test_get_account_doesnt_exist(app):
    """GET /{account} raise 404 if not found."""

    tester = app.test_client()
    response = tester.get("/404/")

    assert_that(response.status_code, equal_to(404))
