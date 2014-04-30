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
from datetime import datetime
from unittest import TestCase
from invenio_kwalitee import app, pull_request
from hamcrest import (assert_that, equal_to, contains_string, has_length,
                      has_item, has_items, is_not)


GPL = """
## This file is part of Invenio-Kwalitee
## Copyright (C) {0} CERN.
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
"""


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
            "issue_url": "https://github.com/issues/1",
            "head": {
                "sha": "2"
            }
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1",
                               body=json.dumps(pull),
                               content_type="application/json")
        issue = {
            "url": "https://github.com/issues/1",
            "labels_url": "https://github.com/issues/1/labels{/name}",
            "id": "42",
            "number": "1",
            "labels": [{"name": "foo"},
                       {"name": "in_work"}],
            "state": "open"
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/issues/1",
                               body=json.dumps(issue),
                               content_type="application/json")
        labels = [{
            "url": "https://github.com/labels/foo",
            "name": "foo",
            "color": "000000"
        }, {
            "url": "https://github.com/labels/in_review",
            "name": "in_review",
            "color": "ff0000"
        }]
        httpretty.register_uri(httpretty.PUT,
                               "https://github.com/issues/1/labels",
                               status=200,
                               body=json.dumps(labels),
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
                               body=json.dumps(files),
                               content_type="application/json")
        eggs_py = "if foo == bar:\n  print('derp')\n"
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/raw/2/spam/eggs.py",
                               body=eggs_py,
                               content_type="text/plain")
        herp_html = "<!DOCTYPE html><html><title>Hello!</title></html>"
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/raw/2/spam/herp.html",
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
        # 6x GET pull, issue, commits, 2xfiles, spam/eggs.py
        # 6x POST comments (2 messages + 2 file), label, status
        assert_that(len(latest_requests), equal_to(12), "6x GET + 6x POST")

        expected_requests = [
            "",
            "",
            "",
            "missing component name",
            "signature is missing",
            "",
            "",
            "",
            "F821 undefined name",
            "I101 copyright is missing",
            "/status/2",
            "in_review"
        ]
        for expected, request in zip(expected_requests, latest_requests):
            assert_that(str(request.body), contains_string(expected))

        body = json.loads(latest_requests[-2].body)
        assert_that(latest_requests[-2].headers["authorization"],
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

    @httpretty.activate
    def test_wip_pull_request_worker(self):
        """Worker pull_request /pulls/1 is work in progress"""
        pull = {
            "title": "WIP Lorem ipsum",
            "url": "https://github.com/pulls/1",
            "commits_url": "https://github.com/pulls/1/commits",
            "statuses_url": "https://github.com/statuses/2",
            "review_comments_url": "https://github.com/pulls/1/comments",
            "issue_url": "https://github.com/issues/1",
            "head": {
                "sha": "2"
            }
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1",
                               body=json.dumps(pull),
                               content_type="application/json")
        issue = {
            "url": "https://github.com/issues/1",
            "labels_url": "https://github.com/issues/1/labels{/name}",
            "id": "42",
            "number": "1",
            "labels": [{"name": "foo"},
                       {"name": "in_integration"}],
            "state": "open"
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/issues/1",
                               body=json.dumps(issue),
                               content_type="application/json")
        labels = [{
            "url": "https://github.com/labels/foo",
            "name": "foo",
            "color": "000000"
        }, {
            "url": "https://github.com/labels/in_review",
            "name": "in_review",
            "color": "ff0000"
        }]
        httpretty.register_uri(httpretty.PUT,
                               "https://github.com/issues/1/labels",
                               status=200,
                               body=json.dumps(issue),
                               content_type="application/json")
        instance_path = tempfile.mkdtemp()
        pull_request("https://github.com/pulls/1",
                     "http://kwalitee.invenio-software.org/status/2",
                     {"ACCESS_TOKEN": "deadbeef",
                      "instance_path": instance_path})

        latest_requests = httpretty.HTTPretty.latest_requests
        # 2x GET pull, issue
        # 1x POST labels
        assert_that(len(latest_requests), equal_to(3), "2x GET + 1x POST")

        expected_requests = [
            "",
            "",
            "in_work"
        ]
        for expected, request in zip(expected_requests, latest_requests):
            assert_that(str(request.body), contains_string(expected))

        labels = json.loads(latest_requests[-1].body)
        assert_that(labels, has_items("in_work", "foo"))
        assert_that(labels, is_not(has_item("in_review")))

        filename = os.path.join(instance_path, "status_{0}.txt")
        assert_that(not os.path.exists(filename.format(1)))
        assert_that(not os.path.exists(filename.format(2)))

        shutil.rmtree(instance_path)

    @httpretty.activate
    def test_pep8_pull_request_worker(self):
        """Worker pull_request /pulls/1 with pep8 errors"""
        pull = {
            "title": "Lorem ipsum",
            "url": "https://github.com/pulls/1",
            "commits_url": "https://github.com/pulls/1/commits",
            "statuses_url": "https://github.com/statuses/1",
            "issue_url": "https://github.com/issues/1",
            "review_comments_url": "https://github.com/pulls/1/comments",
            "head": {
                "sha": "1"
            }
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1",
                               body=json.dumps(pull),
                               content_type="application/json")
        issue = {
            "url": "https://github.com/issues/1",
            "labels_url": "https://github.com/issues/1/labels{/name}",
            "id": "42",
            "number": "1",
            "labels": [{"name": "foo"},
                       {"name": "in_work"}],
            "state": "open"
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/issues/1",
                               body=json.dumps(issue),
                               content_type="application/json")
        labels = [{
            "url": "https://github.com/labels/foo",
            "name": "foo",
            "color": "000000"
        }, {
            "url": "https://github.com/labels/in_review",
            "name": "in_review",
            "color": "ff0000"
        }]
        httpretty.register_uri(httpretty.PUT,
                               "https://github.com/issues/1/labels",
                               status=200,
                               body=json.dumps(labels),
                               content_type="application/json")
        commits = [
            {
                "url": "https://github.com/commits/1",
                "sha": "2",
                "comments_url": "https://github.com/commits/1/comments",
                "commit": {
                    "message": "herp: derp\r\n\r\nSigned-off-by: John Doe "
                               "<john.doe@example.org>"
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
            "contents_url": "https://api.github.com/spam/eggs.py?ref=1"
        }]
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1/files",
                               body=json.dumps(files),
                               content_type="application/json")
        eggs_py = "if foo == bar:\n  print('derp')\n"
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/raw/2/spam/eggs.py",
                               body=eggs_py,
                               content_type="text/plain")
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/commits/1/comments",
                               status=201,
                               body=json.dumps({"id": 1}),
                               content_type="application/json")
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/pulls/1/comments",
                               status=201,
                               body=json.dumps({"id": 3}),
                               content_type="application/json")
        status = {"id": 1, "state": "success"}
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/statuses/1",
                               status=201,
                               body=json.dumps(status),
                               content_type="application/json")

        instance_path = tempfile.mkdtemp()
        pull_request("https://github.com/pulls/1",
                     "http://kwalitee.invenio-software.org/status/1",
                     {"ACCESS_TOKEN": "deadbeef",
                      "TRUSTED_DEVELOPERS": ["john.doe@example.org"],
                      "COMPONENTS": ["herp"],
                      "SIGNATURES": ["Signed-off-by"],
                      "instance_path": instance_path})

        latest_requests = httpretty.HTTPretty.latest_requests
        # 5x GET pull, issue, commits, 1 file, spam/eggs.py
        # 3x POST comments (1xfile), status, label
        assert_that(len(latest_requests), equal_to(8), "5x GET + 3x POST")

        expected_requests = [
            "",
            "",
            "",
            "",
            "",
            "F821 undefined name",
            "/status/1",
            "in_review",
        ]
        for expected, request in zip(expected_requests, latest_requests):
            assert_that(str(request.body), contains_string(expected))

        body = json.loads(latest_requests[-2].body)
        assert_that(latest_requests[-2].headers["authorization"],
                    equal_to(u"token deadbeef"))
        assert_that(body["state"], equal_to("error"))

        filename = os.path.join(instance_path, "status_{0}.txt")
        assert_that(os.path.exists(filename.format(1)))

        with open(filename.format(1)) as f:
            data = f.read()
            assert_that(data,
                        contains_string("1: spam/eggs.py:2:3: E111 indentation"
                                        " is not a multiple of four"))

        shutil.rmtree(instance_path)

    @httpretty.activate
    def test_okay_pull_request_worker(self):
        """Worker pull_request /pulls/1 with pep8 errors"""
        pull = {
            "title": "Lorem ipsum",
            "url": "https://github.com/pulls/1",
            "commits_url": "https://github.com/pulls/1/commits",
            "statuses_url": "https://github.com/statuses/1",
            "issue_url": "https://github.com/issues/1",
            "review_comments_url": "https://github.com/pulls/1/comments",
            "head": {
                "sha": "1"
            }
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1",
                               body=json.dumps(pull),
                               content_type="application/json")
        issue = {
            "url": "https://github.com/issues/1",
            "labels_url": "https://github.com/issues/1/labels{/name}",
            "id": "42",
            "number": "1",
            "labels": [{"name": "foo"},
                       {"name": "in_work"}],
            "state": "open"
        }
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/issues/1",
                               body=json.dumps(issue),
                               content_type="application/json")
        labels = [{
            "url": "https://github.com/labels/foo",
            "name": "foo",
            "color": "000000"
        }, {
            "url": "https://github.com/labels/in_review",
            "name": "in_review",
            "color": "ff0000"
        }]
        httpretty.register_uri(httpretty.PUT,
                               "https://github.com/issues/1/labels",
                               status=200,
                               body=json.dumps(labels),
                               content_type="application/json")
        commits = [
            {
                "url": "https://github.com/commits/1",
                "sha": "1",
                "comments_url": "https://github.com/commits/1/comments",
                "commit": {
                    "message": "herp: derp\r\n\r\nSigned-off-by: John Doe "
                               "<john.doe@example.org>"
                }
            }
        ]
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1/commits",
                               body=json.dumps(commits),
                               content_type="application/json")
        files = [{
            "filename": "eggs/__init__.py",
            "status": "added",
            "raw_url": "https://github.com/raw/1/eggs/__init__.py",
            "contents_url": "https://api.github.com/eggs/__init__.py?ref=1"
        }]
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/pulls/1/files",
                               body=json.dumps(files),
                               content_type="application/json")
        init_py = GPL.format(datetime.now().year)
        httpretty.register_uri(httpretty.GET,
                               "https://github.com/raw/1/eggs/__init__.py",
                               body=init_py,
                               content_type="text/plain")
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/commits/1/comments",
                               status=201,
                               body=json.dumps({"id": 1}),
                               content_type="application/json")
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/pulls/1/comments",
                               status=201,
                               body=json.dumps({"id": 3}),
                               content_type="application/json")
        status = {"id": 1, "state": "success"}
        httpretty.register_uri(httpretty.POST,
                               "https://github.com/statuses/1",
                               status=201,
                               body=json.dumps(status),
                               content_type="application/json")

        instance_path = tempfile.mkdtemp()
        pull_request("https://github.com/pulls/1",
                     "http://kwalitee.invenio-software.org/status/1",
                     {"ACCESS_TOKEN": "deadbeef",
                      "TRUSTED_DEVELOPERS": ["john.doe@example.org"],
                      "COMPONENTS": ["herp"],
                      "SIGNATURES": ["Signed-off-by"],
                      "IGNORE": ["E265", "D100"],
                      "instance_path": instance_path})

        latest_requests = httpretty.HTTPretty.latest_requests
        # 5x GET pull, issue, commits, 1 file, spam/eggs.py
        # 2x POST status, label
        assert_that(len(latest_requests), equal_to(7), "5x GET + 2x POST")

        expected_requests = [
            "",
            "",
            "",
            "",
            "",
            "/status/1",
            "in_integration",
        ]
        for expected, request in zip(expected_requests, latest_requests):
            assert_that(str(request.body), contains_string(expected))

        body = json.loads(latest_requests[-2].body)
        assert_that(latest_requests[-2].headers["authorization"],
                    equal_to(u"token deadbeef"))
        assert_that(body["state"], equal_to("success"))

        filename = os.path.join(instance_path, "status_{0}.txt")
        assert_that(os.path.exists(filename.format(1)))

        with open(filename.format(1)) as f:
            data = f.read()
            assert_that(data, has_length(0))

        shutil.rmtree(instance_path)
