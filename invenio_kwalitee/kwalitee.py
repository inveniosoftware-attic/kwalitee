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

import re
import requests
import operator
from flask import current_app, json, url_for


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
        if test(line):
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


class Kwalitee(object):
    def __init__(self, app=None, **kwargs):
        if app is not None:
            kwargs.update({
                "components": app.config["COMPONENTS"],
                "signatures": app.config["SIGNATURES"],
                "trusted": app.config["TRUSTED_DEVELOPERS"],
            })
        self.config = kwargs
        # This is your Github personal API token, our advice is to
        # put it into instance/invenio_kwalitee.cfg so it won't be
        # versioned ever. Keep it safe.
        self.token = app.config.get("ACCESS_TOKEN", None)

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value

    def __headers(self):
        headers = {"Content-Type": "application/json"}
        if self._token is not None:
            headers["Authorization"] = "token {0}".format(self._token)
        return headers

    def __call__(self, request):
        self.request = request
        if "X-GitHub-Event" in request.headers:
            event = request.headers["X-GitHub-Event"]
        else:
            raise ValueError("No X-GitHub-Event HTTP header found")

        data = json.loads(request.data)
        fn = getattr(self, "on_{0}".format(event))

        return fn(data)

    def __getattr__(self, command):
        raise NotImplementedError("{0}.{1} method is missing"
                                  .format(self.__class__.__name__, command))

    def on_ping(self, data):
        return dict(message="Hi there!")

    def on_pull_request(self, data):
        errors = []

        commits_url = data['pull_request']['commits_url']
        # Check only if title does not contain 'wip'.
        title = data['pull_request'].get('title', '')
        if title.lower().find('wip') == -1:
            response = requests.get(commits_url)
            commits = json.loads(response.content)
            for commit in commits:
                sha = commit["sha"]
                message = commit["commit"]["message"]
                errs = check_message(message, **self.config)

                requests.post(commit["comments_url"],
                              data=json.dumps({"body": "\n".join(errs)}),
                              headers=self.__headers())
                errors += map(lambda x: "%s: %s" % (sha, x), errs)

        state = "error" if len(errors) > 0 else "success"

        commit_sha = data["pull_request"]["head"]["sha"]

        filename = "status_{0}.txt".format(commit_sha)
        with current_app.open_instance_resource(filename, "w+") as f:
            f.write("\n".join(errors))

        body = dict(state=state,
                    target_url=url_for("status", commit_sha=commit_sha,
                                       _external=True),
                    description="\n".join(errors)[:MAX])
        requests.post(data["pull_request"]["statuses_url"],
                      data=json.dumps(body),
                      headers=self.__headers())
        return body
