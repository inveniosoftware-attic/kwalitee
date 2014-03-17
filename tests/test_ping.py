from flask import json
from unittest import TestCase
from invenio_kwalitee import app


class PingTest(TestCase):
    def test_ping(self):
        """Ping should be silently ignored by kwalitee."""
        tester = app.test_client(self)
        response = tester.post("/payload", content_type="application/json",
                               headers=(("X-GitHub-Event", "ping"),
                                        ("X-GitHub-Delivery", "1")),
                               data=json.dumps({"hook_id": 1,
                                                "zen": "Responsive is better "
                                                       "than fast."}))
        self.assertEqual(200, response.status_code)
