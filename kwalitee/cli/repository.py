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

"""Command-line tools for managing repositories."""

from __future__ import absolute_import, print_function, unicode_literals

import sys

from ..models import db, Account, Repository

from flask_script import Manager

manager = Manager(usage="repository management")


def _is_valid_repo(repository):
    """Say whether the repository is valid.

    It must be formed of the account name and repository name.
    """
    if repository.count("/") is not 1:
        print("{0} is not a valid repository "
              "(expected: owner/repository)".format(repository),
              file=sys.stderr)
        return False
    return True


@manager.command
def add(repository):
    """Add a repository to the list of authorized ones."""
    if not _is_valid_repo(repository):
        return 1
    account_name, repository_name = repository.split("/")

    acc = Account.find_or_create(account_name)
    Repository.find_or_create(acc, repository_name)
    print("{0} is now allowed to webhook kwalitee!".format(repository),
          file=sys.stderr)


@manager.command
def remove(repository):
    """Remove a repository from the list of authorized ones."""
    if not _is_valid_repo(repository):
        return 1
    account_name, repository_name = repository.split("/")

    acc = Account.query.filter_by(name=account_name).first()
    if not acc:
        return
    repo = Repository.query.filter_by(name=repository_name,
                                      owner_id=acc.id).first()
    if not repo:
        return

    db.session.delete(repo)
    db.session.commit()


@manager.command
def list():
    """List all the repositories."""
    for acc in Account.query.order_by(db.asc(Account.name)).all():
        for repo in acc.repositories:
            print(repo.fullname)
