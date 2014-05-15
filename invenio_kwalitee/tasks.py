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

"""Tasks to run on the worker."""

from __future__ import unicode_literals

import os
import re
import shutil
import logging
import tempfile
import requests
from flask import json

from . import db
from .kwalitee import get_options, check_message, check_file
from .models import Repository, BranchStatus, CommitStatus

# Worker logger
LOGGER = logging.getLogger("rq.worker")


def push(commit_url, status_url, config):
    """Performing all the tests on the commit.

    :param commit_url: github api commit url
    :param config: configuration dictionary

    """
    body = {}
    errors = {"message": [], "files": []}
    length = 0

    repository = Repository.query.filter_by(id=config["repository"]).first()

    options = get_options(config)
    headers = {
        "Content-Type": "application/json",
        # This is required to post comments on GitHub on yours behalf.
        # Please update your configuration accordingly.
        "Authorization": "token {0}".format(config["ACCESS_TOKEN"])
    }

    check_commit_messages = config.get("CHECK_COMMIT_MESSAGES", True)
    check_pep8 = options["pep8"]
    check_pep257 = options["pep257"]
    check_license = options["license"]
    check_files = check_pep8 or check_pep257 or check_license

    commit = requests.get(commit_url)
    data = json.loads(commit.content)

    # FIXME guessing the status URL based on the commit one.
    statuses_url = data["url"].replace("commits", "statuses")
    comments_url = data["comments_url"]
    sha = data["sha"]
    files = data["files"]

    commit_status = CommitStatus.query.filter_by(
        repository_id=repository.id,
        sha=sha).first()

    # This commit might have been checked in a pull request, which skipped
    # the files check.
    is_new = False
    checked = False
    if not commit_status or commit_status.content["files"] is None:
        is_new = True

    if not commit_status and check_commit_messages:
        errs, commit_status = _check_commit(repository, data, **options)
        checked = True

    errors = commit_status.content

    if is_new and check_files:
        tmp = tempfile.mkdtemp()
        filenames = _download_files_from_commit(files, sha, tmp)
        errs, messages = _check_files(filenames, tmp, **options)
        shutil.rmtree(tmp)

        errors["files"] = errs
        length += len(errs)

        if len(errs):
            _post_file_comments(comments_url, messages, headers)

    db.session.add(commit_status)
    db.session.commit()

    if checked and length:
        body = "\n".join(errors["message"])
        try:
            requests.post(comments_url,
                          data=json.dumps(dict(body=body.strip())),
                          headers=headers)
        except requests.RequestException:
            LOGGER.exception(comments_url)

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


def pull_request(pull_request_url, status_url, config):
    """Performing all the tests on the pull request.

    Then pings back the given status_url and update the issue labels.

    :param pull_request_url: github api pull request
    :param status_url: github api status url
    :param config: configuration dictionary
    :return: status body and applied labels
    """
    errors = {"message": [], "commits": [], "files": []}
    length = 0

    repository = Repository.query.filter_by(id=config["repository"]).first()

    pull_request = requests.get(pull_request_url)
    data = json.loads(pull_request.content)

    options = get_options(config)
    headers = {
        "Content-Type": "application/json",
        # This is required to post comments on GitHub on your behalf.
        # Please update your configuration accordingly.
        "Authorization": "token {0}".format(config["ACCESS_TOKEN"])
    }

    commit_sha = data["head"]["sha"]
    issue_url = data["issue_url"]
    commits_url = data["commits_url"]
    files_url = data["commits_url"].replace("/commits", "/files")
    review_comments_url = data["review_comments_url"]

    # Find existing BranchStatus
    commits = CommitStatus.query.filter_by(repository_id=repository.id,
                                           sha=commit_sha).all()

    bs = None
    if len(commits):
        bs = BranchStatus.query.filter(
            BranchStatus.commit_id.in_([c.id for c in commits]),
            BranchStatus.name == data["head"]["label"]
        ).first()

    if bs:
        return "Known branch {0.name} skipped".format(bs)

    # Check only if the title does not contain 'wip'.
    is_wip = bool(re.match(r"\bwip\b", data["title"], re.IGNORECASE))
    check = config.get("CHECK_WIP", False) or not is_wip
    options["CHECK"] = check

    check_pep8 = options["pep8"]
    check_pep257 = options["pep257"]
    check_license = options["license"]
    check_files = check_pep8 or check_pep257 or check_license

    labels, labels_url = _get_issue_labels(issue_url)
    labels.discard(config.get("LABEL_WIP", "in_work"))
    labels.discard(config.get("LABEL_REVIEW", "in_review"))
    labels.discard(config.get("LABEL_READY", "in_integration"))
    new_labels = set([])

    # Checking commits
    errs, new_labels, messages = _check_commits(repository,
                                                commits_url,
                                                **options)
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
        errs, messages = _check_files(filenames, tmp, **options)
        shutil.rmtree(tmp)

        errors["files"] += errs
        length += len(errs)

        if len(errs):
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

    branch_status = BranchStatus(errors["commits"][0],
                                 data["head"]["label"],
                                 data["html_url"],
                                 errors)
    db.session.add(branch_status)
    db.session.commit()

    if is_wip:
        new_labels = set([config.get("LABEL_WIP", "in_work")])
    if not new_labels:
        if length == 0:
            new_labels = set([config.get("LABEL_READY", "in_integration")])
        else:
            new_labels = set([config.get("LABEL_REVIEW", "in_review")])

    labels.update(new_labels)
    try:
        requests.put(labels_url.replace("{/name}", ""),
                     data=json.dumps(list(labels)),
                     headers=headers)
    except requests.RequestException:
        LOGGER.exception(labels_url)

    return dict(errors, labels=list(labels))


def _post_file_comments(comments_url, messages, headers):
    """Post comment on each file."""
    for msg in messages:
        body = "\n".join(msg["errors"])
        if body is not "":
            # Comment on first line.
            position = 0
            try:
                requests.post(comments_url,
                              data=json.dumps(dict(body=body,
                                                   commit_id=msg["sha"],
                                                   path=msg["path"],
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
        filename = f["filename"]

        _download_file(f["raw_url"], os.path.join(tmp, filename))

        yield (sha, filename)


def _download_file(source, destination):
    """Download the given file and puts it at the desired place."""
    try:
        response = requests.get(source)

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


def _check_commit(repository, commit, **kwargs):
    """Check one commit message."""
    errs = None
    sha = commit["sha"]
    url = commit["html_url"]
    commit_status = CommitStatus.find_or_create(repository, sha, url)

    if commit_status.id:
        errs = commit_status.content["message"]
    else:
        errs = check_message(commit["commit"]["message"], **kwargs)
        commit_status.content = dict(commit_status.content,
                                     **{"message": errs})

    return errs, commit_status


def _check_commits(repository, url, **kwargs):
    """Check the commit messages of a pull request."""
    errors = []
    messages = []
    labels = set()

    check = kwargs.get("CHECK")
    check_commit_messages = kwargs.get("CHECK_COMMIT_MESSAGES", True)

    response = requests.get(url)
    commits = json.loads(response.content)
    for commit in reversed(commits):
        errs = []
        commit_status = None
        sha = commit["sha"]
        url = commit["html_url"]

        if check and check_commit_messages:
            errs, commit_status = _check_commit(repository, commit, **kwargs)
        else:
            commit_status = CommitStatus.find_or_create(repository, sha, url)

        # filter out the needs more reviewerss
        e = list(filter(lambda x: not x.startswith("M100:"), errs))

        if len(errs) > len(e):
            labels.add(kwargs.get("LABEL_REVIEW", "in_review"))

        messages.append({
            "sha": sha,
            "status": commit_status,
            "comments_url": commit["comments_url"],
            "errors": {"message": e,
                       "files": {}}
        })
        errors += list(map(lambda x: "{0}: {1}".format(sha, x), errs))
    return errors, labels, messages


def _check_files(files, tmp, **kwargs):
    """Download and runs the checks on the files of a pull request."""
    errors = []
    messages = []

    for sha, filename in files:
        path = os.path.join(tmp, filename)
        errs = check_file(path, **kwargs)

        messages.append({
            "path": filename,
            "sha": sha,
            "errors": errs
        })

        errors += list(map(lambda x: "{0}: {1}:{2}"
                                     .format(sha, filename, x),
                           errs))
    return errors, messages
