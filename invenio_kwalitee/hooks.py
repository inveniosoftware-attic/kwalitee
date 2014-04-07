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


from __future__ import print_function, absolute_import

import os
import sys
from subprocess import Popen, PIPE
import shutil
from tempfile import mkdtemp
import six

from .kwalitee import check_file, check_message, get_options, get_component


#
# Helper
#
def check_files(files):
    """
    Check a list of files
    """
    from invenio_kwalitee import app
    with app.app_context():
        options = get_options(app.config)

        report = {'errors': {}, 'count': 0}

        for f in files:
            report['errors'][f] = check_file(f, **options)
            report['count'] += len(report['errors'][f])

        return report


def check_commit_message(msg):
    """
    """
    from invenio_kwalitee import app

    if msg and not msg.isspace():
        with app.app_context():
            options = get_options(app.config)
            errs = check_message(msg, **options)

            for e in errs:
                print(e, file=sys.stderr)

            return len(errs)
    return 0


#
# Hooks
#
def prepare_commit_msg_hook():
    """
    Prepare a commitm
    """
    from invenio_kwalitee import app

    # Only prepare message if there's no message already
    with open(sys.argv[1], 'r') as fh:
        contents = fh.readlines()
        msg = "\n".join(
            filter(lambda x: not x.startswith('#'), contents)
        )
        if msg and not msg.isspace():
            return 0

    # Get author
    _, git_author, _ = run("""git var GIT_AUTHOR_IDENT""")

    git_author = git_author[0]
    git_author = git_author[:git_author.find('>')+1]

    # Get components
    _, files_modified, _ = run(
        "git diff-index --cached --name-only --diff-filter=ACMRTUXB HEAD"
    )
    files_modified = [f for f in files_modified if (
        f.endswith('.py') or f.endswith('.html'))
    ]

    component = 'unknown'
    components = set()
    extra = contents

    for f in files_modified:
        components.add(get_component(f))

    if len(components) == 1:
        component = list(components)[0]
    if len(components) > 1:
        component = "/".join(components)
        extra.append(
            "# WARNING: Multiple components detected - consider splitting "
            "commit.\n"
        )

    # Write template
    with app.app_context():
        ctx = dict(
            component=component,
            author=git_author,
            extra="".join(extra),
        )
        with open(sys.argv[1], 'wb') as fh:
            fh.write(six.b(app.config['COMMIT_MSG_TEMPLATE'] % ctx))


def commit_msg_hook():
    """
    Hook for checking commit message
    """
    # commit-msg hook first arguemtn is path to tmp file with commit
    # message (i.e. sys.argv[1])
    with open(sys.argv[1], 'r') as fh:
        msg = "\n".join(
            filter(lambda x: not x.startswith('#'), fh.readlines())
        )
        ret = check_commit_message(msg)
        if ret != 0:
            print("Aborting commit due commit message errors (override "
                  "with 'git commit --no-verify').")
        return ret


def post_commit_hook():
    """
    Hook for checking commit message
    """
    _, msg, _ = run("""git log -1 --format="%B" HEAD""")

    ret = check_commit_message(msg[0])

    if ret != 0:
        print("Commit message errors (fix with "
              "'git commit --amend').")

    return ret


# =============================================================================
# pre_commit_hook() and run() is based on initially on Flake8 git_hook, which
# is covered by the license:

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

def pre_commit_hook():
    """
    Hook for checking committed files
    """
    gitcmd = "git diff-index --cached --name-only --diff-filter=ACMRTUXB HEAD"

    # Returns the exit code, list of files modified, list of error messages
    _, files_modified, _ = run(gitcmd)

    files_modified = [f for f in files_modified if (
        f.endswith('.py') or f.endswith('.html'))
    ]

    # Copy staged versions to temporary directory
    tmpdir = mkdtemp()
    files_to_check = []
    try:
        for file_ in files_modified:
            # get the staged version of the file
            gitcmd_getstaged = "git show :%s" % file_
            _, out, _ = run(gitcmd_getstaged, raw_output=True, decode=False)
            # write the staged version to temp dir with its full path to
            # avoid overwriting files with the same name
            dirname, filename = os.path.split(os.path.abspath(file_))
            prefix = os.path.commonprefix([dirname, tmpdir])
            dirname = os.path.relpath(dirname, start=prefix)
            dirname = os.path.join(tmpdir, dirname)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            filename = os.path.join(dirname, filename)
            # write staged version of file to temporary directory
            with open(filename, "wb") as fh:
                fh.write(out)
            files_to_check.append(filename)
        # Run the checks
        report = check_files(files_to_check)
    # remove temporary directory
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # Print errors
    for f, errs in six.iteritems(report['errors']):
        for e in errs:
            print("%s: %s" % (f, e), file=sys.stderr)

    if report['count'] > 0:
        print("Aborting commit due kwalitee errors (override with "
              "'git commit --no-verify').")

    return report['count']


def run(command, raw_output=False, decode=True):
    p = Popen(command.split(), stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = p.communicate()
    # On python 3, subprocess.Popen returns bytes objects which expect
    # endswith to be given a bytes object or a tuple of bytes but not native
    # string objects. This is simply less mysterious than using b'.py' in the
    # endswith method. That should work but might still fail horribly.
    if hasattr(stdout, 'decode'):
        if decode:
            stdout = stdout.decode()
    if hasattr(stderr, 'decode'):
        if decode:
            stderr = stderr.decode()
    if not raw_output:
        stdout = [line.strip() for line in stdout.splitlines()]
        stderr = [line.strip() for line in stderr.splitlines()]
    return (p.returncode, stdout, stderr)
# =============================================================================
