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

"""Tasks to run on the worker."""

from __future__ import unicode_literals

import os
import re
import shutil
import logging
import tempfile
import requests
import yaml
from flask import json

from .kwalitee import get_options, check_message, check_file
from .models import db, BranchStatus, CommitStatus
# Worker logger
LOGGER = logging.getLogger("rq.worker")


def get_headers(repository, config):
    """Get the HTTP headers for the GitHub api.

    This is required to post comments on GitHub on your behalf.
    Please update your configuration accordingly.

    .. code-block:: python

        ACCESS_TOKEN = "deadbeef..."

    It can also be overwritten per user.

    .. code-block:: console

        $ kwalitee account add username --token=deadbeef...

    :return: HTTP headers
    :rtype: dict

    """
    token = repository.owner.token or config["ACCESS_TOKEN"]
    return {
        "Content-Type": "application/json",
        "Authorization": "token {token}".format(token=token)
    }


def push(commit_status_id, commit_url, status_url, config):
    """Performing all the tests on the commit.

    :param commit_status_id: identifier of the branch status
    :param commit_url: github api commit url
    :param status_url: github api status url
    :param config: configuration dictionary

    """
    body = {}
    length = 0

    commit_status = CommitStatus.query.filter_by(id=commit_status_id).first()
    if not commit_status:
        raise AssertionError("Unknown commit: {0} ({1})"
                             .format(commit_status_id, commit_url))

    options = get_options(config)
    headers = get_headers(commit_status.repository, config)

    check_commit_messages = config.get("CHECK_COMMIT_MESSAGES", True)
    check_pep8 = options["pep8"]
    check_pep257 = options["pep257"]
    check_license = options["license"]
    check_files = check_pep8 or check_pep257 or check_license

    commit = requests.get(commit_url, headers=headers)
    data = json.loads(commit.content)

    # FIXME guessing the status URL based on the commit one.
    statuses_url = data["url"].replace("commits", "statuses")
    comments_url = data["comments_url"]
    sha = data["sha"]
    files = data["files"]

    # Check only if the component does not contain 'wip'.
    component = data["commit"]["message"].split(":", 1)[0]
    is_wip = bool(re.match(r"\bwip\b", component, re.IGNORECASE))
    check = config.get("CHECK_WIP", False) or not is_wip

    # This commit might have been checked in a pull request, which skipped
    # the files check.
    is_new = False
    checked = False
    if commit_status.is_pending() or commit_status.content["files"] is None:
        is_new = True

    if check and check_commit_messages:
        errs = _check_commit(commit_status, data, **options)
        length = len(errs)
        checked = True

    if check and is_new and checked and length:
        body = "\n".join(commit_status.content["message"])
        try:
            requests.post(comments_url,
                          data=json.dumps(dict(body=body.strip())),
                          headers=headers)
        except requests.RequestException:
            LOGGER.exception(comments_url)

    if check and is_new and check_files:
        tmp = tempfile.mkdtemp()
        filenames = _download_files_from_commit(files, sha, tmp)
        total, messages = _check_files(filenames, tmp, **options)
        shutil.rmtree(tmp)

        commit_status.content = dict(commit_status.content, files=messages)
        length += total

        if total:
            _post_file_comments(comments_url, messages, headers)

    if not check:
        commit_status.content = dict(commit_status.content, message=[])

    db.session.add(commit_status)
    db.session.commit()

    state = "error" if length > 0 else "success"
    body = dict(state=state,
                target_url=status_url,
                description="[{0}] {1} errors".format(state, length),
                context=config.get("CONTEXT"))

    # Do not send the status if we've already seen this commit in the past.
    if is_new:
        try:
            requests.post(statuses_url,
                          data=json.dumps(body),
                          headers=headers)
        except requests.RequestException:
            LOGGER.exception(statuses_url)
    return body


def pull_request(branch_status_id, pull_request_url, status_url, config):
    """Performing all the tests on the pull request.

    Then pings back the given status_url and update the issue labels.

    :param branch_status_id: identifier of the branch status.
    :type branch_status_id: int
    :param pull_request_url: github api pull request
    :type pull_request_url: str
    :param status_url: github api status url
    :type status_url: str
    :param config: configuration dictionary
    :type config: dict
    :return: status body and applied labels
    :rtype: dict

    """
    errors = {"message": [], "commits": [], "files": {}}
    length = 0

    branch_status = BranchStatus.query.filter_by(id=branch_status_id).first()

    if not branch_status:
        raise AssertionError("Unknown branch: {0} ({1})"
                             .format(branch_status_id, pull_request_url))
    if not branch_status.is_pending():
        LOGGER.info("Known pull request, skipping.")
        return branch_status.errors

    options = get_options(config)

    headers = get_headers(branch_status.commit.repository, config)

    pull_request = requests.get(pull_request_url, headers=headers)
    data = json.loads(pull_request.content)

    # Update config with .kwalitee.yml from git root folder
    options.update(_check_for_kwalitee_configuration(data))

    issue_url = data["issue_url"]
    commits_url = data["commits_url"]
    files_url = data["commits_url"].replace("/commits", "/files")
    review_comments_url = data["review_comments_url"]

    # Check only if the title does not contain 'wip'.
    is_wip = bool(re.match(r"\bwip\b", data["title"], re.IGNORECASE))
    check = config.get("CHECK_WIP", False) or not is_wip
    options["CHECK"] = check

    check_pep8 = options["pep8"]
    check_pep257 = options["pep257"]
    check_license = options["license"]
    check_files = check_pep8 or check_pep257 or check_license

    # Checking commits
    errs, messages = _check_commits(
        branch_status.commit.repository,
        commits_url,
        **options
    )

    errors["message"] += errs
    length += len(errs)

    for msg in messages:
        errors["commits"].append(msg["status"])
        body = "\n".join(msg["errors"]["message"])
        if body is not "":
            if db.session.is_modified(msg["status"]):
                db.session.add(msg["status"])
                try:
                    requests.post(msg["comments_url"],
                                  data=json.dumps(dict(body=body)),
                                  headers=headers)
                except requests.RequestException:
                    LOGGER.exception(msg["comments_url"])

    db.session.commit()

    # Checking the files
    if check and check_files:
        tmp = tempfile.mkdtemp()
        filenames = _download_files_from_pull_request(files_url, tmp)
        total, messages = _check_files(filenames, tmp, **options)
        shutil.rmtree(tmp)

        errors["files"].update(messages)
        length += total

        if total:
            _post_file_comments(review_comments_url, messages, headers)
        state = "error" if length > 0 else "success"
        body = dict(state=state,
                    target_url=status_url,
                    description="[{0}] {1} errors".format(state, length),
                    context=config.get("CONTEXT"))
        try:
            requests.post(data["statuses_url"],
                          data=json.dumps(body),
                          headers=headers)
        except requests.RequestException:
            LOGGER.exception(data["statuses_url"])

    branch_status.content = errors
    db.session.add(branch_status)
    db.session.commit()

    new_labels = set()
    if is_wip:
        new_labels = set([config.get("LABEL_WIP", "in_work")])
    if not new_labels:
        if length == 0:
            new_labels = set([config.get("LABEL_READY", "in_integration")])
        else:
            new_labels = set([config.get("LABEL_REVIEW", "in_review")])
    labels = _update_labels(issue_url, new_labels, headers, config)

    return dict(errors, labels=list(labels))


def _update_labels(issue_url, new_labels, headers, config):
    """Update the labels of an issue.

    :param issue_url: url of the issue to read the existing labels from.
    :param new_labels: set of new labels to be applied.
    :return: set of updated labels of the issue.
    """
    labels, labels_url = _get_issue_labels(issue_url)
    labels.discard(config.get("LABEL_WIP", "in_work"))
    labels.discard(config.get("LABEL_REVIEW", "in_review"))
    labels.discard(config.get("LABEL_READY", "in_integration"))

    labels.update(new_labels)
    try:
        requests.put(labels_url.replace("{/name}", ""),
                     data=json.dumps(list(labels)),
                     headers=headers)
    except requests.RequestException:
        LOGGER.exception(labels_url)

    return labels


def _post_file_comments(comments_url, messages, headers):
    """Post comment on each file."""
    # Sorting the filenames so the output is predictable and tests are easier.
    filenames = list(messages.keys())
    filenames.sort()
    for filename in filenames:
        msg = messages[filename]
        body = "\n".join(msg["errors"])
        if body is not "":
            # Comment on first line.
            position = 0
            try:
                requests.post(comments_url,
                              data=json.dumps(dict(body=body,
                                                   commit_id=msg["sha"],
                                                   path=filename,
                                                   position=position)),
                              headers=headers)
            except requests.RequestException:
                LOGGER.exception(comments_url)


def _download_files_from_pull_request(url, tmp):
    """Download the files of a pull request.

    :param url: pull request's list of files URL
    :param tmp: temporary directory to put the files into
    :return: filenames with their sha1
    """
    sha_match = re.compile(r"(?<=ref=)[^=]+")
    response = requests.get(url)
    files = json.loads(response.content)

    for f in files:
        filename = f["filename"]
        sha = sha_match.search(f["contents_url"]).group(0)

        _download_file(f["raw_url"], os.path.join(tmp, filename))

        yield (sha, filename)


def _download_files_from_commit(files, sha, tmp):
    """Download the files from the commit.

    :param files: list of files from the commit JSON
    :param tmp: temporary directory to put the files into
    :returns: filenames
    """
    for f in files:
        if f["status"] != "removed":
            filename = f["filename"]

            if _download_file(f["raw_url"], os.path.join(tmp, filename)):
                yield (sha, filename)


def _download_file(source, destination):
    """Download the given file and puts it at the desired place."""
    try:
        response = requests.get(source)

        # File not found or other error.
        if response.status_code > 400:
            return requests.HTTPError(response.status_code)

        dirname = os.path.dirname(destination)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(destination, "wb+") as fp:
            for block in response.iter_content(1024):
                if block:
                    fp.write(block)

        return True
    except requests.RequestException:
        LOGGER.exception(source)
        return False


def _get_issue_labels(issue_url):
    """Download the labels of the issue."""
    issue = json.loads(requests.get(issue_url).content)
    labels = set()
    for label in issue["labels"]:
        labels.add(label["name"])
    return labels, issue["labels_url"]


def _check_commit(commit_status, commit, **kwargs):
    """Check one commit message.

    Does nothing if the commit has already been checked in the past.

    :param commit_status: commit status
    :type: CommitStatus
    :param commit: json object
    :type commit: dict
    :return: errors
    :rtype: list
    """
    errs = None

    if commit_status.is_pending():
        errs = check_message(commit["commit"]["message"], **kwargs)
        commit_status.content = dict(commit_status.content, message=errs)
    else:
        errs = commit_status.content["message"]

    return errs


def _check_commits(repository, url, **kwargs):
    """Check the commit messages of a pull request."""
    errors = []
    messages = []

    check = kwargs.get("CHECK")
    check_commit_messages = kwargs.get("CHECK_COMMIT_MESSAGES", True)

    response = requests.get(url)
    commits = json.loads(response.content)
    for commit in reversed(commits):
        errs = []
        sha = commit["sha"]
        url = commit["html_url"]

        commit_status = CommitStatus.query.filter_by(
            repository_id=repository.id,
            sha=sha).first()

        if not commit_status:
            raise AssertionError(
                "CommitStatus not found for {0.fullname} {sha}"
                .format(repo=repository, sha=sha))

        if check and check_commit_messages:
            errs = _check_commit(commit_status, commit, **kwargs)

        # filter out the needs more reviewers
        e = list(filter(lambda x: not re.match(r"\d+: M100\b", x), errs))

        messages.append({
            "sha": sha,
            "status": commit_status,
            "comments_url": commit["comments_url"],
            "errors": {
                "message": e,
                "files": {}
            }
        })
        errors += list(map(lambda x: "{0}: {1}".format(sha, x), errs))
    return errors, messages


def _check_files(files, cwd, **kwargs):
    """Download and runs the checks on the files of a pull request.

    Format of the dict returned.

    .. code-block:: json

        {
            "filename": {
                "sha": ...
                "errors": [...]
            },
            "filename2": { ... }
        }

    :param files: list of files ``(sha, filename)``.
    :param cwd: directory where the files are located.
    :param kwargs: arguments for :meth:`check_file`.
    :return: tuple composed of the number of errors found and a dict with the
             files checked.
    """
    total = 0
    messages = {}

    for sha, filename in files:
        errors = check_file(os.path.join(cwd, filename), **kwargs)

        messages[filename] = {
            "sha": sha,
            "errors": errors
        }
        total += len(errors or [])
    return total, messages


def _check_for_kwalitee_configuration(github_pr):
    """Check if a configuaration file exists in the repo.

    .. note::

        If the `.kwalitee.yml` file has not been found it will return
        an empty dict will not affect the process.

    :param dict github_pr: responded github pull_request object
    :return: yaml parsed configuration
    :rtype: dict
    """
    # download .kwalitee.yml if exists
    github_contents_api = (
        "https://api.github.com/repos/{name}/contents/.kwalitee.yml"
        "?ref={branch}"
    ).format(
        name=github_pr.get('base', {}).get('repo', {}).get('full_name'),
        branch=github_pr.get('base', {}).get('ref')
    )
    # try to request the file
    request_configuration = requests.get(github_contents_api)
    data = {}
    # check if the status code is 200
    if request_configuration.status_code == 200:
        response = request_configuration.content
        data_response = json.loads(response)
        # get the file's download url and download it
        download_url = data_response.get('download_url')
        # create a temporary file
        tmp = tempfile.mkdtemp()
        destination = os.path.join(tmp, data_response.get('name', 'temp'))
        # and finaly download the file into it
        written = _download_file(download_url, destination)
        # if there is an actual downloaded file try to read the yaml
        if written:
            with open(destination, 'r') as file_read:
                data = yaml.load(file_read.read())
        # finaly delete the tempdirectory
        shutil.rmtree(tmp)
    return data
