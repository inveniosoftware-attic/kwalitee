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

"""Invenio Kwalitee Flask application and git hooks."""

from __future__ import unicode_literals

import os

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from rq import Queue
from werkzeug.routing import BaseConverter

from .worker import conn


__docformat__ = "restructuredtext en"
__version__ = "0.2.0a.20140604"
__all__ = ("app", "db", "CommitStatus", "BranchStatus", "Repository",
           "Account")

app = Flask(__name__, template_folder="templates", static_folder="static",
            instance_relative_config=True)

# Load default configuration
app.config.from_object("invenio_kwalitee.config")

# Load invenio_kwalitee.cfg from instance folder
app.config.from_pyfile("invenio_kwalitee.cfg", silent=True)
app.config.from_envvar("INVENIO_KWALITEE_CONFIG", silent=True)
app.config["queue"] = Queue(connection=conn)

database = os.path.join(app.instance_path,
                        app.config.get("DATABASE_NAME", "database.db"))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{0}".format(database)
db = SQLAlchemy(app)

# Create instance path
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

# Create db
# the models are here so the db.create_all knows about them.
from .models import CommitStatus, BranchStatus, Repository, Account
if not os.path.exists(database):
    db.create_all()


# Routing
class ShaConverter(BaseConverter):

    """Werkzeug routing converter for sha-1 (truncated or full)."""

    regex = r'(?!/)(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{7})'
    weight = 150


app.url_map.converters['sha'] = ShaConverter

from . import views
app.add_url_rule("/", "index", views.index, methods=["GET"])
app.add_url_rule("/<account>/", "account", views.account, methods=["GET"])
app.add_url_rule("/<account>/<repository>/", "repository", views.repository,
                 methods=["GET"])
app.add_url_rule("/<account>/<repository>/commits/<sha:sha>/", "commit",
                 views.commit, methods=["GET"])
app.add_url_rule("/<account>/<repository>/branches/<sha:sha>/<path:branch>",
                 "branch_status", views.branch_status, methods=["GET"])
app.add_url_rule("/<account>/<repository>/branches/<path:branch>", "branch",
                 views.branch, methods=["GET"])
app.add_url_rule("/payload", "payload", views.payload, methods=["POST"])
# legacy
app.add_url_rule("/status/<sha>", "status", views.status, methods=["GET"])
