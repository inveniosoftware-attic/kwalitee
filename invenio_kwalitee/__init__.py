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
import operator

from flask import (Flask, json, jsonify, make_response, render_template,
                   request, url_for)
from rq import Queue

from .kwalitee import pull_request
from .worker import conn
from .version import __version__


app = Flask(__name__, template_folder="templates", static_folder="static",
            instance_relative_config=True)

# Load default configuration
app.config.from_object("invenio_kwalitee.config")

# Load invenio_kwalitee.cfg from instance folder
app.config.from_pyfile("invenio_kwalitee.cfg", silent=True)
app.config.from_envvar("INVENIO_KWALITEE_CONFIG", silent=True)
app.config["queue"] = Queue(connection=conn)


# Create instance path
try:
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)  # pragma: no cover
except Exception:  # pragma: no cover
    pass


@app.route("/status/<commit_sha>")
def status(commit_sha):
    with app.open_instance_resource(
            "status_{sha}.txt".format(sha=commit_sha), "r") as f:
        status = f.read()
    status = status if len(status) > 0 else commit_sha + ": Everything OK"
    return render_template("status.html", status=status)


@app.route("/", methods=["GET"])
def index():
    key = lambda x: os.path.getctime(os.path.join(app.instance_path, x))
    test = operator.methodcaller("startswith", "status_")
    files = map(lambda x: x[7:-4], filter(test, sorted(
        os.listdir(app.instance_path), key=key, reverse=True)))
    return render_template("index.html", files=files)


@app.route("/payload", methods=["POST"])
def payload():
    q = app.config["queue"]
    try:
        event = None
        if "X-GitHub-Event" in request.headers:
            event = request.headers["X-GitHub-Event"]
        else:
            raise ValueError("No X-GitHub-Event HTTP header found")

        if event == "ping":
            payload = {"message": "pong"}
        elif event == "pull_request":
            data = json.loads(request.data)
            pull_request_url = data["pull_request"]["url"]
            commit_sha = data["pull_request"]["head"]["sha"]
            status_url = url_for("status", commit_sha=commit_sha,
                                 _external=True)
            config = dict(app.config, instance_path=app.instance_path)
            del config["queue"]
            q.enqueue(pull_request, pull_request_url, status_url, config)
            payload = {
                "state": "pending",
                "target_url": status_url,
                "description": "kwalitee is working this commit out"
            }
        else:
            raise ValueError("Event {0} is not supported".format(event))

        return jsonify(payload=payload)
    except Exception as e:
        import traceback
        # Uncomment to help you debug
        #traceback.print_exc()
        return make_response(jsonify(status="failure",
                                     stacktrace=traceback.format_exc(),
                                     exception=str(e)),
                             500)


