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

"""Git hooks."""

from __future__ import print_function, unicode_literals

import os
import re
import shutil
import sys

from codecs import open
from subprocess import PIPE, Popen
from tempfile import mkdtemp

import yaml

from .kwalitee import SUPPORTED_FILES, check_file, check_message, get_options


def _get_files_modified():
    """Get the list of modified files that are Python or Jinja2."""
    cmd = "git diff-index --cached --name-only --diff-filter=ACMRTUXB HEAD"
    _, files_modified, _ = run(cmd)

    extensions = [re.escape(ext) for ext in list(SUPPORTED_FILES) + [".rst"]]
    test = "(?:{0})$".format("|".join(extensions))
    return list(filter(lambda f: re.search(test, f), files_modified))


def _get_git_author():
    """Return the git author from the git variables."""
    _, stdout, _ = run("git var GIT_AUTHOR_IDENT")

    git_author = stdout[0]
    return git_author[:git_author.find(">") + 1]


def _get_component(filename, default="global"):
    """Get component name from filename."""
    if hasattr(filename, "decode"):
        filename = filename.decode()
    parts = filename.split(os.path.sep)

    if len(parts) >= 3:
        if parts[1] in "modules legacy ext".split():
            return parts[2]
    if len(parts) >= 2:
        if parts[1] in "base celery utils".split():
            return parts[1]
    if len(parts) >= 1:
        if parts[0] in "grunt docs".split():
            return parts[0]
    return default


def _get_components(files):
    """Compile the components list from the given files."""
    return tuple(set(_get_component(f) for f in files))


def _prepare_commit_msg(tmp_file, author, files_modified=None, template=None):
    """Prepare the commit message in tmp_file.

    It will build the commit message prefilling the component line, as well
    as the signature using the git author and the modified files.

    The file remains untouched if it is not empty.
    """
    files_modified = files_modified or []
    template = template or "{component}:\n\nSigned-off-by: {author}\n{extra}"
    if hasattr(template, "decode"):
        template = template.decode()

    with open(tmp_file, "r", "utf-8") as fh:
        contents = fh.readlines()
        msg = filter(lambda x: not (x.startswith("#") or x.isspace()),
                     contents)
        if len(list(msg)):
            return

    component = "unknown"
    components = _get_components(files_modified)

    if len(components) == 1:
        component = components[0]
    elif len(components) > 1:
        component = "/".join(components)
        contents.append(
            "# WARNING: Multiple components detected - consider splitting "
            "commit.\r\n"
        )

    with open(tmp_file, "w", "utf-8") as fh:
        fh.write(template.format(component=component,
                                 author=author,
                                 extra="".join(contents)))


def _check_message(message, options):
    """Checking the message and printing the errors."""
    options = options or dict()

    from flask import current_app
    with current_app.app_context():
        options.update(get_options(current_app.config))

    errors = check_message(message, **options)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)

        return False
    return True


def prepare_commit_msg_hook(argv):
    """Hook: prepare a commit message."""
    from flask import current_app
    with current_app.app_context():
        options = get_options(current_app.config)

    # Check if the repo has a configuration repo
    options.update(_read_local_kwalitee_configuration())

    _prepare_commit_msg(argv[1],
                        _get_git_author(),
                        _get_files_modified(),
                        options.get('template'))
    return 0


def commit_msg_hook(argv):
    """Hook: for checking commit message (prevent commit)."""
    with open(argv[1], "r", "utf-8") as fh:
        message = "\n".join(filter(lambda x: not x.startswith("#"),
                                   fh.readlines()))
    options = {"allow_empty": True}

    if not _check_message(message, options):
        print("Aborting commit due to commit message errors (override with "
              "'git commit --no-verify').", file=sys.stderr)
        return 1
    return 0


def post_commit_hook(argv=None):
    """Hook: for checking commit message."""
    _, stdout, _ = run("git log -1 --format=%B HEAD")
    message = "\n".join(stdout)
    options = {"allow_empty": True}

    if not _check_message(message, options):
        print("Commit message errors (fix with 'git commit --amend').",
              file=sys.stderr)
        return 1
    return 0


def _read_local_kwalitee_configuration(directory="."):
    """Check if the repo has a ``.kwalitee.yaml`` file."""
    filepath = os.path.abspath(os.path.join(directory, '.kwalitee.yml'))
    data = {}
    if os.path.exists(filepath):
        with open(filepath, 'r') as file_read:
            data = yaml.load(file_read.read())
    return data

# =============================================================================
# _pre_commit, pre_commit_hook() and run() is based on initially on Flake8
# git_hook, which is covered by the license:

# Copyright (C) 2014, 2015 CERN
# Copyright (C) 2011-2013 Tarek Ziade <tarek@ziade.org>
# Copyright (C) 2012-2013 Ian Cordasco <graffatcolmingov@gmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def _pre_commit(files, options):
    """Run the check on files of the added version.

    They might be different than the one on disk. Equivalent than doing a git
    stash, check, and git stash pop.
    """
    errors = []
    tmpdir = mkdtemp()
    files_to_check = []
    try:
        for (file_, content) in files:
            # write staged version of file to temporary directory
            dirname, filename = os.path.split(os.path.abspath(file_))
            prefix = os.path.commonprefix([dirname, tmpdir])
            dirname = os.path.relpath(dirname, start=prefix)
            dirname = os.path.join(tmpdir, dirname)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            filename = os.path.join(dirname, filename)
            with open(filename, "wb") as fh:
                fh.write(content)
            files_to_check.append((file_, filename))

        for (file_, filename) in files_to_check:
            errors += list(map(lambda x: "{0}: {1}".format(file_, x),
                               check_file(filename, **options) or []))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return errors


def pre_commit_hook(argv=None):
    """Hook: checking the staged files."""
    from flask import current_app
    with current_app.app_context():
        options = get_options(current_app.config)

    # Check if the repo has a configuration repo
    options.update(_read_local_kwalitee_configuration())

    files = []
    for filename in _get_files_modified():
        # get the staged version of the file and
        # write the staged version to temp dir with its full path to
        # avoid overwriting files with the same name
        _, stdout, _ = run("git show :{0}".format(filename), raw_output=True)
        files.append((filename, stdout))

    errors = _pre_commit(files, options)

    for error in errors:
        if hasattr(error, "decode"):
            error = error.decode()
        print(error, file=sys.stderr)

    if errors:
        print("Aborting commit due to kwalitee errors (override with "
              "'git commit --no-verify').",
              file=sys.stderr)
        return 1
    return 0


def run(command, raw_output=False):
    """Run a command using subprocess.

    :param command: command line to be run
    :type command: str
    :param raw_output: does not attempt to convert the output as unicode
    :type raw_output: bool
    :return: error code, output (``stdout``) and error (``stderr``)
    :rtype: tuple

    """
    p = Popen(command.split(), stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = p.communicate()
    # On python 3, subprocess.Popen returns bytes objects.
    if not raw_output:
        return (
            p.returncode,
            [line.rstrip() for line in stdout.decode("utf-8").splitlines()],
            [line.rstrip() for line in stderr.decode("utf-8").splitlines()]
        )
    else:
        return (p.returncode, stdout, stderr)
# =============================================================================
