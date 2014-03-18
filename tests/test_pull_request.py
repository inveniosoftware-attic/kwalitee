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

import httpretty
from flask import json
from unittest import TestCase
from invenio_kwalitee import app, kw


class PullRequestTest(TestCase):
    @httpretty.activate
    def test_pull_request(self):
        """Pull request should do the checks..."""
        kw.token = "deadbeef"

        commits = [{
            "url": "https://github.com/pulls/1/commits",
            "sha": 1,
            "comments_url": "https://github.com/commits/1/comments",
            "commit": {
                "message": "fix all the bugs!"
            }
        }]
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1/commits",
                               body=json.dumps(commits),
                               content_type="application/json")
        comment = {"id": 1}
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/commits/1/comments",
                               status=201,
                               body=json.dumps(comment),
                               content_type="application/json")
        status = {"id": 1, "state": "success"}
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/pulls/1/statuses",
                               status=201,
                               body=json.dumps(status),
                               content_type="application/json")

        tester = app.test_client(self)
        pull_request = {
            "action": "opened",
            "number": 1,
            "pull_request": {
                "url": "https://github.com/pulls/1",
                "commits_url": "https://github.com/pulls/1/commits",
                "statuses_url": "https://github.com/pulls/1/statuses",
                "head": {
                    "sha": "1"
                }
            }
        }
        response = tester.post("/payload", content_type="application/json",
                               headers=(("X-GitHub-Event", "pull_request"),
                                        ("X-GitHub-Delivery", "1")),
                               data=json.dumps(pull_request))
        self.assertEqual(200, response.status_code)
        body = json.loads(httpretty.last_request().body)
        self.assertEqual(u"token {0}".format(kw.token),
                         httpretty.last_request().headers["Authorization"])
        self.assertEqual(u"error", body["state"])
