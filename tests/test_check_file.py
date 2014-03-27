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
        self.error = "{0}error.py.test".format(self.fixtures)

    def test_valid_file(self):
        """valid.py has is correct"""
        errors = check_file(self.valid)
        self.assertEquals(0, len(errors), errors)

    def test_invalid_file(self):
        """invalid.py has 7 PEP8 violations + 1 from pyFlakes"""
        errors = check_file(self.invalid)
        print(errors)
        self.assertEquals(8, len(errors), errors)

    def test_erroneous_file(self):
        """error.py has 2 pyflakes violations"""
        errors = check_file(self.error)
        self.assertEquals(2, len(errors), errors)

    def test_pep8_ignore(self):
        """ignored PEP8 codes are ignored"""
        errors = check_file(self.invalid, pep8_ignore=('E111', 'E113', 'E901'))
        self.assertEquals(0, len(errors), errors)

    def test_pep8_select(self):
        """selected PEP8 codes are selected"""
        errors = check_file(self.invalid, pep8_select=('E111',))
        self.assertEquals(3, len(errors), errors)
