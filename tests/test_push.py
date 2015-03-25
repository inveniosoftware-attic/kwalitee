# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014, 2015 CERN.
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

"""Integration tests for the pull_request event."""

from __future__ import absolute_import, unicode_literals

import httpretty

from flask import json
from kwalitee.models import CommitStatus, Repository
from kwalitee.tasks import push
from hamcrest import (assert_that, equal_to, contains_string, has_length,
                      has_item)

from utils import MyQueue


def test_push(app, repository):
    """POST /payload (push) performs the checks"""
    queue = MyQueue()
    # Replace the default Redis queue
    app.config["queue"] = queue

    push_event = {
        "commits": [{
            "id": "1",
            "url": "https://github.com/commits/1"
        }, {
            "id": "2",
            "url": "https://github.com/commits/2"
        }],
        "repository": {
            "name": "test",
            "owner": {
                "name": "invenio"
            }
        }
    }

    tester = app.test_client()
    response = tester.post("/payload", content_type="application/json",
                           headers=(("X-GitHub-Event", "push"),
                                    ("X-GitHub-Delivery", "1")),
                           data=json.dumps(push_event))

    assert_that(response.status_code, equal_to(200))
    body = json.loads(response.data)
    assert_that(body["payload"]["state"], equal_to("pending"))

    cs = CommitStatus.query.filter_by(repository_id=repository.id,
                                      sha="1").first()

    (fn, commit_id, commit_url, status_url, config) = queue.dequeue()
    assert_that(fn, equal_to(push))
    assert_that(commit_id, equal_to(cs.id))
    assert_that(commit_url, equal_to("https://api.github.com"
                                     "/repos/invenio/test/commits/1"))
    assert_that(status_url, contains_string("/invenio/test/commits/1"))

    cs = CommitStatus.query.filter_by(repository_id=repository.id,
                                      sha="2").first()

    (fn, commit_id, commit_url, status_url, config) = queue.dequeue()
    assert_that(fn, equal_to(push))
    assert_that(commit_id, equal_to(cs.id))
    assert_that(commit_url, equal_to("https://api.github.com"
                                     "/repos/invenio/test/commits/2"))
    assert_that(status_url, contains_string("/invenio/test/commits/2"))


def test_push_with_auto_create(app, repository):
    """POST /payload (push) performs the checks"""
    queue = MyQueue()
    # Replace the default Redis queue
    config = dict(app.config)
    app.config["queue"] = queue
    app.config["AUTO_CREATE"] = True

    push_event = {
        "commits": [{
            "id": "1",
            "url": "https://github.com/commits/1"
        }],
        "repository": {
            "name": "doe",
            "owner": {
                "name": "john"
            }
        }
    }

    tester = app.test_client()
    response = tester.post("/payload", content_type="application/json",
                           headers=(("X-GitHub-Event", "push"),
                                    ("X-GitHub-Delivery", "1")),
                           data=json.dumps(push_event))

    assert_that(response.status_code, equal_to(200))
    body = json.loads(response.data)
    assert_that(body["payload"]["state"], equal_to("pending"))

    repo = Repository.query.filter_by(name="doe").first()
    assert_that(repo)
    assert_that(repo.owner.name, equal_to("john"))
    app.config = config


def test_push_to_unknown_repository(app):
    """POST /payload (push) with unknown repository should fails."""
    queue = MyQueue()
    config = dict(app.config)
    app.config["queue"] = queue

    push_event = {
        "commits": [{
            "id": "1",
            "url": "https://github.com/commits/1"
        }],
        "repository": {
            "name": "eggs",
            "owner": {
                "name": "spam"
            }
        }
    }

    tester = app.test_client()
    response = tester.post("/payload", content_type="application/json",
                           headers=(("X-GitHub-Event", "push"),
                                    ("X-GitHub-Delivery", "1")),
                           data=json.dumps(push_event))

    assert_that(response.status_code, equal_to(200))
    body = json.loads(response.data)
    assert_that(body["payload"]["state"], equal_to("error"))
    assert_that(body["payload"]["description"],
                contains_string("spam/eggs"))
    assert_that(body["payload"]["context"],
                equal_to(app.config.get("CONTEXT")))

    app.config = config


def test_push_valid_commit(app, repository):
    """Worker push /commits/1 is valid"""
    httpretty.reset()
    commit = {
        "sha": 1,
        "url": "https://api.github.com/commits/1",
        "html_url": "https://github.com/commits/1",
        "comments_url": "https://api.github.com/commits/1/comments",
        "commit": {
            "message": "comp: that\n\nBy: John Doe <john.doe@example.org>",
        },
        "files": [{
            "filename": "spam/__init__.py",
            "status": "added",
            "raw_url": "https://github.com/raw/1/spam/__init__.py"
        }, {
            "filename": "spam/deleted_files.py",
            "status": "removed",
            "raw_url": "https://github.com/raw/1/spam/deleted_files.py"
        }]
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/commits/1",
                           body=json.dumps(commit),
                           content_type="application/json")
    init_py = '"""Test module."""\n'
    httpretty.register_uri(httpretty.GET,
                           "https://github.com/raw/1/spam/__init__.py",
                           body=init_py,
                           content_type="text/plain")
    status = {"id": 1, "state": "success"}
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/statuses/1",
                           status=201,
                           body=json.dumps(status),
                           content_type="application/json")

    cs = CommitStatus.find_or_create(repository,
                                     commit["sha"],
                                     commit["url"])
    assert_that(cs.is_pending())

    httpretty.enable()
    push(cs.id,
         "https://api.github.com/commits/1",
         "https://api.github.com/statuses/1",
         {"COMPONENTS": ["comp"],
          "SIGNATURES": ["By"],
          "TRUSTED_DEVELOPERS": ["john.doe@example.org"],
          "CHECK_LICENSE": False,
          "repository": repository.id})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    assert_that(len(latest_requests), equal_to(3), "2x GET, 1x POST")

    expected_requests = [
        "",
        "",
        "success"
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.parsed_body), contains_string(expected))

    cs = CommitStatus.query.filter_by(repository_id=repository.id,
                                      sha=commit["sha"]).first()
    assert_that(cs)
    assert_that(cs.state, equal_to("success"))
    assert_that(cs.errors, equal_to(0))
    assert_that(cs.content["files"]["spam/__init__.py"]["errors"],
                has_length(0))


def test_push_wip_commit(app, repository):
    """Worker push /commits/1 has wip as a component and is ignored"""
    httpretty.reset()
    commit = {
        "sha": 1,
        "url": "https://api.github.com/commits/1",
        "html_url": "https://github.com/commits/1",
        "comments_url": "https://api.github.com/commits/1/comments",
        "commit": {
            "message": "wip: herp derp\n\nBy: John Doe <john.doe@example.org>",
        },
        "files": [{
            "filename": "spam/__init__.py",
            "status": "added",
            "raw_url": "https://github.com/raw/1/spam/__init__.py"
        }]
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/commits/1",
                           body=json.dumps(commit),
                           content_type="application/json")
    status = {"id": 1, "state": "success"}
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/statuses/1",
                           status=201,
                           body=json.dumps(status),
                           content_type="application/json")

    cs = CommitStatus.find_or_create(repository,
                                     commit["sha"],
                                     commit["url"])
    assert_that(cs.is_pending())

    httpretty.enable()
    push(cs.id,
         "https://api.github.com/commits/1",
         "https://api.github.com/statuses/1",
         {"COMPONENTS": ["comp"],
          "SIGNATURES": ["By"],
          "TRUSTED_DEVELOPERS": ["john.doe@example.org"],
          "CHECK_LICENSE": False,
          "repository": repository.id})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    assert_that(len(latest_requests), equal_to(2), "1x GET, 1x POST")

    expected_requests = [
        "",
        "success"
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.parsed_body), contains_string(expected))

    cs = CommitStatus.query.filter_by(repository_id=repository.id,
                                      sha=commit["sha"]).first()
    assert_that(cs)
    assert_that(cs.state, equal_to("success"))
    assert_that(cs.errors, equal_to(0))


def test_push_broken_commit_message(app, repository):
    """Worker push /commits/1 is invalid (message)"""
    httpretty.reset()
    commit = {
        "sha": 1,
        "url": "https://api.github.com/commits/1",
        "html_url": "https://github.com/commits/1",
        "comments_url": "https://api.github.com/commits/1/comments",
        "commit": {
            "message": "Fix all the bugs!"
        },
        "files": [{
            "filename": "spam/eggs.py",
            "status": "modified",
            "raw_url": "https://github.com/raw/1/spam/eggs.py"
        }]
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/commits/1",
                           body=json.dumps(commit),
                           content_type="application/json")
    eggs_py = '"""Eggs are boiled."""\n'
    httpretty.register_uri(httpretty.GET,
                           "https://github.com/raw/1/spam/eggs.py",
                           body=eggs_py,
                           content_type="text/plain")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/commits/1/comments",
                           status=201,
                           body=json.dumps({"id": 1}),
                           content_type="application/json")
    status = {"id": 1, "state": "success"}
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/statuses/1",
                           status=201,
                           body=json.dumps(status),
                           content_type="application/json")

    cs = CommitStatus.find_or_create(repository,
                                     commit["sha"],
                                     commit["url"])
    assert_that(cs.is_pending())

    httpretty.enable()
    push(cs.id,
         "https://api.github.com/commits/1",
         "https://api.github.com/statuses/1",
         {"CHECK_LICENSE": False,
          "repository": repository.id})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    assert_that(len(latest_requests), equal_to(4), "2x GET, 2x POST")

    expected_requests = [
        "",
        "needs more reviewers",
        "",
        "error"
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.parsed_body),
                    contains_string(expected))


def test_push_broken_files(repository):
    """Worker push /commits/1 is invalid (files)"""
    httpretty.reset()
    commit = {
        "sha": 1,
        "url": "https://api.github.com/commits/1",
        "html_url": "https://github.com/commits/1",
        "comments_url": "https://api.github.com/commits/1/comments",
        "commit": {
            "message": "comp: bob\n\nBy: John <john.doe@example.org>"
        },
        "files": [{
            "filename": "spam/eggs.py",
            "status": "modified",
            "raw_url": "https://github.com/raw/1/spam/eggs.py"
        }]
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/commits/1",
                           body=json.dumps(commit),
                           content_type="application/json")
    eggs_py = "if foo == bar:\n  print('derp')\n"
    httpretty.register_uri(httpretty.GET,
                           "https://github.com/raw/1/spam/eggs.py",
                           body=eggs_py,
                           content_type="text/plain")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/commits/1/comments",
                           status=201,
                           body=json.dumps({"id": 1}),
                           content_type="application/json")
    status = {"id": 1, "state": "success"}
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/statuses/1",
                           status=201,
                           body=json.dumps(status),
                           content_type="application/json")

    cs = CommitStatus.find_or_create(repository,
                                     commit["sha"],
                                     commit["url"])
    assert_that(cs.is_pending())

    httpretty.enable()
    push(cs.id,
         "https://api.github.com/commits/1",
         "https://api.github.com/statuses/1",
         {"COMPONENTS": ["comp"],
          "SIGNATURES": ["By"],
          "TRUSTED_DEVELOPERS": ["john.doe@example.org"],
          "repository": repository.id})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    assert_that(len(latest_requests), equal_to(4), "2x GET, 2x POST")

    expected_requests = [
        "",
        "",
        "F821 undefined name 'foo'",
        "error"
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.parsed_body),
                    contains_string(expected))


def test_push_known_commit(repository, session):
    """Worker push /commits/1 is not rechecked if known"""
    httpretty.reset()
    commit = {
        "sha": 1,
        "url": "https://api.github.com/commits/1",
        "html_url": "https://github.com/commits/1",
        "comments_url": "https://api.github.com/commits/1/comments",
        "commit": {
            "message": "Fix all the bugs!"
        },
        "files": [{
            "filename": "spam/eggs.py",
            "status": "modified",
            "raw_url": "https://github.com/raw/1/spam/eggs.py"
        }]
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/commits/1",
                           body=json.dumps(commit),
                           content_type="application/json")

    cs = CommitStatus(repository,
                      "1",
                      "https://github.com/commits/1",
                      {"message": ["error 1", "error 2"], "files": {}})
    session.add(cs)
    session.commit()
    assert_that(cs.is_pending(), equal_to(False))

    httpretty.enable()
    body = push(cs.id,
                "https://api.github.com/commits/1",
                "https://api.github.com/statuses/1",
                {"repository": repository.id})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    assert_that(len(latest_requests), equal_to(1), "1x GET")

    assert_that(body["description"],
                contains_string("[error] 2 errors"))


def test_push_half_known_commit(repository, session):
    """Worker push /commits/1 checks the files if none"""
    httpretty.reset()
    commit = {
        "sha": "1",
        "url": "https://api.github.com/commits/1",
        "html_url": "https://github.com/commits/1",
        "comments_url": "https://api.github.com/commits/1/comments",
        "commit": {
            "message": "Fix all the bugs!"
        },
        "files": [{
            "filename": "spam/eggs.py",
            "status": "modified",
            "raw_url": "https://github.com/raw/1/spam/eggs.py"
        }]
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/commits/1",
                           body=json.dumps(commit),
                           content_type="application/json")
    eggs_py = "if foo == bar:\n  print('derp')\n"
    httpretty.register_uri(httpretty.GET,
                           "https://github.com/raw/1/spam/eggs.py",
                           body=eggs_py,
                           content_type="text/plain")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/commits/1/comments",
                           status=201,
                           body=json.dumps({"id": 1}),
                           content_type="application/json")
    status = {"id": 1, "state": "success"}
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/statuses/1",
                           status=201,
                           body=json.dumps(status),
                           content_type="application/json")

    cs = CommitStatus(repository,
                      "1",
                      "https://github.com/commits/1",
                      {"message": [], "files": None})
    session.add(cs)
    session.commit()
    assert_that(cs.is_pending(), equal_to(False))

    httpretty.enable()
    push(cs.id,
         "https://api.github.com/commits/1",
         "https://api.github.com/statuses/1",
         {"repository": repository.id})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    assert_that(len(latest_requests), equal_to(4), "2x GET, 2x POST")

    expected_requests = [
        "",
        "",
        "F821 undefined name 'foo'",
        "error"
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.parsed_body),
                    contains_string(expected))

    cs = CommitStatus.query.filter_by(id=cs.id).first()
    assert_that(cs)
    assert_that(cs.is_pending(), equal_to(False))
    assert_that(cs.content["files"]["spam/eggs.py"]["errors"],
                has_item("1: D100 Missing docstring in public module"))
