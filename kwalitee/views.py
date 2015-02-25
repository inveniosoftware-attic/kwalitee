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

"""Views like in MTV."""

from __future__ import unicode_literals

import requests
from flask import (current_app, render_template, make_response, json, jsonify,
                   request, url_for)
from werkzeug.exceptions import NotFound

from .tasks import pull_request, push, get_headers
from .models import db, Account, BranchStatus, CommitStatus, Repository


def status(sha):
    """Show the status of a commit.

    **deprecated** static files aren't used anymore. To be removed at some
    point.

    :param sha: identifier of a commit.
    """
    try:
        with current_app.open_instance_resource(
                "status_{sha}.txt".format(sha=sha), "r") as f:
            status = f.read()
    except IOError:
        raise NotFound("{sha} was not found.".format(sha=sha))

    status = status if len(status) > 0 else sha + ": Everything OK"
    return render_template("status.html", status=status)


def index():
    """Homepage that lists the accounts."""
    accounts = Account.query.order_by(db.asc(Account.name)).all()
    return render_template("index.html", accounts=accounts)


def account(account):
    """Display the repositories linked with one account.

    :param account: name of the account
    """
    acc = _get_account(account)
    return render_template("account.html",
                           account=acc,
                           repositories=acc.repositories)


def repository(account, repository, limit=50):
    """Display the recents commits and branches of a repository.

    :param account: name of the owner
    :param repository: name of the repository
    :param limit: size of the commit window
    """
    acc = _get_account(account)
    repo = _get_repository(acc, repository)
    commits = CommitStatus.query \
                          .filter_by(repository_id=repo.id) \
                          .order_by(db.desc(CommitStatus.id)) \
                          .limit(limit)
    return render_template("repository.html",
                           account=acc,
                           repository=repo,
                           commits=commits)


def commit(account, repository, sha):
    """Display the status of a commit.

    :param account: name of the owner
    :param repository: name of the repository
    :param sha: identifier of the commit
    """
    acc = _get_account(account)
    repo = _get_repository(acc, repository)
    commit = CommitStatus.query.filter_by(repository_id=repo.id,
                                          sha=sha).first_or_404()
    return render_template("commit.html",
                           account=acc,
                           repository=repo,
                           commit=commit)


def branch(account, repository, branch):
    """Display the statuses of a branch.

    :param account: name of the owner
    :param repository: name of the repository
    :param branch: name of the branch
    """
    acc = _get_account(account)
    repo = _get_repository(acc, repository)
    all = BranchStatus.query.join(BranchStatus.commit) \
                            .filter(CommitStatus.repository_id == repo.id) \
                            .filter(BranchStatus.name == branch) \
                            .all()

    if not all:
        raise NotFound("{0.fullname} as no branches called {1}"
                       .format(repo, branch))

    return render_template("branches.html",
                           account=acc,
                           repository=repo,
                           branches=all)


def branch_status(account, repository, branch, sha):
    """Display the status of a pull request.

    :param account: name of the owner
    :param repository: name of the repository
    :param branch: name of the branch
    :param sha: commit identifier of the commit related with the branch
    """
    acc = _get_account(account)
    repo = _get_repository(acc, repository)
    branch = BranchStatus.query.join(BranchStatus.commit) \
                               .filter(CommitStatus.repository_id == repo.id) \
                               .filter(CommitStatus.sha == sha) \
                               .filter(BranchStatus.name == branch) \
                               .first_or_404()

    return render_template("branch.html",
                           account=acc,
                           repository=repo,
                           branch=branch,
                           commit=branch.commit)


def payload():
    """Handle the GitHub events.

    .. seealso::

        `Event Types <https://developer.github.com/v3/activity/events/types/>`
    """
    q = current_app.config["queue"]
    events = ["push", "pull_request"]
    try:
        event = None
        if "X-GitHub-Event" in request.headers:
            event = request.headers["X-GitHub-Event"]
        else:
            raise ValueError("No X-GitHub-Event HTTP header found")

        if event == "ping":
            payload = {"message": "pong"}
        elif event in events:
            config = dict(current_app.config)
            config.pop("queue")
            timeout = config.pop("WORKER_TIMEOUT", None)
            auto_create = config.pop("AUTO_CREATE", False)

            data = json.loads(request.data)

            repository_name = data["repository"]["name"]
            keyname = "name" if event == "push" else "login"
            owner_name = data["repository"]["owner"][keyname]

            payload = {
                "state": "pending",
                "context": config.get("CONTEXT")
            }

            owner = Account.query.filter_by(name=owner_name).first()
            if owner:
                repository = Repository.query.filter_by(
                    name=repository_name,
                    owner_id=owner.id).first()

            if not owner or not repository:
                if auto_create:
                    owner = Account.find_or_create(owner_name)
                    repository = Repository.find_or_create(owner,
                                                           repository_name)
                else:
                    payload["state"] = "error"
                    payload["description"] = "{0}/{1} is not yet registered" \
                                             .format(owner_name,
                                                     repository_name)

            if owner and repository:
                if event == "push":
                    status_url = ""
                    commit_url = "https://api.github.com/repos/{owner}" \
                                 "/{repo}/commits/{sha}"
                    for commit in data["commits"]:
                        cs = CommitStatus.find_or_create(repository,
                                                         commit["id"],
                                                         commit["url"])

                        status_url = url_for("commit",
                                             account=owner.name,
                                             repository=repository.name,
                                             sha=cs.sha,
                                             _external=True)

                        url = commit_url.format(
                            commit_url,
                            owner=owner.name,
                            repo=repository.name,
                            sha=cs.sha)

                        q.enqueue(push, cs.id, url, status_url, config,
                                  timeout=timeout)

                    payload["target_url"] = status_url
                    payload["description"] = "commits queues"

                elif event == "pull_request":
                    if data["action"] not in ["synchronize", "opened",
                                              "reopened"]:
                        raise ValueError(
                            "Pull request action {0} is not supported"
                            .format(data["action"]))
                    repo = data["repository"]
                    data = data["pull_request"]
                    pull_request_url = data["url"]
                    commit_sha = data["head"]["sha"]
                    commits = []
                    headers = get_headers(Repository.query.filter_by(
                        name=repo["name"]).first(), config)
                    response = requests.get(data["commits_url"],
                                            headers=headers)
                    response.raise_for_status()  # check API rate limit
                    response_json = json.loads(response.content)
                    for commit in response_json:
                        cstat = CommitStatus.find_or_create(repository,
                                                            commit["sha"],
                                                            commit["html_url"])
                        commits.append(cstat)

                    bs = BranchStatus.find_or_create(commits[-1],
                                                     data["head"]["label"],
                                                     data["html_url"],
                                                     {"commits": commits})
                    status_url = url_for("branch_status",
                                         account=owner.name,
                                         repository=repository.name,
                                         branch=bs.name,
                                         sha=commit_sha,
                                         _external=True)

                    q.enqueue(pull_request, bs.id, pull_request_url,
                              status_url, config, timeout=timeout)

                    payload["target_url"] = status_url
                    payload["description"] = "pull request {0} queued" \
                                             .format(bs.name)
        else:
            raise ValueError("Event {0} is not supported".format(event))

        return jsonify(payload=payload)
    except Exception as e:
        import traceback
        # Uncomment to help you debugging the tests
        # raise e
        return make_response(jsonify(status="failure",
                                     stacktrace=traceback.format_exc(),
                                     exception=str(e)),
                             500)


def _get_account(account_name):
    """Get the account by name.

    :param account_name: name of the account
    :raise NotFound: if the account cannot be found
    """
    account = Account.query.filter_by(name=account_name).first()
    if not account:
        raise NotFound("{0} isn't registered yet.".format(account_name))
    return account


def _get_repository(account, repository_name):
    """Get the repository by name.

    :param account: account
    :param repository_name: name of the repository
    :raise NotFound: if the repository cannot be found
    """
    repository = Repository.query.filter_by(owner_id=account.id,
                                            name=repository_name).first()
    if not repository:
        raise NotFound("{0}/{1} isn't registered yet.".format(account.name,
                                                              repository_name))
    return repository
