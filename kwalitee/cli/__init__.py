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

"""Command line interfaces entrypoints."""


from flask_script import Manager

from . import account, check, githooks, prepare, repository


manager = Manager()

manager.add_command("account", account.manager)
manager.add_command("githooks", githooks.manager)
manager.add_command("prepare", prepare.manager)
manager.add_command("repository", repository.manager)
manager.add_command("check", check.manager)


def main():  # pragma: no cover
    """Running the manager."""
    from .. import create_app
    manager.app = create_app()
    manager.run()
