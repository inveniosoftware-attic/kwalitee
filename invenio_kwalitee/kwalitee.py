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
import pep8
import shutil
import codecs
import operator
import pyflakes
import pyflakes.checker
import requests
import tempfile
from flask import json
from datetime import datetime


# Max number of errors to be sent back
MAX = 130

_re_copyright_year = re.compile(r"^Copyright\s+(?:\([Cc]\)|\xa9)\s+"
                                r"(?:\d{4},\s+)*"
                                r"(?P<year>\d{4})\s+CERN\.?$",
                                re.UNICODE | re.MULTILINE)

_re_program = re.compile(r"^(?P<program>.*?) is free software;",
                         re.UNICODE | re.MULTILINE)
_re_program_2 = re.compile(r"^(?P<program>.*?) is distributed in",
                           re.UNICODE | re.MULTILINE)
_re_program_3 = re.compile(r"GNU General Public License\s+along\s+with "
                           r"(?P<program>.*?)[;\.]",
                           re.UNICODE | re.MULTILINE)

_messages_codes = {
    "M100": "needs more reviewers",
    "M101": "missing component name",
    "M102": "unrecognized component name: {0}",
    "M103": "no bullets are allowed after signatures",
    "M104": "missing empty line before bullet",
    "M105": "indentation of two spaces expected",
    "M106": "line is too long ({1} > {0})",
    "M107": "unrecognized bullet/signature",
    "M108": "signature is missing",
}

_licenses_codes = {
    "I100": "license is missing",
    "I101": "copyright is missing",
    "I102": "copyright year is outdated, expected {0} but got {1}",
    "I103": "license is not GNU GPLv2",
}


def _check_1st_line(line, components, max_first_line=50, **kwargs):
    """Check that the first line has a known component name followed by a colon
    and then a short description of the commit"""
    errors = []
    if len(line) > max_first_line:
        errors.append(("M106", 1, max_first_line, len(line)))

    if ':' not in line:
        errors.append(("M101", 1))
    else:
        component, msg = line.split(':', 1)
        if component not in components:
            errors.append(("M102", 1, component))

    return errors


def _check_bullets(lines, max_length=72, **kwargs):
    """Check that the bullet point list is well formatted. Each bullet point
    shall have one space before and after it. The bullet character is the
    "*" and there is no space before it but one after it meaning the next line
    are starting with two blanks spaces to respect the identation.
    """
    errors = []
    missed_lines = []
    skipped = []

    for (i, line) in enumerate(lines[1:]):
        if line.startswith('*'):
            if len(missed_lines) > 0:
                errors.append(("M103", i + 2))
            if lines[i].strip() != '':
                errors.append(("M104", i + 2))
            for (j, indented) in enumerate(lines[i + 2:]):
                if indented.strip() == '':
                    break
                if not re.search(r"^ {2}\S", indented):
                    errors.append(("M105", i + j + 3))
                else:
                    skipped.append(i + j + 1)
        elif i not in skipped and line.strip() != '':
            missed_lines.append((i + 2, line))

        if len(line) > max_length:
            errors.append(("M106", i + 2, max_length, len(line)))

    return errors, missed_lines


def _check_signatures(lines, signatures, trusted=None, **kwargs):
    """Check that there is at least three signatures or that one of them is a
    trusted developer/reviewer.

    Format should be: [signature] full name <email@address>
    """
    matching = []
    errors = []
    trusted = trusted or []
    signatures = tuple(signatures) if signatures else []
    test = operator.methodcaller('startswith', signatures)
    for i, line in lines:
        if signatures and test(line):
            matching.append(line)
        else:
            errors.append(("M107", i))

    if len(matching) == 0:
        errors.append(("M108", 1))
        errors.append(("M100", 1))
    elif len(matching) <= 2:
        pattern = re.compile('|'.join(map(lambda x: '<' + re.escape(x) + '>',
                                          trusted)))
        trusted_matching = list(filter(None, map(pattern.search, matching)))
        if len(trusted_matching) == 0:
            errors.append(("M100", 1))

    return errors


def check_message(message, **kwargs):
    """Check the message format.

    Rules:
    * the first line must start by a component name
    * and a short description (52 chars),
    * then bullet points are expected
    * and finally signatures.

    Required kwargs:
    * components: e.g. ('auth', 'utils', 'misc')
    * signatures: e.g. ('Signed-off-by', 'Reviewed-by')

    Optional args:
    * trusted, e.g. ('john.doe@example.org',), by default empty
    * max_length: by default 72
    * max_first_line: by default 50
    """
    lines = re.split(r"\r\n|\r|\n", message)
    errors = _check_1st_line(lines[0], **kwargs)
    err, signature_lines = _check_bullets(lines, **kwargs)
    errors += err
    errors += _check_signatures(signature_lines, **kwargs)

    def _format(code, lineno, args):
        return "{0}: {1}: {2}".format(code,
                                      lineno,
                                      _messages_codes[code].format(*args))

    return list(map(lambda x: _format(x[0], x[1], x[2:]), errors))


class _PyFlakesChecker(pyflakes.checker.Checker):
    """PEP8 compatible checker for pyFlakes. Inspired by flake8."""
    name = "pyflakes"
    version = pyflakes.__version__

    def run(self):
        for msg in self.messages:
            col = getattr(msg, 'col', 0)
            yield msg.lineno, col, (msg.tpl % msg.message_args), msg.__class__


def _register_pyflakes_check():
    """Register the pyFlakes checker into PEP8 set of checks."""
    # Resolving conflicts between pep8 and pyflakes.
    codes = {
        "UnusedImport": "F401",
        "ImportShadowedByLoopVar": "F402",
        "ImportStarUsed": "F403",
        "LateFutureImport": "F404",
        "Redefined": "F801",
        "RedefinedInListComp": "F812",
        "UndefinedName": "F821",
        "UndefinedExport": "F822",
        "UndefinedLocal": "F823",
        "DuplicateArgument": "F831",
        "UnusedVariable": "F841",
    }

    for name, obj in vars(pyflakes.messages).items():
        if name[0].isupper() and obj.message:
            obj.tpl = "{0} {1}".format(codes.get(name, "F999"), obj.message)

    pep8.register_check(_PyFlakesChecker, codes=['F'])
_registered_pyflakes_check = False


class _Report(pep8.BaseReport):
    """Own reporter that keeps a list of errors in a sortable list and never
    prints.
    """
    def __init__(self, options):
        super(_Report, self).__init__(options)
        self.errors = []

    def error(self, line_number, offset, text, check):
        code = super(_Report, self).error(line_number, offset, text, check)
        if code:
            self.errors.append((line_number, offset + 1, code, text, check))


def check_pep8(filename, **kwargs):
    """Perform static analysis on the given file.

    Options:
    * pep8_ignore: e.g. ('E111', 'E123')
    * pep8_select: ditto
    * pep8_pyflakes: True
    """

    pep8options = {
        "ignore": kwargs.get("pep8_ignore"),
        "select": kwargs.get("pep8_select"),
    }

    if not _registered_pyflakes_check and kwargs.get("pep8_pyflakes", True):
        _register_pyflakes_check()

    checker = pep8.Checker(filename, reporter=_Report, **pep8options)
    checker.check_all()

    errors = []
    checker.report.errors.sort()
    for error in checker.report.errors:
        errors.append("{0}:{1}: {3}".format(*error))
    return errors


def check_license(filename, **kwargs):
    """Perform a license check on the given file.

    The license format should be commented using ## and live at the top of the
    file. Also, the year should be the current one.

    Supported filetypes: python, jinja
    """
    year = kwargs.pop("year", datetime.now().year)
    errors = []
    lines = []
    ignores = kwargs.get("pep8_ignore")
    template = "{0}: {1} {2}"
    file_is_empty = False
    license = ""
    lineno = 0
    re_comment = re.compile(r"^#.*|\{#.*|[\r\n]+$")
    with codecs.open(filename, "r", "utf-8") as fp:
        line = fp.readline()
        blocks = []
        while re_comment.match(line):
            if line.startswith("##"):
                line = line.lstrip("# ")
                blocks.append(line)
                lines.append((lineno, line.strip()))
            lineno, line = lineno + 1, fp.readline()
        file_is_empty = line == ""
        license = "".join(blocks)

    if file_is_empty and license == "":
        return errors

    match_year = _re_copyright_year.search(license)
    if match_year is None:
        errors.append((lineno, "I101"))
    elif int(match_year.group("year")) != year:
        theline = match_year.group(0)
        lno = lineno
        for no, l in lines:
            if theline.strip() == l:
                lno = no
                break
        errors.append((lno + 1, "I102", year, match_year.group("year")))
    else:
        program_match = _re_program.search(license)
        program_2_match = _re_program_2.search(license)
        program_3_match = _re_program_3.search(license)
        if program_match is None:
            errors.append((lineno, "I100"))
        elif (program_2_match is None or
              program_3_match is None or
              (program_match.group("program").upper() !=
               program_2_match.group("program").upper() !=
               program_3_match.group("program").upper())):
            errors.append((lineno, "I103"))

    def _format_error(lineno, code, *args):
        return template.format(lineno, code,
                               _licenses_codes[code].format(*args))

    def _filter_codes(error):
        if not ignores or error[1] not in ignores:
            return error

    return list(map(lambda x: _format_error(*x),
                    filter(_filter_codes, errors)))


def check_file(filename, **kwargs):
    """Perform static analysis on the given file.

    See: check_pep8 and check_license
    """
    if filename.endswith(".py"):
        return check_pep8(filename, **kwargs) + \
            check_license(filename, **kwargs)
    else:
        return check_license(filename, **kwargs)


def get_component(filename):
    """ Get components name from filename """
    parts = filename.split(os.path.sep)

    if len(parts) >= 3:
        if parts[1] == 'modules':
            return parts[2]
        if parts[1] == 'legacy':
            return parts[2]
        if parts[1] == 'ext':
            return parts[2]
    if len(parts) >= 2:
        if parts[1] in ['base', 'celery', 'utils', ]:
            return parts[1]
    if len(parts) >= 1:
        if parts[0] in ['grunt', 'docs', ]:
            return parts[0]
    return 'global'


def _get_issue_labels(issue_url):
    """Downloads the labels of the issue."""
    issue = json.loads(requests.get(issue_url).content)
    labels = set()
    for label in issue["labels"]:
        labels.add(label["name"])
    return labels, issue["labels_url"]


def get_options(config):
    kwargs = {
        "components": config.get("COMPONENTS", None),
        "signatures": config.get("SIGNATURES", None),
        "trusted": config.get("TRUSTED_DEVELOPERS", None)
    }

    kwargs["pep8"] = config.get("CHECK_PEP8", True)
    kwargs["license"] = config.get("CHECK_LICENSE", True)
    kwargs["pep8_pyflakes"] = config.get("CHECK_PYFLAKES", True)
    kwargs["pep8_ignore"] = config.get("PEP8_IGNORE", None)
    kwargs["pep8_select"] = config.get("PEP8_SELECT", None)

    return kwargs


def pull_request(pull_request_url, status_url, config):
    """
    Performing all the tests on the pull request and pings back the given
    status_url.
    """
    body = {}
    errors = []
    pull_request = requests.get(pull_request_url)
    data = json.loads(pull_request.content)
    options = get_options(config)
    headers = {
        "Content-Type": "application/json",
        # This is required to post comments on GitHub on yours behalf.
        # Please update your configuration accordingly.
        "Authorization": "token {0}".format(config["ACCESS_TOKEN"])
    }
    instance_path = config["instance_path"]

    commit_sha = data["head"]["sha"]
    issue_url = data["issue_url"]
    commits_url = data["commits_url"]
    files_url = data["commits_url"].replace("/commits", "/files")
    review_comments_url = data["review_comments_url"]

    # Check only if the title does not contain 'wip'.
    is_wip = bool(re.match(r"\bwip\b", data["title"], re.IGNORECASE))
    check = config.get("CHECK_WIP", False) or not is_wip
    check_commit_messages = config.get("CHECK_COMMIT_MESSAGES", True)
    check_pep8 = options['pep8']
    check_pyflakes = options['pep8_pyflakes']
    check_license = options['license']

    labels, labels_url = _get_issue_labels(issue_url)
    labels.discard(config.get("LABEL_WIP", "in_work"))
    labels.discard(config.get("LABEL_REVIEW", "in_review"))
    labels.discard(config.get("LABEL_READY", "in_integration"))
    new_labels = set([])

    if check and check_commit_messages:
        errs, new_labels, messages = _check_commits(commits_url, **options)
        errors += errs

        for msg in messages:
            body = "\n".join(msg["errors"])
            if body is not "":
                requests.post(msg["comments_url"],
                              data=json.dumps(dict(body=body)),
                              headers=headers)

    if check and (check_pep8 or check_pyflakes or check_license):
        errs, messages = _check_files(files_url, **options)
        errors += errs
        for msg in messages:
            body = "\n".join(msg["errors"])
            if body is not "":
                # Comment on first line with problem.
                position = int(msg["errors"][0].split(':')[0])
                position = position if position > -1 else 0
                requests.post(review_comments_url,
                              data=json.dumps(dict(body=body,
                                                   commit_id=msg["sha"],
                                                   path=msg["path"],
                                                   position=position)),
                              headers=headers)

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

    if is_wip:
        new_labels = set([config.get("LABEL_WIP", "in_work")])
    if not new_labels:
        if not errors:
            new_labels = set([config.get("LABEL_READY", "in_integration")])
        else:
            new_labels = set([config.get("LABEL_REVIEW", "in_review")])

    labels.update(new_labels)
    requests.put(labels_url.replace("{/name}", ""),
                 data=json.dumps(list(labels)),
                 headers=headers)

    return dict(body, labels=list(labels))


def _check_commits(url, **kwargs):
    """Check the commit messages of a pull request."""
    errors = []
    messages = []
    labels = set()

    response = requests.get(url)
    commits = json.loads(response.content)
    for commit in commits:
        sha = commit["sha"]
        errs = check_message(commit["commit"]["message"], **kwargs)

        # filter out the needs more reviewerss
        e = list(filter(lambda x: not x.startswith("M100:"), errs))

        if len(errs) > len(e):
            labels.add(kwargs.get("LABEL_REVIEW", "in_review"))

        messages.append({
            "sha": sha,
            "comments_url": commit["comments_url"],
            "errors": e
        })
        errors += list(map(lambda x: "{0}: {1}".format(sha, x), errs))
    return errors, labels, messages


def _check_files(url, **kwargs):
    """Downloads and runs the checks on the files of a pull request."""
    errors = []
    messages = []

    response = requests.get(url)
    files = json.loads(response.content)
    tmp = tempfile.mkdtemp()
    try:
        sha_match = re.compile(r"(?<=ref=)[^=]+")
        for f in files:
            filename = f["filename"]
            sha = sha_match.search(f["contents_url"]).group(0)
            if filename.endswith(".py") or filename.endswith(".html"):
                response = requests.get(f["raw_url"])
                path = os.path.join(tmp, filename)
                dirname = os.path.dirname(path)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)
                with open(path, "wb+") as fp:
                    for block in response.iter_content(1024):
                        fp.write(block)

                errs = check_file(path, **kwargs)

                messages.append({
                    "path": filename,
                    "sha": sha,
                    "errors": errs
                })

                errors += list(map(lambda x: "{0}: {1}:{2}"
                                             .format(sha, filename, x),
                                   errs))
    finally:
        shutil.rmtree(tmp)
    return errors, messages
