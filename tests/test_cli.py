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
import shutil
import tempfile
from unittest import TestCase


class CliTest(TestCase):
    def test_install_hook(self):
        """GET / displays some recent statuses"""
        test_path = tempfile.mkdtemp()
        notest_path = tempfile.mkdtemp()
        os.system("cd %s && git init" % test_path)
        os.system("cd %s && touch .git/hooks/pre-commit" % test_path)

        os.chdir(test_path)
        from invenio_kwalitee.cli import install, uninstall
        install(False)

        for f in ['pre-commit', 'prepare-commit-msg', 'post-commit', ]:
            assert os.path.exists(os.path.join(test_path, '.git/hooks/%s' % f))

        uninstall()

        for f in ['pre-commit', 'prepare-commit-msg', 'post-commit', ]:
            assert not os.path.exists(os.path.join(
                test_path, '.git/hooks/%s' % f)
            )

        # Do write in non git repository
        os.chdir(notest_path)
        install(True)
        uninstall()

        for f in ['pre-commit', 'prepare-commit-msg', 'post-commit', ]:
            assert not os.path.exists(
                os.path.join(notest_path, '.git/hooks/%s' % f)
            )

        shutil.rmtree(test_path)
        shutil.rmtree(notest_path)

    def test_main(self):
        from invenio_kwalitee.cli import main
        self.assertRaises(
            SystemExit,
            main
        )
