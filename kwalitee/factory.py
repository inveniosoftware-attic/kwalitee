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

"""kwalitee factory for Flask application."""


from __future__ import unicode_literals

import os

from flask import Flask, Config
from flask_sqlalchemy import SQLAlchemy
from werkzeug.routing import BaseConverter

class ShaConverter(BaseConverter):

    """Werkzeug routing converter for sha-1 (truncated or full)."""

    regex = r'(?!/)(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{7})'
    weight = 150


def create_app(name=None, config=None):
    """Create the Flask application."""
    name = 'kwalitee' if name is None else name
    app = Flask(name, template_folder="templates", static_folder="static",
                instance_relative_config=True,
                instance_path=os.environ.get("KWALITEE_INSTANCE_PATH"))

    # Load default configuration
    app.config.from_object("kwalitee.config")

    # Load kwalitee.cfg from instance folder
    app.config.from_pyfile("kwalitee.cfg", silent=True)
    app.config.from_envvar("KWALITEE_CONFIG", silent=True)
    app.config.update(config or {})

    # Create instance path
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    # Setting up the database
    from .import models
    models.init_app(app)

    # Setting up RQ
    from . import worker
    worker.init_app(app)

    # Setting up the views
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

    if app.debug:
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    return app
