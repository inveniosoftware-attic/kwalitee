import httpretty
from flask import json
from unittest import TestCase
from invenio_kwalitee import app


class PullRequestTest(TestCase):
    @httpretty.activate
    def test_pull_request(self):
        """Pull request should do the checks..."""
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
        body = json.loads(httpretty.last_request().body)
        self.assertEqual(200, response.status_code)
        self.assertEqual(u"error", body["state"])
