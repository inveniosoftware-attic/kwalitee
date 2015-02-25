# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014 CERN.
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

"""Integration tests for the status page.

Legacy view: that will eventually be dropped.
"""

from __future__ import unicode_literals

import os
import shutil
import tempfile
from hamcrest import assert_that, equal_to, contains_string


def test_simple_status(app):
    """GET /status/sha1 displays the associated text file"""
    sha = "deadbeef"
    instance_path = tempfile.mkdtemp()
    app.instance_path = instance_path
    filename = os.path.join(app.instance_path,
                            "status_{0}.txt".format(sha))
    with open(filename, "w+") as f:
        f.write("\n".join(["{0}: Signature missing",
                           "{0}: Needs more reviewers"]).format(sha))

    tester = app.test_client()
    response = tester.get("status/{0}".format(sha))

    assert_that(response.status_code, equal_to(200))
    assert_that(str(response.data), contains_string("Signature missing"))
    assert_that(str(response.data),
                contains_string("Needs more reviewers"))

    shutil.rmtree(instance_path)


def test_missing_status(app):
    """GET /status/sha2 404"""
    sha = "deadbeef"
    instance_path = tempfile.mkdtemp()
    app.instance_path = instance_path

    tester = app.test_client()
    response = tester.get("status/{0}".format(sha))

    assert_that(response.status_code, equal_to(404))
    shutil.rmtree(instance_path)
