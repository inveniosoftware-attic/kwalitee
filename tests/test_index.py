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
from unittest import TestCase
from invenio_kwalitee import app


class IndexTest(TestCase):
    """Integration tests for the homepage"""
    def test_simple_status(self):
        """GET / displays some recent statuses"""
        filenames = []
        for sha in range(10):
            filename = os.path.join(app.instance_path,
                                    "status_{0}.txt".format(sha))
            with open(filename, "w+") as f:
                f.write("\n".join(["{0}: Signature missing",
                                   "{0}: Needs more reviewers"]).format(sha))
            filenames.append(filename)

        tester = app.test_client(self)
        response = tester.get("/")

        self.assertEquals(200, response.status_code)
        for sha in range(10):
            self.assertRegexpMatches(response.data, r"/status/{0}".format(sha))

        for filename in filenames:
            os.unlink(filename)
