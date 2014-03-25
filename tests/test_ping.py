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

from flask import json
from unittest import TestCase
from invenio_kwalitee import app


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
        self.assertEqual(200, response.status_code)

    def test_ping_no_headers(self):
        """POST /payload (ping) expects a X-GitHub-Event header"""
        tester = app.test_client(self)
        response = tester.post("/payload",
                               data=json.dumps({"hook_id": 1,
                                                "zen": "Responsive is better "
                                                       "than fast."}))
        body = json.loads(response.data)
        self.assertEqual(500, response.status_code)
        self.assertEqual(u"No X-GitHub-Event HTTP header found",
                         body["exception"])
        self.assertEqual(u"failure", body["status"])

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
        self.assertEqual(500, response.status_code)
        self.assertEqual(u"Event pong is not supported",
                         body["exception"])
        self.assertEqual(u"failure", body["status"])
