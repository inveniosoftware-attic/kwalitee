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
#g
# You should have received a copy of the GNU General Public License
# along with kwalitee; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Command-line tools for managing accounts."""

from __future__ import absolute_import, print_function, unicode_literals

import sys

from ..models import db, Account

from flask_script import Manager

manager = Manager(usage="repository management")


@manager.command
@manager.option('-m', '--email', dest="email", required=False)
@manager.option('-t', '--token', dest="token", required=False)
def add(account, email=None, token=None):
    """Add/modify an account."""
    acc = Account.update_or_create(account, email, token)

    print("Welcome (back) {0.name}!".format(acc), file=sys.stderr)


@manager.command
def remove(account):
    """Remove an account (and its repositories)."""
    acc = Account.query.filter_by(name=account).first()
    if not acc:
        return

    db.session.delete(acc)
    db.session.commit()


@manager.command
def list():
    """List all the repositories."""
    for acc in Account.query.order_by(db.asc(Account.name)).all():
        if acc.email:
            print("{acc.name} <{acc.email}>".format(acc=acc))
        else:
            print(acc.name)
