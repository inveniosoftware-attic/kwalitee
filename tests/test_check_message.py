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

from __future__ import unicode_literals

from itertools import repeat
from unittest import TestCase

from hamcrest import assert_that, has_item, has_items, has_length, is_not

from kwalitee.kwalitee import check_message


class TestCheckMessage(TestCase):
    """Unit tests of the commit message validation checks"""
    options = dict(components=("search", "utils"),
                   trusted=("john.doe@example.org",),
                   signatures=("Signed-off-by", "Reviewed-by"),
                   commit_msg_labels=(('NEW', 'New'), ('AMENDS', None)),
                   alt_signatures=("Reported-by",))

    def test_no_message(self):
        errors = check_message("", **self.options)
        assert_that(errors,
                    has_items("1: M110 missing component name",
                              "1: M101 signature is missing",
                              "1: M100 needs more reviewers"))

    def test_allow_empty_message(self):
        options = dict(self.options, allow_empty="True")
        errors = check_message("", **options)
        assert_that(errors, has_length(0))

    def test_no_component_name(self):
        errors = check_message("foo bar.", **self.options)
        assert_that(errors,
                    has_items("1: M110 missing component name",
                              "1: M101 signature is missing",
                              "1: M100 needs more reviewers",
                              "1: M191 must not end with a dot '.'"))

    def test_known_component_name(self):
        errors = check_message("utils: foo bar", **self.options)
        assert_that(errors,
                    has_items("1: M101 signature is missing",
                              "1: M100 needs more reviewers"))

    def test_unknonwn_component_name(self):
        errors = check_message("kikoo: lol", **self.options)
        assert_that(errors,
                    has_item("1: M111 unrecognized component name: kikoo"))

    def test_first_line_is_too_long(self):
        message = "".join(repeat("M", 51))
        errors = check_message(message, **self.options)
        assert_that(errors, has_item("1: M190 line is too long (51 > 50)"))

    def test_has_enough_reviewers(self):
        errors = check_message("search: hello\r\n\r\n"
                               "Signed-off-by: a a <a@a.com>\r\n"
                               "Reviewed-by: b b <b@b.com>\r\n"
                               "Reviewed-by: c c <c@c.com>\r\n"
                               "Reported-by: d d <d@d.com>",
                               **self.options)
        assert_that(errors, has_length(0))

    def test_needs_more_reviewers(self):
        errors = check_message("search: hello\r\n\r\n"
                               "Signed-off-by: a a <a@a.com>",
                               **self.options)
        assert_that(errors, has_item("1: M100 needs more reviewers"))

    def test_signature_ends_with_a_dot(self):
        errors = check_message("search: hello\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>.",
                               **self.options)
        assert_that(errors, has_item("3: M191 must not end with a dot '.'"))

    def test_has_a_trusted_developer(self):
        errors = check_message("search: hello\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.options)
        assert_that(errors, has_length(0))

    def test_valid_bullets(self):
        errors = check_message("search: hello\r\n\r\n"
                               "* bullet 1\r\n\r\n"
                               "* bullet 2\r\n\r\n"
                               "* bullet 3\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.options)
        assert_that(errors, has_length(0))

    def test_valid_multiline_bullets(self):
        errors = check_message("search: hello\r\n\r\n"
                               "* bullet 1\r\n"
                               "  lorem ipsum\r\n\r\n"
                               "* bullet 2\r\n"
                               "  dolor sit amet\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.options)
        assert_that(errors, has_length(0))

    def test_line_is_too_long(self):
        # max is 72 total including the identation
        too_long = "".join(list(repeat("M", 70)))
        errors = check_message("search: hello\r\n\r\n"
                               "* {0}\r\n\r\n"
                               "* M{0}\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>"
                               .format(too_long),
                               **self.options)
        assert_that(errors, has_length(1))
        assert_that(errors,
                    has_item("5: M190 line is too long (73 > 72)"))

    def test_missing_empty_line_before_bullet(self):
        errors = check_message("search: hello\r\n"
                               "* bullet 1\r\n\r\n"
                               "* bullet 2\r\n"
                               "* bullet 3\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.options)
        assert_that(errors, has_length(3))
        assert_that(errors,
                    has_items("2: M120 missing empty line before bullet",
                              "5: M120 missing empty line before bullet"))

    def test_using_alternative_bullet_character(self):
        errors = check_message("search: hello\r\n\r\n"
                               "- bullet 1\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.options)
        assert_that(errors,
                    has_item("3: M102 unrecognized bullet/signature"))

    def test_wrong_identation_after_bullet(self):
        errors = check_message("search: hello\r\n\r\n"
                               "* line 1\r\n"
                               "line 2\r\n"
                               " line 3\r\n"
                               "  line 4\r\n"
                               "   line 5\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.options)
        assert_that(errors,
                    has_items("4: M121 indentation of two spaces expected",
                              "5: M121 indentation of two spaces expected",
                              "7: M121 indentation of two spaces expected"))
        assert_that(errors,
                    is_not(has_item("M121: 6: indentation of two spaces "
                                    "expected")))

    def test_signatures_mixed_with_bullets(self):
        errors = check_message("search: hello\r\n\r\n"
                               "* bullet 1\r\n\r\n"
                               "Signed-off-by: a a <a@a.com>\r\n\r\n"
                               "* bullet 2\r\n\r\n"
                               "Reviewed-by: b b <b@b.com>\r\n\r\n"
                               "* bullet 3\r\n\r\n"
                               "Reviewed-by: c c <c@c.com>",
                               **self.options)
        assert_that(errors, has_items(
            "7: M130 no bullets are allowed after signatures",
            "11: M130 no bullets are allowed after signatures"))

    def test_bullet_labels(self):
        errors = check_message("search: hello\r\n\r\n"
                               "* NEW bullet 1\r\n  line 2\r\n\r\n"
                               "* AMENDS deadbeef\r\n\r\n"
                               "* DEADBEEF invalid name\r\n\r\n"
                               "* MISSINGSPACE\r\n\r\n"
                               "Signed-off-by: a a <a@a.com>\r\n\r\n"
                               "Reviewed-by: b b <b@b.com>\r\n\r\n"
                               "Reviewed-by: c c <c@c.com>",
                               **self.options)
        assert_that(errors, has_items(
            "8: M122 unrecognized bullet label: DEADBEEF"))
