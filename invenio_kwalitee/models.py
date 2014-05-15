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

"""Database models to persist the data over time."""

from __future__ import unicode_literals

from flask import json

from . import db


class Account(db.Model):

    """Github account."""

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.UnicodeText(), unique=True, nullable=False)
    email = db.Column(db.UnicodeText())
    token = db.Column(db.UnicodeText())

    def __init__(self, name, email=None, token=None):
        """Initialize the account."""
        self.name = name
        self.email = email
        self.token = token

    def __repr__(self):
        """String representation of the account."""
        return "<Account ({0.id}, {0.name}, {0.email})>".format(self)

    @classmethod
    def create(cls, name, email=None, token=None):
        """Create and commit and new account."""
        acc = cls(name, email, token)
        db.session.add(acc)
        db.session.commit()
        return acc

    @classmethod
    def find_or_create(cls, name, email=None, token=None):
        """Find or create an account."""
        acc = cls.query.filter_by(name=name).first()
        if not acc:
            return cls.create(name, email, token)
        return acc

    @classmethod
    def update_or_create(cls, name, email=None, token=None):
        """Modify or create an account."""
        acc = cls.query.filter_by(name=name).first()
        if not acc:
            return cls.create(name, email, token)
        else:
            if email and acc.email != email:
                acc.email = email
            if token and acc.token != token:
                acc.token = token
            if db.session.is_modified(acc):
                db.session.add(acc)
                db.session.commit()
            return acc


class Repository(db.Model):

    """Github repository."""

    __table_args__ = db.UniqueConstraint('owner_id', 'name'),

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer(),
                         db.ForeignKey("account.id"),
                         nullable=False)
    name = db.Column(db.UnicodeText(), nullable=False)

    owner = db.relationship("Account",
                            backref=db.backref("repositories",
                                               cascade="all",
                                               order_by=db.asc(name),
                                               lazy="dynamic"))

    @property
    def fullname(self):
        """Get the fullname of the repository."""
        return "{0}/{1}".format(self.owner.name, self.name)

    def __init__(self, owner, name):
        """Initialize the repository."""
        self.owner = owner
        self.name = name

    def __repr__(self):
        """String representation of the repository."""
        return "<Repository ({0}, {1})>".format(self.id, self.fullname)

    @classmethod
    def find_or_create(cls, owner, name):
        """Find or create a repository."""
        repo = cls.query.filter_by(name=name, owner_id=owner.id).first()
        if not repo:
            repo = cls(owner, name)
            db.session.add(repo)
            db.session.commit()
        return repo


class CommitStatus(db.Model):

    """Status of a push."""

    __table_args__ = db.UniqueConstraint('repository_id', 'sha'),

    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer(),
                              db.ForeignKey("repository.id"),
                              nullable=False)
    sha = db.Column(db.UnicodeText(), nullable=False)
    url = db.Column(db.UnicodeText(), nullable=False)
    errors = db.Column(db.Integer(), nullable=False)
    _content = db.Column(db.UnicodeText())

    repository = db.relationship("Repository",
                                 backref=db.backref("commit_statuses",
                                                    cascade="all",
                                                    order_by=db.desc(id),
                                                    lazy="dynamic"))

    def get_content(self):
        """Get the content of the status."""
        return json.loads(self._content)

    def set_content(self, value):
        """Set the content of the status."""
        self.errors = len(value["message"])
        if value["files"] is not None:
            self.errors += len(value["files"])

        self._content = json.dumps(value, ensure_ascii=False)
    content = property(get_content, set_content)

    def __init__(self, repository, sha, url, content=None):
        """Initialize the commit status."""
        self.repository = repository
        self.sha = sha
        self.url = url
        content = content or {"message": [], "files": None}
        self.content = content

    def __repr__(self):
        """String representation of the commit status."""
        return "<CommitStatus ({0.id}, {0.sha})>".format(self)

    @classmethod
    def find_or_create(cls, repository, sha, url):
        """Find or create a commit status."""
        cs = cls.query.filter_by(repository_id=repository.id, sha=sha).first()
        if not cs:
            cs = CommitStatus(repository, sha, url)

        return cs


class BranchStatus(db.Model):

    """Status of a pull request."""

    __table_args__ = db.UniqueConstraint('commit_id', 'name'),

    id = db.Column(db.Integer(), primary_key=True)
    commit_id = db.Column(db.Integer(),
                          db.ForeignKey("commit_status.id"),
                          nullable=False)
    name = db.Column(db.UnicodeText(), nullable=False)
    url = db.Column(db.UnicodeText(), nullable=False)
    errors = db.Column(db.Integer(), nullable=False)
    _content = db.Column(db.UnicodeText())

    commit = db.relationship("CommitStatus",
                             backref=db.backref("branch_statuses",
                                                cascade="all",
                                                order_by=db.desc(id),
                                                lazy="dynamic"))

    def get_content(self):
        """Get the content of the status."""
        return json.loads(self._content)

    def set_content(self, value):
        """Set the content of the status."""
        c = {"commits": [],
             "files": value["files"]}
        self.errors = len(value["files"])
        for commit in value["commits"]:
            if not isinstance(commit, CommitStatus):
                # FIXME potentially unnecessary heavy operation
                commit = CommitStatus.query.filter_by(
                    repository_id=self.commit.repository_id,
                    sha=commit
                ).first()
            self.errors += len(commit.content["message"])
            c["commits"].append(commit.sha)

        self._content = json.dumps(c, ensure_ascii=False)
    content = property(get_content, set_content)

    def __init__(self, commit, name, url, content=None):
        """Initialize a branch status."""
        self.commit = commit
        self.name = name
        self.url = url
        content = content or dict(commits=[], files=[])
        self.content = content

    def __repr__(self):
        """String representation of a branch status."""
        return "<BranchStatus ({0.id}, {0.commit_id}, {0.name})>".format(self)
