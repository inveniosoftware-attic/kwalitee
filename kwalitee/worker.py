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

"""Initialize Redis and setups the RQ worker."""

from __future__ import absolute_import

from os import environ
from redis import Redis
from rq import Connection, Queue, Worker

conn = Redis(host=environ.get('REDIS_HOST', 'localhost'))


def init_app(app):
    """Initialize the RQ queue."""
    queue = Queue(connection=conn)
    app.config["queue"] = queue
    return app


if __name__ == "__main__":
    import sys
    import logging

    from .wsgi import application

    with application.app_context():
        if tuple(sys.version_info) < (2, 7):
            logger = logging.getLogger("rq.worker")
            logger.setLevel(logging.DEBUG)
            logger.addHandler(logging.StreamHandler())
        with Connection(conn):
            worker = Worker(list(map(Queue, ('high', 'default', 'low'))))
            worker.work()
