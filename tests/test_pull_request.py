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
import shutil
import tempfile
import httpretty

from flask import json
from unittest import TestCase
from invenio_kwalitee import app, pull_request
from hamcrest import assert_that, equal_to, contains_string


class PullRequestTest(TestCase):
    """Integration tests for the pull_request event."""

    class MyQueue(object):
        def __init__(self):
            self.queue = []

        def __len__(self):
            return len(self.queue)

        def dequeue(self):
            return self.queue.pop()

        def enqueue(self, *args):
            self.queue.append(args)

    def test_pull_request(self):
        """POST /payload (pull_request) performs the checks"""
        queue = self.MyQueue()
        # Replace the default Redis queue
        app.config["queue"] = queue

        pull_request_event = {
            "action": "opened",
            "number": 1,
            "pull_request": {
                "title": "Lorem ipsum",
                "url": "https://github.com/pulls/1",
                "commits_url": "https://github.com/pulls/1/commits",
                "statuses_url": "https://github.com/pulls/1/statuses",
                "head": {
                    "sha": "1"
                }
            }
        }

        tester = app.test_client(self)
        response = tester.post("/payload", content_type="application/json",
                               headers=(("X-GitHub-Event", "pull_request"),
                                        ("X-GitHub-Delivery", "1")),
                               data=json.dumps(pull_request_event))

        assert_that(response.status_code, equal_to(200))
        body = json.loads(response.data)
        assert_that(body["payload"]["state"], equal_to("pending"))

        (fn, pull_request_url, status_url, config) = queue.dequeue()
        self.assertEquals(pull_request, fn)
        assert_that(fn, equal_to(pull_request))
        assert_that(pull_request_url, equal_to("https://github.com/pulls/1"))

    @httpretty.activate
    def test_pull_request_worker(self):
        """Worker pull_request /pulls/1"""
        pull = {
            "title": "Lorem ipsum",
            "url": "https://github.com/pulls/1",
            "commits_url": "https://github.com/pulls/1/commits",
            "statuses_url": "https://github.com/statuses/2",
            "review_comments_url": "https://github.com/pulls/1/comments",
            "head": {
                "sha": "2"
            }
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1",
                               body=json.dumps(pull),
                               content_type="application/json")
        commits = [
            {
                "url": "https://github.com/commits/1",
                "sha": "1",
                "comments_url": "https://github.com/commits/1/comments",
                "commit": {
                    "message": "fix all the bugs!"
                }
            }, {

                "url": "https://github.com/commits/2",
                "sha": "2",
                "comments_url": "https://github.com/commits/2/comments",
                "commit": {
                    "message": "herp derp"
                }
            }
        ]
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1/commits",
                               body=json.dumps(commits),
                               content_type="application/json")
        files = [{
            "filename": "spam/eggs.py",
            "status": "added",
            "raw_url": "https://github.com/raw/2/spam/eggs.py",
            "contents_url": "https://api.github.com/spam/eggs.py?ref=2"
        }, {
            "filename": "spam/herp.html",
            "status": "added",
            "raw_url": "https://github.com/raw/2/spam/herp.html",
            "contents_url": "https://api.github.com/spam/herp.html?ref=2"
        }]
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1/files",
                               status=200,
                               body=json.dumps(files),
                               content_type="application/json")
        foo_py = "if foo == bar:\n  print('derp')\n"
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/raw/2/spam/eggs.py",
                               status=200,
                               body=foo_py,
                               content_type="text/plain")
        herp_html = "<!DOCTYPE html><html><title>Hello!</title></html>"
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/raw/2/spam/herp.html",
                               status=200,
                               body=herp_html,
                               content_type="text/html")
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/commits/1/comments",
                               status=201,
                               body=json.dumps({"id": 1}),
                               content_type="application/json")
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/commits/2/comments",
                               status=201,
                               body=json.dumps({"id": 2}),
                               content_type="application/json")
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/pulls/1/comments",
                               status=201,
                               body=json.dumps({"id": 3}),
                               content_type="application/json")
        status = {"id": 1, "state": "success"}
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/statuses/2",
                               status=201,
                               body=json.dumps(status),
                               content_type="application/json")

        instance_path = tempfile.mkdtemp()
        pull_request("https://github.com/pulls/1",
                     "http://kwalitee.invenio-software.org/status/2",
                     {"ACCESS_TOKEN": "deadbeef",
                      "instance_path": instance_path})

        latest_requests = httpretty.HTTPretty.latest_requests
        # 5x GET pull, commits, 2xfiles, spam/eggs.py
        # 5x POST comments (2 messages + 2 file), status
        assert_that(len(latest_requests), equal_to(10), "5x GET + 5x POST")

        expected_requests = [
            "",
            "",
            "Missing component name",
            "Signature missing",
            "",
            "",
            "",
            "F821 undefined name",
            "I101 copyright is missing",
            "/status/2"
        ]
        for expected, request in zip(expected_requests, latest_requests):
            assert_that(str(request.body), contains_string(expected))

        body = json.loads(httpretty.last_request().body)
        assert_that(httpretty.last_request().headers["authorization"],
                    equal_to(u"token deadbeef"))
        assert_that(body["state"], equal_to("error"))

        filename = os.path.join(instance_path, "status_{0}.txt")
        assert_that(not os.path.exists(filename.format(1)))
        assert_that(os.path.exists(filename.format(2)))

        with open(filename.format(2)) as f:
            data = f.read()
            assert_that(data,
                        contains_string("2: spam/eggs.py:2:3: E111 indentation"
                                        " is not a multiple of four"))

        shutil.rmtree(instance_path)
