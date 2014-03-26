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
        self.assertEqual(200, response.status_code)
        body = json.loads(response.data)
        self.assertEqual(u"pending", body["payload"]["state"])

        (fn, pull_request_url, status_url, config) = queue.dequeue()
        self.assertEquals(pull_request, fn)
        self.assertEquals(u"https://github.com/pulls/1", pull_request_url)

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
        # 4x GET pull, commits, files, spam/eggs.py
        # 4x POST comments (2 messages + 1 file), status
        self.assertEqual(8, len(latest_requests), "8 requests are expected")

        # Testing some bits of the content of the POST requests
        expected_requests = [
            "Missing component name",
            "Signature missing",
            "F821 undefined name",
            "/status/2"
        ]
        for expected, request in zip(expected_requests, latest_requests[-4:]):
            self.assertIn(expected, str(request.body))

        body = json.loads(httpretty.last_request().body)
        self.assertEqual(u"token deadbeef",
                         httpretty.last_request().headers["Authorization"])
        self.assertEqual(u"error", body["state"])

        filename = os.path.join(instance_path, "status_{0}.txt")
        self.assertFalse(os.path.exists(filename.format(1)),
                         "status 1 file was NOT created")
        self.assertTrue(os.path.exists(filename.format(2)),
                        "status 2 file was created")

        with open(filename.format(2)) as f:
            data = f.read()
            self.assertIn("2: spam/eggs.py:2:3: E111 indentation is not a "
                          "multiple of four",
                          data)

        shutil.rmtree(instance_path)
