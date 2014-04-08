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
##g
## You should have received a copy of the GNU General Public License
## along with Invenio-Kwalitee; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
##
## In applying this licence, CERN does not waive the privileges and immunities
## granted to it by virtue of its status as an Intergovernmental Organization
## or submit itself to any jurisdiction.

from __future__ import absolute_import

import os
import six

from flask.ext.script import Manager

from . import app
from .hooks import pre_commit_hook, prepare_commit_msg_hook, \
    run, post_commit_hook

HOOKS = {
    'pre-commit': pre_commit_hook.__name__,
    'prepare-commit-msg': prepare_commit_msg_hook.__name__,
    'post-commit': post_commit_hook.__name__,
}

manager = Manager(app)
githooks = Manager()


@githooks.option('-f', '--force',
                 help='Overwrite existing hooks', default=False,
                 action='store_true')
def install(force):
    """Install git hooks"""
    ret, git_dir, _ = run('git rev-parse --show-toplevel')
    if ret != 0:
        print("ERROR: Please run from within a GIT repository.")
        return 1
    git_dir = git_dir[0]

    hooks_dir = os.path.join(git_dir, ".git/hooks")

    tpl = app.config['HOOK_TEMPLATE']

    for hook, name in six.iteritems(HOOKS):
        hook_path = os.path.join(hooks_dir, hook)
        if os.path.exists(hook_path) and not force:
            print ("Hook already exists. Skipping %s" % hook_path)
            continue

        with open(hook_path, 'wb') as fh:
            fh.write(six.b(tpl % dict(hook=name)))
        os.chmod(hook_path, 493)  # 0o755


@githooks.command
def uninstall():
    """Uninstall git hooks"""
    ret, git_dir, _ = run('git rev-parse --show-toplevel')
    if ret != 0:
        print("ERROR: Please run from within a GIT repository.")
        return 1
    git_dir = git_dir[0]

    hooks_dir = os.path.join(git_dir, ".git/hooks")

    for hook, name in six.iteritems(HOOKS):
        hook_path = os.path.join(hooks_dir, hook)
        if os.path.exists(hook_path):
            os.remove(hook_path)

manager.add_command('githooks', githooks)


def main():
    manager.run()
