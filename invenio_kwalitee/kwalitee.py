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
import re
import requests
import operator
from flask import json


# Max number of errors to be sent back
MAX = 130


def _check_1st_line(line, components, max_first_line=50, **kwargs):
    """Check that the first line has a known component name followed by a colon
    and then a short description of the commit"""
    errors = []
    if len(line) > max_first_line:
        errors.append('First line is too long')

    if ':' not in line:
        errors.append('Missing component name')
    else:
        component, msg = line.split(':', 1)
        if component not in components:
            errors.append('Unknown "{0}" component name'.format(component))

    return errors


def _check_bullets(lines, max_length=72, **kwargs):
    """Check that the bullet point list is well formatted. Each bullet point
    shall have one space before and after it. The bullet character is the
    "*" and there is no space before it but one after it meaning the next line
    are starting with two blanks spaces to respect the identation.
    """
    errors = []
    missed_lines = []

    for (i, line) in enumerate(lines[1:]):
        if line.startswith('*'):
            if len(missed_lines) > 0:
                errors.append("No bullets are allowed after signatures on line"
                              " {0}".format(i+1))
            if lines[i].strip() != '':
                errors.append('Missing empty line before line {0}'.format(i+1))
            for (j, indented) in enumerate(lines[i+2:]):
                if indented.strip() == '':
                    break
                if not re.search(r"^ {2}\S", indented):
                    errors.append('Wrong indentation on line {0}'
                                  .format(i+j+3))
        elif line.strip() != '':
            missed_lines.append((i+1, line))

        if len(line) > max_length:
            errors.append('Line {0} is too long ({1} > {2})'
                          .format(i+2, len(line), max_length))

    return errors, missed_lines


def _check_signatures(lines, signatures, trusted, **kwargs):
    """Check that there is at least three signatures or that one of them is a
    trusted developer/reviewer.

    Format should be: [signature] full name <email@address>
    """
    matching = []
    errors = []
    test = operator.methodcaller('startswith', signatures)
    for i, line in lines:
        if signatures and test(line):
            matching.append(line)
        else:
            errors.append('Unrecognized bullet/signature on line {0}: "{1}"'
                          .format(i, line))

    if len(matching) == 0:
        errors.append('Signature missing')
    elif len(matching) <= 2:
        pattern = re.compile('|'.join(map(lambda x: '<' + re.escape(x) + '>',
                                          trusted)))
        trusted_matching = list(filter(None, map(pattern.search, matching)))
        if len(trusted_matching) == 0:
            errors.append('Needs more reviewers')

    return errors


def check_message(message, **kwargs):
    """Check the message format. The first line must start by a component
    name and shoart description (52 chars), then bullet points are expected
    and finally signatures. Anything else will be rejected."""
    lines = re.split(r"\r\n|\r|\n", message)
    errors = _check_1st_line(lines[0], **kwargs)
    err, signatures = _check_bullets(lines, **kwargs)
    errors += err
    errors += _check_signatures(signatures, **kwargs)
    return errors


def pull_request(pull_request_url, status_url, config):
    errors = []
    pull_request = requests.get(pull_request_url)
    data = json.loads(pull_request.content)
    kwargs = {
        "components": config.get("COMPONENTS", []),
        "signatures": config.get("SIGNATURES", []),
        "trusted": config.get("TRUSTED_DEVELOPERS", [])
    }
    headers = {
        "Content-Type": "application/json",
        # This is required to post comments on GitHub on yours behalf.
        # Please update your configuration accordingly.
        "Authorization": "token {0}".format(config["ACCESS_TOKEN"])
    }
    instance_path = config["instance_path"]

    commits_url = data["commits_url"]
    commit_sha = data["head"]["sha"]

    # Check only if the title does not contain 'wip'.
    must_check = re.search(r"\bwip\b",
                           data["title"],
                           re.IGNORECASE) is None

    if must_check is True:
        response = requests.get(commits_url)
        commits = json.loads(response.content)
        for commit in commits:
            sha = commit["sha"]
            message = commit["commit"]["message"]
            errs = check_message(message, **kwargs)

            requests.post(commit["comments_url"],
                          data=json.dumps({"body": "\n".join(errs)}),
                          headers=headers)
            errors += map(lambda x: "%s: %s" % (sha, x), errs)

        filename = "status_{0}.txt".format(commit_sha)
        with open(os.path.join(instance_path, filename), "w+") as f:
            f.write("\n".join(errors))

    state = "error" if len(errors) > 0 else "success"
    body = dict(state=state,
                target_url=status_url,
                description="\n".join(errors)[:MAX])
    requests.post(data["statuses_url"],
                  data=json.dumps(body),
                  headers=headers)
