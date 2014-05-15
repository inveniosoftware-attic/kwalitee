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

from __future__ import unicode_literals

from flask import json
from unittest import TestCase
from invenio_kwalitee import app
from hamcrest import assert_that, equal_to


class PingTest(TestCase):
    """Integration tests for the ping event."""
    def test_ping(self):
        """POST /payload (ping) is ignored by kwalitee"""
        tester = app.test_client(self)
        response = tester.post("/payload", content_type="application/json",
                               headers=(("X-GitHub-Event", "ping"),
                                        ("X-GitHub-Delivery", "1")),
                               data=json.dumps({"hook_id": 1,
                                                "zen": "Responsive is better "
                                                       "than fast."}))
        assert_that(response.status_code, equal_to(200))

    def test_ping_no_headers(self):
        """POST /payload (ping) expects a X-GitHub-Event header"""
        tester = app.test_client(self)
        response = tester.post("/payload",
                               data=json.dumps({"hook_id": 1,
                                                "zen": "Responsive is better "
                                                       "than fast."}))
        body = json.loads(response.data)
        assert_that(response.status_code, equal_to(500))
        assert_that(body["exception"],
                    equal_to("No X-GitHub-Event HTTP header found"))
        assert_that(body["status"], equal_to("failure"))

    def test_not_a_ping(self):
        """POST /payload (pong) rejects an unknown event"""
        tester = app.test_client(self)
        response = tester.post("/payload",
                               headers=(("X-GitHub-Event", "pong"),
                                        ("X-GitHub-Delivery", "1")),
                               data=json.dumps({"hook_id": 1,
                                                "zen": "Responsive is better "
                                                       "than fast."}))
        body = json.loads(response.data)
        assert_that(response.status_code, equal_to(500))
        assert_that(body["exception"],
                    equal_to("Event pong is not supported"))
        assert_that(body["status"], equal_to("failure"))
