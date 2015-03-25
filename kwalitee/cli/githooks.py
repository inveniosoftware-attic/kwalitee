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

"""Command-line tools for the git hooks."""

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys

from flask import current_app as app
from flask_script import Manager

from ..hooks import (pre_commit_hook, prepare_commit_msg_hook, run,
                     post_commit_hook)

HOOKS = {
    "pre-commit": pre_commit_hook.__name__,
    "prepare-commit-msg": prepare_commit_msg_hook.__name__,
    "post-commit": post_commit_hook.__name__,
}
HOOK_PATH = os.path.join(".git", "hooks")

manager = Manager(usage="install githooks for kwalitee checks")


@manager.option("-f", "--force",
                help="Overwrite existing hooks", default=False,
                action="store_true")
def install(force=False):
    """Install git hooks."""
    ret, git_dir, _ = run("git rev-parse --show-toplevel")
    if ret != 0:
        print("ERROR: Please run from within a GIT repository.",
              file=sys.stderr)
        return False
    git_dir = git_dir[0]

    hooks_dir = os.path.join(git_dir, HOOK_PATH)

    tpl = app.config["HOOK_TEMPLATE"]

    for hook, name in HOOKS.items():
        hook_path = os.path.join(hooks_dir, hook)
        if os.path.exists(hook_path) and not force:
            print("Hook already exists. Skipping {0}".format(hook_path),
                  file=sys.stderr)
            continue

        with open(hook_path, "w") as fh:
            fh.write(tpl.format(hook=name))
        os.chmod(hook_path, 0o755)
    return True


@manager.command
def uninstall():
    """Uninstall git hooks."""
    ret, git_dir, _ = run("git rev-parse --show-toplevel")
    if ret != 0:
        print("ERROR: Please run from within a GIT repository.",
              file=sys.stderr)
        return False
    git_dir = git_dir[0]

    hooks_dir = os.path.join(git_dir, HOOK_PATH)

    for hook, name in HOOKS.items():
        hook_path = os.path.join(hooks_dir, hook)
        if os.path.exists(hook_path):
            os.remove(hook_path)
    return True
