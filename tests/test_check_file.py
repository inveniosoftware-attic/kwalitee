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

from __future__ import unicode_literals

import os
import tempfile
from invenio_kwalitee.kwalitee import check_pep8, check_pep257, check_license
from unittest import TestCase
from hamcrest import assert_that, has_length, has_item, is_not


class TestCheckFile(TestCase):

    def setUp(self):
        fixtures = os.path.join(os.path.dirname(__file__), "fixtures", "")
        self.valid = "{0}valid.py.test".format(fixtures)
        self.invalid = "{0}invalid.py.test".format(fixtures)
        self.error = "{0}error.py.test".format(fixtures)
        self.empty = "{0}empty.py.test".format(fixtures)
        self.invalid_license = "{0}invalid_license.py.test".format(fixtures)
        self.valid_license = "{0}valid_license.py.test".format(fixtures)
        self.missing_license = "{0}missing_license.py.test".format(fixtures)
        self.license_html = "{0}license.html.test".format(fixtures)
        self.license_js = "{0}license.js.test".format(fixtures)
        self.license_css = "{0}license.css.test".format(fixtures)


class TestCheckPep8(TestCheckFile):
    """Unit tests of the PEP8 check."""

    def test_valid(self):
        """valid.py is correctly formatted (according to pep8)"""
        errors = check_pep8(self.valid)
        assert_that(errors, has_length(0))

    def test_invalid_file(self):
        """invalid.py has 7 PEP8 violations + 1 from pyFlakes"""
        errors = check_pep8(self.invalid)
        assert_that(errors, has_length(8))

    def test_erroneous_file(self):
        """error.py has 2 pyflakes violations"""
        errors = check_pep8(self.error)
        assert_that(errors, has_length(2))

    def test_ignore(self):
        """ignored PEP8 codes are ignored"""
        errors = check_pep8(self.invalid,
                            ignore=('E111', 'E113', 'E901'))
        assert_that(errors, has_length(0))

    def test_ignore_license(self):
        """ignored PEP8 codes are ignored"""
        errors = check_pep8(self.error, ignore=('E265',))
        assert_that(errors, has_length(2))

    def test_select(self):
        """selected PEP8 codes are selected"""
        errors = check_pep8(self.invalid, select=('E111',))
        assert_that(errors, has_length(3))


class TestCheckPep257(TestCheckFile):
    """Unit tests of the PEP257 checks."""

    def test_valid(self):
        """valid.py is correctly formatted (according to pep257)"""
        print(self.valid)
        errors = check_pep257(self.valid)
        assert_that(errors, has_length(0))

    def test_missing(self):
        """invalid.py has no docstring"""
        errors = check_pep257(self.invalid)
        assert_that(errors, has_item("1: D100 Docstring missing"))

    def test_ignore(self):
        """ignored PEP257 codes are ignored"""
        errors = check_pep257(self.invalid, ignore=('D100'))
        assert_that(errors, has_length(0))

    def test_match(self):
        """test only the file that are matched by the regex"""
        errors = check_pep257("test_bar.py", match="(?!test_).*\.py")
        assert_that(errors, has_length(0))

    def test_match_dir(self):
        """test only the directories that are matched by the regex"""
        errors = check_pep257("foo/.hidden/spam/eggs/bar.py",
                              match_dir="[^\.].*")
        assert_that(errors, has_length(0))

    def test_match_absolute_dir(self):
        fp, path = tempfile.mkstemp(text=True)
        os.write(fp, "# -*- coding: utf-8 -*-\n".encode("ascii"))
        os.close(fp)

        errors = check_pep257(path, match_dir="[^\.].*")
        assert_that(errors, has_length(1))

        os.unlink(path)


class TestCheckLicense(TestCheckFile):
    """Unit tests of the license validation."""

    def test_license(self):
        """valid_license has a well formatted license."""
        errors = check_license(self.valid_license, year=2014)
        assert_that(errors, has_length(0))

    def test_missing(self):
        """missing_license has only the copyright"""
        errors = check_license(self.missing_license)
        assert_that(errors, has_item("13: I100 license is missing"))

    def test_license_jinja(self):
        """license.html has a well formatted license."""
        errors = check_license(self.license_html, year=2014)
        assert_that(errors, has_length(0))

    def test_license_js(self):
        """license.js has a well formatted license."""
        errors = check_license(self.license_js, year=2014, python_style=False)
        assert_that(errors, has_length(0))

    def test_license_css(self):
        """license.css has a well formatted license."""
        errors = check_license(self.license_css, year=2014, python_style=False)
        assert_that(errors, has_length(0))

    def test_empty(self):
        """empty files like __init__ are skipped"""
        errors = check_license(self.empty)
        assert_that(errors, has_length(0))

    def test_unicode_license(self):
        """invalid_license uses unicode copyright and multiline years.

        Where copyright is ©.
        """
        errors = check_license(self.invalid_license, year=2014)
        assert_that(errors, is_not(has_item("25: I101 copyright is missing")))

    def test_no_license(self):
        """license is missing"""
        errors = check_license(self.valid)
        assert_that(errors, has_item("25: I101 copyright is missing"))

    def test_no_copyright(self):
        """copyright is missing"""
        errors = check_license(self.valid)
        assert_that(errors, has_item("25: I101 copyright is missing"))

    def test_outdated_license(self):
        """valid_license has an outdated license."""
        errors = check_license(self.valid_license, year=2015)
        assert_that(errors, has_item("4: I102 copyright year is outdated, "
                                     "expected 2015 but got 2014"))

    def test_doesnt_look_like_gnu_gpl(self):
        """invalid_license doesn't look like the GNU GPL"""
        errors = check_license(self.invalid_license, year=2014)
        assert_that(errors, has_item("25: I103 license is not GNU GPLv2"))
