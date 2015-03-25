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
from datetime import datetime
from kwalitee.models import BranchStatus, CommitStatus
from kwalitee.tasks import pull_request
from hamcrest import (assert_that, equal_to, contains_string, has_length,
                      has_item, has_items, is_not, greater_than)

from utils import MyQueue, GPL


def test_pull_request(app, owner, repository):
    """POST /payload (pull_request) performs the checks"""
    httpretty.reset()
    queue = MyQueue()
    # Replace the default Redis queue
    app.config["queue"] = queue

    pull_request_event = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "title": "Lorem ipsum",
            "url": "https://api.github.com/pulls/1",
            "html_url": "https://github.com/pulls/1",
            "commits_url": "https://api.github.com/pulls/1/commits",
            "statuses_url": "https://api.github.com/pulls/1/statuses",
            "head": {
                "sha": "2",
                "label": "spam:wip/my-branch",
                "ref": "wip/my-branch"
            }
        },
        "repository": {
            "name": "test",
            "owner": {
                "login": "invenio"
            }
        }
    }

    commits = [
        {
            "url": "https://api.github.com/commits/1",
            "sha": "1",
            "html_url": "https://github.com/commits/1",
            "comments_url": "https://api.github.com/commits/1/comments",
            "commit": {
                "message": "herp derp"
            }
        }, {
            "url": "https://api.github.com/commits/2",
            "sha": "2",
            "html_url": "https://github.com/commits/2",
            "comments_url": "https://api.github.com/commits/2/comments",
            "commit": {
                "message": "fix all the bugs!"
            }
        }
    ]
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1/commits",
                           body=json.dumps(commits),
                           content_type="application/json")

    tester = app.test_client()
    httpretty.enable()
    response = tester.post("/payload", content_type="application/json",
                           headers=(("X-GitHub-Event", "pull_request"),
                                    ("X-GitHub-Delivery", "1")),
                           data=json.dumps(pull_request_event))
    httpretty.disable()

    assert_that(response.status_code, equal_to(200))
    body = json.loads(response.data)
    assert_that(body["payload"]["state"], equal_to("pending"))

    (fn, bs_id, pull_request_url, status_url, config) = queue.dequeue()
    assert_that(fn, equal_to(pull_request))
    assert_that(bs_id, greater_than(0))
    assert_that(pull_request_url,
                equal_to("https://api.github.com/pulls/1"))

    cs = CommitStatus.query.filter_by(repository_id=repository.id,
                                      sha="1").first()
    assert_that(cs)
    assert_that(cs.state, equal_to("pending"))

    cs = CommitStatus.query.filter_by(repository_id=repository.id,
                                      sha="2").first()
    assert_that(cs)
    assert_that(cs.state, equal_to("pending"))

    bs = BranchStatus.query.filter_by(commit_id=cs.id,
                                      name="spam:wip/my-branch").first()
    assert_that(bs)
    assert_that(bs.is_pending())
    assert_that(bs.state, equal_to("pending"))


def test_invalid_pull_request_action(app, owner, repository):
    """POST /payload (pull_request) performs the action checks"""
    httpretty.reset()
    queue = MyQueue()
    # Replace the default Redis queue
    app.config["queue"] = queue

    pull_request_event = {
        "action": "labeled",
        "number": 1,
        "pull_request": {
            "title": "Lorem ipsum",
            "url": "https://api.github.com/pulls/1",
            "html_url": "https://github.com/pulls/1",
            "commits_url": "https://api.github.com/pulls/1/commits",
            "statuses_url": "https://api.github.com/pulls/1/statuses",
            "head": {
                "sha": "2",
                "label": "spam:wip/my-branch",
                "ref": "wip/my-branch"
            }
        },
        "repository": {
            "name": "test",
            "owner": {
                "login": "invenio"
            }
        }
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1/commits",
                           body=json.dumps([]),
                           content_type="application/json")

    tester = app.test_client()
    httpretty.enable()

    response = tester.post("/payload", content_type="application/json",
                           headers=(("X-GitHub-Event", "pull_request"),
                                    ("X-GitHub-Delivery", "1")),
                           data=json.dumps(pull_request_event))
    httpretty.disable()

    assert_that(response.status_code, equal_to(500))


def test_pull_request_task(app, owner, repository, session):
    """Task pull_request /pulls/1"""
    httpretty.reset()
    pull = {
        "title": "Lorem ipsum",
        "url": "https://api.github.com/pulls/1",
        "html_url": "https://github.com/pulls/1",
        "commits_url": "https://api.github.com/pulls/1/commits",
        "statuses_url": "https://api.github.com/statuses/2",
        "review_comments_url": "https://api.github.com/pulls/1/comments",
        "issue_url": "https://api.github.com/issues/1",
        "head": {
            "sha": "2",
            "label": "test:my-branch"
        },
        "base": {
            "repo": {
                "full_name": "kwalitee/test"
            },
            "ref": "testref"
        },
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1",
                           body=json.dumps(pull),
                           content_type="application/json")

    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/repos/kwalitee/test/"
                           "contents/.kwalitee.yml?ref=testref",
                           status=404)

    issue = {
        "url": "https://api.github.com/issues/1",
        "html_url": "https://github.com/issues/1",
        "labels_url": "https://api.github.com/issues/1/labels{/name}",
        "id": "42",
        "number": "1",
        "labels": [{"name": "foo"},
                   {"name": "in_work"}],
        "state": "open"
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/issues/1",
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
                           "https://api.github.com/issues/1/labels",
                           status=200,
                           body=json.dumps(labels),
                           content_type="application/json")
    commits = [
        {
            "url": "https://api.github.com/commits/1",
            "sha": "1",
            "html_url": "https://github.com/commits/1",
            "comments_url": "https://api.github.com/commits/1/comments",
            "commit": {
                "message": "fix all the bugs!"
            }
        }, {

            "url": "https://api.github.com/commits/2",
            "sha": "2",
            "html_url": "https://github.com/commits/2",
            "comments_url": "https://api.github.com/commits/1/comments",
            "commit": {
                "message": "herp derp"
            }
        }
    ]
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1/commits",
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
                           "https://api.github.com/pulls/1/files",
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
                           "https://api.github.com/commits/1/comments",
                           status=201,
                           body=json.dumps({"id": 1}),
                           content_type="application/json")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/commits/2/comments",
                           status=201,
                           body=json.dumps({"id": 2}),
                           content_type="application/json")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/pulls/1/comments",
                           status=201,
                           body=json.dumps({"id": 3}),
                           content_type="application/json")
    status = {"id": 1, "state": "success"}
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/statuses/2",
                           status=201,
                           body=json.dumps(status),
                           content_type="application/json")

    css = []
    for commit in commits:
        css.append(CommitStatus.find_or_create(repository,
                                               commit["sha"],
                                               commit["url"]))

    bs = BranchStatus(css[-1],
                      "test:my-branch",
                      "https://github.com/pulls/1",
                      {"commits": css, "files": None})
    session.add(bs)
    session.commit()

    assert_that(css[0].is_pending())
    assert_that(css[1].is_pending())
    assert_that(bs.is_pending())

    httpretty.enable()
    pull_request(bs.id,
                 "https://api.github.com/pulls/1",
                 "http://kwalitee.invenio-software.org/status/2",
                 {"repository": repository.id})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    # 7x GET pull, .kwalitee.yml, issue, commits, files, spam/eggs.py,
    # spam/herp.html
    # 5x POST comments (1 message + 2 files), status
    # 1x PUT labels
    assert_that(len(latest_requests), equal_to(12), "7x GET + 4x POST + 1 PUT")

    expected_requests = [
        "",
        "",
        "",
        "missing component name",  # "signature is missing",
        "",
        "",
        "",
        "F821 undefined name",
        "L101 copyright is missing",
        "/status/2",
        "",
        "in_review"
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.body), contains_string(expected))

    body = json.loads(latest_requests[-3].body)
    assert_that(latest_requests[-3].headers["authorization"],
                equal_to("token {0}".format(owner.token)))
    assert_that(body["state"], equal_to("error"))

    cs = CommitStatus.query.filter_by(repository_id=repository.id).all()

    assert_that(cs, has_length(2))
    assert_that(cs[0].content["message"],
                has_item("1: M110 missing component name"))
    assert_that(cs[1].content["message"],
                has_item("1: M100 needs more reviewers"))

    bs = BranchStatus.query.filter_by(commit_id=cs[1].id,
                                      name="test:my-branch").first()

    assert_that(bs)
    assert_that(bs.content["commits"], has_items("1", "2"))
    assert_that(bs.errors, equal_to(12))
    assert_that(
        bs.content["files"]["spam/eggs.py"]["errors"],
        has_item("2:3: E111 indentation is not a multiple of four"))


def test_wip_pull_request_task(app, owner, repository, session):
    """Task pull_request /pulls/1 is work in progress"""
    httpretty.reset()
    pull = {
        "title": "WIP Lorem ipsum",
        "url": "https://api.github.com/pulls/1",
        "html_url": "https://github.com/pulls/1",
        "commits_url": "https://api.github.com/pulls/1/commits",
        "statuses_url": "https://api.github.com/statuses/1",
        "review_comments_url": "https://api.github.com/pulls/1/comments",
        "issue_url": "https://api.github.com/issues/1",
        "head": {
            "sha": "2",
            "label": "test:my-branch"
        },
        "base": {
            "repo": {
                "full_name": "kwalitee/test"
            },
            "ref": "testref"
        },
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1",
                           body=json.dumps(pull),
                           content_type="application/json")

    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/repos/kwalitee/test/"
                           "contents/.kwalitee.yml?ref=testref",
                           status=404)

    commits = [
        {
            "url": "https://api.github.com/commits/1",
            "sha": "1",
            "html_url": "https://github.com/commits/1",
            "comments_url": "https://api.github.com/commits/1/comments",
            "commit": {
                "message": "fix all the bugs!"
            }
        }, {

            "url": "https://api.github.com/commits/2",
            "sha": "2",
            "html_url": "https://github.com/commits/2",
            "comments_url": "https://api.github.com/commits/2/comments",
            "commit": {
                "message": "herp derp"
            }
        }
    ]
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1/commits",
                           body=json.dumps(commits),
                           content_type="application/json")
    issue = {
        "url": "https://api.github.com/issues/1",
        "html_url": "https://github.com/issues/1",
        "labels_url": "https://api.github.com/issues/1/labels{/name}",
        "id": "42",
        "number": "1",
        "labels": [{"name": "foo"},
                   {"name": "in_integration"}],
        "state": "open"
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/issues/1",
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
                           "https://api.github.com/issues/1/labels",
                           status=200,
                           body=json.dumps(issue),
                           content_type="application/json")

    css = []
    for commit in commits:
        css.append(CommitStatus.find_or_create(repository,
                                               commit["sha"],
                                               commit["url"]))
    bs = BranchStatus(css[-1],
                      "test:my-branch",
                      "https://github.com/pulls/1",
                      {"commits": css, "files": None})
    session.add(bs)
    session.commit()
    assert_that(bs.is_pending())

    httpretty.enable()
    pull_request(bs.id,
                 "https://api.github.com/pulls/1",
                 "http://kwalitee.invenio-software.org/status/1",
                 {"repository": repository.id})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    # 4x GET pull, .kwalitee.yml, commits, issue
    # 1x POST labels
    assert_that(len(latest_requests), equal_to(5), "4x GET + 1x POST")

    expected_requests = [
        "",
        "",
        "",
        "",
        "in_work"
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.body), contains_string(expected))

    labels = json.loads(latest_requests[-1].body)
    assert_that(labels, has_items("in_work", "foo"))
    assert_that(labels, is_not(has_item("in_review")))


def test_pep8_pull_request_task(app, owner, repository, session):
    """Task pull_request /pulls/1 with pep8 errors"""
    httpretty.reset()
    pull = {
        "title": "Lorem ipsum",
        "url": "https://api.github.com/pulls/1",
        "html_url": "https://github.com/pulls/1",
        "commits_url": "https://api.github.com/pulls/1/commits",
        "statuses_url": "https://api.github.com/statuses/1",
        "issue_url": "https://api.github.com/issues/1",
        "review_comments_url": "https://api.github.com/pulls/1/comments",
        "head": {
            "sha": "1",
            "label": "test:my-branch"
        },
        "base": {
            "repo": {
                "full_name": "kwalitee/test"
            },
            "ref": "testref"
        },
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1",
                           body=json.dumps(pull),
                           content_type="application/json")

    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/repos/kwalitee/test/"
                           "contents/.kwalitee.yml?ref=testref",
                           status=404)

    issue = {
        "url": "https://api.github.com/issues/1",
        "html_url": "https://github.com/issues/1",
        "labels_url": "https://api.github.com/issues/1/labels{/name}",
        "id": "42",
        "number": "1",
        "labels": [{"name": "foo"},
                   {"name": "in_work"}],
        "state": "open"
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/issues/1",
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
                           "https://api.github.com/issues/1/labels",
                           status=200,
                           body=json.dumps(labels),
                           content_type="application/json")
    commits = [
        {
            "url": "https://api.github.com/commits/2",
            "sha": "2",
            "html_url": "https://github.com/commits/2",
            "comments_url": "https://api.github.com/commits/1/comments",
            "commit": {
                "message": "herp: derp\r\n\r\nSigned-off-by: John Doe "
                           "<john.doe@example.org>"
            }
        }
    ]
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1/commits",
                           body=json.dumps(commits),
                           content_type="application/json")
    files = [{
        "filename": "spam/eggs.py",
        "status": "added",
        "raw_url": "https://github.com/raw/2/spam/eggs.py",
        "contents_url": "https://api.github.com/spam/eggs.py?ref=1"
    }]
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1/files",
                           body=json.dumps(files),
                           content_type="application/json")
    eggs_py = "if foo == bar:\n  print('derp')\n"
    httpretty.register_uri(httpretty.GET,
                           "https://github.com/raw/2/spam/eggs.py",
                           body=eggs_py,
                           content_type="text/plain")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/commits/1/comments",
                           status=201,
                           body=json.dumps({"id": 1}),
                           content_type="application/json")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/pulls/1/comments",
                           status=201,
                           body=json.dumps({"id": 3}),
                           content_type="application/json")
    status = {"id": 1, "state": "success"}
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/statuses/1",
                           status=201,
                           body=json.dumps(status),
                           content_type="application/json")

    cs = []
    for commit in commits:
        cs.append(CommitStatus.find_or_create(repository,
                                              commit["sha"],
                                              commit["url"]))

    bs = BranchStatus(cs[0],
                      "test:my-branch",
                      "https://github.com/pulls/1",
                      {"commits": cs, "files": None})
    session.add(bs)
    session.commit()
    assert_that(bs.is_pending())

    httpretty.enable()
    pull_request(bs.id,
                 "https://api.github.com/pulls/1",
                 "http://kwalitee.invenio-software.org/status/1",
                 {"TRUSTED_DEVELOPERS": ["john.doe@example.org"],
                  "COMPONENTS": ["herp"],
                  "SIGNATURES": ["Signed-off-by"]})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    # 6x GET pull, .kwalitee.yml, issue, commits, 1 file, spam/eggs.py
    # 3x POST comments (1xfile), status, label
    assert_that(len(latest_requests), equal_to(9), "6x GET + 3x POST")

    expected_requests = [
        "",
        "",
        "",
        "",
        "",
        "D100 Missing docstring in public module",
        "/status/1",
        "",
        "in_review",
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.body), contains_string(expected))

    body = json.loads(latest_requests[-3].body)
    assert_that(latest_requests[-3].headers["authorization"],
                equal_to("token {0}".format(owner.token)))
    assert_that(body["state"], equal_to("error"))

    cs = CommitStatus.query.filter_by(repository_id=repository.id,
                                      ).all()
    assert_that(cs, has_length(1))
    assert_that(cs[0].content["files"] is None)
    assert_that(cs[0].sha, equal_to("2"))
    assert_that(cs[0].is_pending(), equal_to(False))

    bs = BranchStatus.query.filter_by(commit_id=cs[0].id,
                                      name="test:my-branch").first()

    assert_that(bs)
    assert_that(bs.errors, equal_to(5))
    assert_that(
        bs.content["files"]["spam/eggs.py"]["errors"],
        has_item("2:3: E111 indentation is not a multiple of four"))


def test_okay_pull_request_task(app, owner, repository, session):
    """Task pull_request /pulls/1 with pep8 errors"""
    httpretty.reset()
    pull = {
        "title": "Lorem ipsum",
        "url": "https://api.github.com/pulls/1",
        "html_url": "https://github.com/pulls/1",
        "commits_url": "https://api.github.com/pulls/1/commits",
        "statuses_url": "https://api.github.com/statuses/1",
        "issue_url": "https://api.github.com/issues/1",
        "review_comments_url": "https://api.github.com/pulls/1/comments",
        "head": {
            "sha": "1",
            "label": "test:my-branch"
        },
        "base": {
            "repo": {
                "full_name": "kwalitee/test"
            },
            "ref": "testref"
        },
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1",
                           body=json.dumps(pull),
                           content_type="application/json")

    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/repos/kwalitee/test/"
                           "contents/.kwalitee.yml?ref=testref",
                           status=404)

    issue = {
        "url": "https://apigithub.com/issues/1",
        "html_url": "https://github.com/issues/1",
        "labels_url": "https://api.github.com/issues/1/labels{/name}",
        "id": "42",
        "number": "1",
        "labels": [{"name": "foo"},
                   {"name": "in_work"}],
        "state": "open"
    }
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/issues/1",
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
                           "https://api.github.com/issues/1/labels",
                           status=200,
                           body=json.dumps(labels),
                           content_type="application/json")
    commits = [
        {
            "url": "https://api.github.com/commits/1",
            "sha": "1",
            "html_url": "https://github.com/commits/1",
            "comments_url": "https://api.github.com/commits/1/comments",
            "commit": {
                "message": "herp: derp\r\n\r\nSigned-off-by: John Doe "
                           "<john.doe@example.org>"
            }
        }
    ]
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1/commits",
                           body=json.dumps(commits),
                           content_type="application/json")
    files = [{
        "filename": "eggs/__init__.py",
        "status": "added",
        "raw_url": "https://github.com/raw/1/eggs/__init__.py",
        "contents_url": "https://api.github.com/eggs/__init__.py?ref=1"
    }]
    httpretty.register_uri(httpretty.GET,
                           "https://api.github.com/pulls/1/files",
                           body=json.dumps(files),
                           content_type="application/json")
    init_py = GPL.format(datetime.now().year, '#')
    httpretty.register_uri(httpretty.GET,
                           "https://github.com/raw/1/eggs/__init__.py",
                           body=init_py,
                           content_type="text/plain")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/commits/1/comments",
                           status=201,
                           body=json.dumps({"id": 1}),
                           content_type="application/json")
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/pulls/1/comments",
                           status=201,
                           body=json.dumps({"id": 3}),
                           content_type="application/json")
    status = {"id": 1, "state": "success"}
    httpretty.register_uri(httpretty.POST,
                           "https://api.github.com/statuses/1",
                           status=201,
                           body=json.dumps(status),
                           content_type="application/json")

    cs = []
    for commit in commits:
        cs.append(CommitStatus.find_or_create(repository,
                                              commit["sha"],
                                              commit["url"]))
    bs = BranchStatus(cs[-1],
                      "test:my-branch",
                      "http://github.com/pulls/1",
                      {"commits": cs, "files": None})
    session.add(bs)
    session.commit()

    httpretty.enable()
    pull_request(bs.id,
                 "https://api.github.com/pulls/1",
                 "http://kwalitee.invenio-software.org/status/1",
                 {"TRUSTED_DEVELOPERS": ["john.doe@example.org"],
                  "COMPONENTS": ["herp"],
                  "SIGNATURES": ["Signed-off-by"],
                  "IGNORE": ["E265", "D100"]})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    # 5x GET pull, .kwalitee.yml, issue, commits, 1 file, spam/eggs.py
    # 2x POST status, label
    assert_that(len(latest_requests), equal_to(8), "6x GET + 2x POST")

    expected_requests = [
        "",
        "",
        "",
        "",
        "",
        "/status/1",
        "",
        "in_integration",
    ]
    for expected, request in zip(expected_requests, latest_requests):
        assert_that(str(request.body), contains_string(expected))

    body = json.loads(latest_requests[-3].body)
    assert_that(latest_requests[-3].headers["authorization"],
                equal_to("token {0}".format(owner.token)))
    assert_that(body["state"], equal_to("success"))

    cs = CommitStatus.query.filter_by(repository_id=repository.id).all()
    assert_that(cs, has_length(1))
    assert_that(cs[0].content["files"] is None)
    assert_that(cs[0].is_pending(), equal_to(False))

    bs = BranchStatus.query.filter_by(commit_id=cs[0].id,
                                      name="test:my-branch").first()

    assert_that(bs.errors, equal_to(0))
    assert_that(bs.content["commits"], has_length(1))
    assert_that(bs.content["files"]["eggs/__init__.py"]["errors"],
                has_length(0))


def test_known_pull_request_task(app, owner, repository, session):
    """Task pull_request /pulls/1 that already exists."""
    httpretty.reset()
    cs1 = CommitStatus(repository,
                       "1",
                       "https://github.com/pulls/1",
                       {"message": [], "files": {}})
    cs2 = CommitStatus(repository,
                       "2",
                       "https://github.com/pulls/2",
                       {"message": [], "files": {}})
    session.add(cs1)
    session.add(cs2)
    session.commit()

    bs = BranchStatus(cs2,
                      "test:my-branch",
                      "https://github.com/pulls/1",
                      {"commits": [cs1, cs2], "files": {}})
    session.add(bs)
    session.commit()
    assert_that(bs.is_pending(), equal_to(False))

    httpretty.enable()
    pull_request(bs.id,
                 "https://api.github.com/pulls/1",
                 "http://kwalitee.invenio-software.org/status/2",
                 {"ACCESS_TOKEN": "deadbeef"})
    httpretty.disable()

    latest_requests = httpretty.HTTPretty.latest_requests
    assert_that(len(latest_requests), equal_to(0),
                "No requests are expected")
