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
from invenio_kwalitee.kwalitee import check_file
from unittest import TestCase


class TestCheckFile(TestCase):
    """Unit tests of the file validation checks"""

    def setUp(self):
        self.fixtures = os.path.join(os.path.dirname(__file__), "fixtures", "")
        self.valid = "{0}valid.py.test".format(self.fixtures)
        self.invalid = "{0}invalid.py.test".format(self.fixtures)

    def test_valid_file(self):
        errors = check_file(self.valid)
        self.assertEquals(0, len(errors), errors)

    def test_invalid_file(self):
        errors = check_file(self.invalid)
        self.assertEquals(7, len(errors), errors)

    def test_pep8_ignore(self):
        errors = check_file(self.invalid, pep8_ignore=('E111', 'E113'))
        self.assertEquals(0, len(errors), errors)

    def test_pep8_select(self):
        errors = check_file(self.invalid, pep8_select=('E111',))
        self.assertEquals(3, len(errors), errors)
