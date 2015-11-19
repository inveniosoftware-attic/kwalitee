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

from __future__ import absolute_import, print_function

import os
import sys

import click

from ..hooks import run

HOOKS = {
    "pre-commit",
    "prepare-commit-msg",
    "post-commit",
}
HOOK_PATH = os.path.join(".git", "hooks")

@click.group()
def githooks():
    """Install githooks for kwalitee checks."""


@githooks.command()
@click.option("-f", "--force", is_flag=True,
              help="Overwrite existing hooks", default=False)
def install(force=False):
    """Install git hooks."""
    ret, git_dir, _ = run("git rev-parse --show-toplevel")
    if ret != 0:
        click.echo(
            "ERROR: Please run from within a GIT repository.",
            file=sys.stderr)
        raise click.Abort
    git_dir = git_dir[0]

    hooks_dir = os.path.join(git_dir, HOOK_PATH)

    for hook in HOOKS:
        hook_path = os.path.join(hooks_dir, hook)
        if os.path.exists(hook_path):
            if not force:
                click.echo(
                    "Hook already exists. Skipping {0}".format(hook_path),
                    file=sys.stderr)
                continue
            else:
                os.unlink(hook_path)

        source = os.path.join(sys.prefix, "bin", "kwalitee-" + hook)
        os.symlink(os.path.normpath(source), hook_path)
    return True


@githooks.command()
def uninstall():
    """Uninstall git hooks."""
    ret, git_dir, _ = run("git rev-parse --show-toplevel")
    if ret != 0:
        click.echo(
            "ERROR: Please run from within a GIT repository.",
            file=sys.stderr)
        raise click.Abort
    git_dir = git_dir[0]

    hooks_dir = os.path.join(git_dir, HOOK_PATH)

    for hook in HOOKS:
        hook_path = os.path.join(hooks_dir, hook)
        if os.path.exists(hook_path):
            os.remove(hook_path)
    return True
