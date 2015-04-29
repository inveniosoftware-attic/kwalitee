# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2015 CERN.
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

"""Test excludes option."""

from __future__ import unicode_literals

import os

from kwalitee.kwalitee import check_file, is_file_excluded, get_options

from unittest import TestCase


class TestExcludesOption(TestCase):

    """Test excludes option."""

    def setUp(self):
        """Setup."""
        base_dir = os.path.join(os.path.dirname(__file__), "fixtures",
                                "excludes_option")
        self.legacy_regex_1 = ['(.)+/legacy/(.)+']
        self.legacy_regex_2 = ['(.)+/legacy/(.)+', '(.)+/foo/(.)+']
        self.file_1 = base_dir + '/fuu/bar/foo.py'
        self.file_2 = base_dir + '/foo/bar/beer.py'
        self.file_3 = base_dir + '/legacy/excluded/excluded.py'

    def test_options(self):
        """Check option loading."""
        # test default value
        options = get_options({})
        assert options['excludes'] == []
        # test set excludes
        options = get_options({'EXCLUDES': self.legacy_regex_1})
        assert options['excludes'] == self.legacy_regex_1

    def test_is_file_escluded(self):
        """Check if is_file_escluded() correctly excludes files."""
        assert is_file_excluded(filename=self.file_1,
                                excludes=self.legacy_regex_1) is False
        assert is_file_excluded(filename=self.file_1,
                                excludes=self.legacy_regex_2) is False
        assert is_file_excluded(filename=self.file_2,
                                excludes=self.legacy_regex_1) is False
        assert is_file_excluded(filename=self.file_2,
                                excludes=self.legacy_regex_2) is True
        assert is_file_excluded(filename=self.file_3,
                                excludes=self.legacy_regex_1) is True
        assert is_file_excluded(filename=self.file_3,
                                excludes=self.legacy_regex_2) is True

    def test_check_file(self):
        """Test check_file()."""
        options_1 = get_options({'EXCLUDES': self.legacy_regex_1})
        options_2 = get_options({'EXCLUDES': self.legacy_regex_2})

        assert check_file(filename=self.file_1, **options_1) is not None
        assert check_file(filename=self.file_1, **options_2) is not None
        assert check_file(filename=self.file_2, **options_1) is not None
        assert check_file(filename=self.file_2, **options_2) is None
        assert check_file(filename=self.file_3, **options_1) is None
        assert check_file(filename=self.file_3, **options_2) is None
