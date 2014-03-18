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

from invenio_kwalitee.kwalitee import check_message
from itertools import repeat
from unittest import TestCase


class TestCheckMessage(TestCase):
    """Unit tests of the commit message validation checks"""
    kwargs = dict(components=("search", "utils"),
                  trusted=("john.doe@example.org",),
                  signatures=("Signed-off-by", "Reviewed-by"))

    def test_no_message(self):
        errors = check_message("", **self.kwargs)
        self.assertIn(u"Missing component name", errors)
        self.assertIn(u"Signature missing", errors)

    def test_known_component_name(self):
        errors = check_message("kikoo lol", **self.kwargs)
        self.assertIn(u"Missing component name", errors)
        self.assertIn(u"Signature missing", errors)

    def test_unknonwn_component_name(self):
        errors = check_message("kikoo: lol", **self.kwargs)
        self.assertIn(u'Unknown "kikoo" component name', errors)

    def test_first_line_is_too_long(self):
        message = "".join(repeat("M", 51))
        errors = check_message(message, **self.kwargs)
        self.assertIn(u"First line is too long", errors)

    def test_has_enough_reviewers(self):
        errors = check_message("search: hello\r\n\r\n"
                               "Signed-off-by: a a <a@a.com>\r\n"
                               "Reviewed-by: b b <b@b.com>\r\n"
                               "Reviewed-by: c c <c@c.com>",
                               **self.kwargs)
        self.assertEquals(0, len(errors), errors)

    def test_needs_more_reviewers(self):
        errors = check_message("search: hello\r\n\r\n"
                               "Signed-off-by: a a <a@a.com>",
                               **self.kwargs)
        self.assertIn(u"Needs more reviewers", errors)

    def test_has_a_trusted_developer(self):
        errors = check_message("search: hello\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.kwargs)
        self.assertEqual(0, len(errors), errors)

    def test_valid_bullets(self):
        errors = check_message("search: hello\r\n\r\n"
                               "* bullet 1\r\n\r\n"
                               "* bullet 2\r\n\r\n"
                               "* bullet 3\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.kwargs)
        self.assertEquals(0, len(errors), errors)

    def test_line_is_too_long(self):
        # max is 72 total including the identation
        too_long = "".join(list(repeat("M", 70)))
        errors = check_message("search: hello\r\n\r\n"
                               "* {0}\r\n\r\n"
                               "* M{0}\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>"
                               .format(too_long),
                               **self.kwargs)
        self.assertNotIn(u"Line 3 is too long (72 > 72)", errors)
        self.assertIn(u"Line 5 is too long (73 > 72)", errors)

    def test_missing_empty_line_before_bullet(self):
        errors = check_message("search: hello\r\n"
                               "* bullet 1\r\n\r\n"
                               "* bullet 2\r\n"
                               "* bullet 3\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.kwargs)
        self.assertIn(u"Missing empty line before line 1", errors)
        self.assertNotIn(u"Missing empty line before line 3", errors)
        self.assertIn(u"Missing empty line before line 4", errors)

    def test_using_alternative_bullet_character(self):
        errors = check_message("search: hello\r\n\r\n"
                               "- bullet 1\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.kwargs)
        self.assertIn(u'Unrecognized bullet/signature on line 2: "- bullet 1"',
                      errors)

    def test_wrong_identation_after_bullet(self):
        errors = check_message("search: hello\r\n\r\n"
                               "* line 1\r\n"
                               "line 2\r\n"
                               " line 3\r\n"
                               "  line 4\r\n"
                               "   line 5\r\n\r\n"
                               "Signed-off-by: a a <john.doe@example.org>",
                               **self.kwargs)
        self.assertIn(u"Wrong indentation on line 4", errors)
        self.assertIn(u"Wrong indentation on line 5", errors)
        self.assertNotIn(u"Wrong indentation on line 6", errors)
        self.assertIn(u"Wrong indentation on line 7", errors)

    def test_signatures_mixed_with_bullets(self):
        errors = check_message("search: hello\r\n\r\n"
                               "* bullet 1\r\n\r\n"
                               "Signed-off-by: a a <a@a.com>\r\n\r\n"
                               "* bullet 2\r\n\r\n"
                               "Reviewed-by: b b <b@b.com>\r\n\r\n"
                               "* bullet 3\r\n\r\n"
                               "Reviewed-by: c c <c@c.com>",
                               **self.kwargs)
        self.assertIn(u"No bullets are allowed after signatures on line 6",
                      errors)
        self.assertIn(u"No bullets are allowed after signatures on line 10",
                      errors)
