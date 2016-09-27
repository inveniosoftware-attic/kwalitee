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

"""Prepare release news from git log.

Prepares release news from git log messages, breaking release news
into (1) sections (e.g. Security fixes, detected from commit labels)
and (2) modules (e.g. search, detected from commit log headlines).
"""

from __future__ import absolute_import, print_function

import itertools
import re
import sys
import textwrap
from collections import OrderedDict

import click

from .check import Repo, pass_repo


@click.group()
@click.option('-r', '--repository', envvar='KWALITEE_REPO', default='.')
@click.pass_context
def prepare(ctx, repository):
    """Assist with release process."""
    ctx.obj = Repo(repository=repository)


def analyse_body_paragraph(body_paragraph, labels=None):
    """Analyse commit body paragraph and return (label, message).

    >>> analyse_body_paragraph('* BETTER Foo and bar.',
    >>> ... {'BETTER': 'Improvements'})
    ('BETTER', 'Foo and bar.')
    >>> analyse_body_paragraph('* Foo and bar.')
    (None, 'Foo and bar.')
    >>> analyse_body_paragraph('Foo and bar.')
    (None, None)
    """
    # try to find leading label first:
    for label, dummy in labels:
        if body_paragraph.startswith('* ' + label):
            return (label, body_paragraph[len(label) + 3:].replace('\n  ',
                                                                   ' '))
    # no conformed leading label found; do we have leading asterisk?
    if body_paragraph.startswith('* '):
        return (None, body_paragraph[2:].replace('\n  ', ' '))
    # no leading asterisk found; ignore this paragraph silently:
    return (None, None)


def remove_ticket_directives(message):
    """Remove ticket directives like "(closes #123).

    >>> remove_ticket_directives('(closes #123)')
    '(#123)'
    >>> remove_ticket_directives('(foo #123)')
    '(foo #123)'
    """
    if message:
        message = re.sub(r'closes #', '#', message)
        message = re.sub(r'addresses #', '#', message)
        message = re.sub(r'references #', '#', message)
    return message


def amended_commits(commits):
    """Return those git commit sha1s that have been amended later."""
    # which SHA1 are declared as amended later?
    amended_sha1s = []
    for message in commits.values():
        amended_sha1s.extend(re.findall(r'AMENDS\s([0-f]+)', message))
    return amended_sha1s


def enrich_git_log_dict(messages, labels):
    """Enrich git log with related information on tickets."""
    for commit_sha1, message in messages.items():
        # detect module and ticket numbers for each commit:
        component = None
        title = message.split('\n')[0]
        try:
            component, title = title.split(":", 1)
            component = component.strip()
        except ValueError:
            pass  # noqa

        paragraphs = [analyse_body_paragraph(p, labels)
                      for p in message.split('\n\n')]
        yield {
            'sha1': commit_sha1,
            'component': component,
            'title': title.strip(),
            'tickets': re.findall(r'\s(#\d+)', message),
            'paragraphs': [
                (label, remove_ticket_directives(message))
                for label, message in paragraphs
            ],
        }


@prepare.command()
@click.argument('commit', metavar='<sha or branch>',
                default='HEAD')  # , help='an integer for the accumulator')
@click.option('-c', '--components', is_flag=True, help='group components')
@pass_repo
def release(obj, commit='HEAD', components=False):
    """Generate release notes."""
    options = obj.options
    repository = obj.repository
    commits = list(obj.iter_commits(commit))
    sha = obj.sha

    messages = OrderedDict([(getattr(c, sha), c.message) for c in commits])

    for commit_sha1 in amended_commits(messages):
        if commit_sha1 in messages:
            del messages[commit_sha1]

    full_messages = list(
        enrich_git_log_dict(messages, options.get('commit_msg_labels'))
    )
    indent = '  ' if components else ''
    wrapper = textwrap.TextWrapper(
        width=70,
        initial_indent=indent + '- ',
        subsequent_indent=indent + '  ',
    )

    for label, section in options.get('commit_msg_labels'):
        if section is None:
            continue
        bullets = []
        for commit in full_messages:
            bullets += [
                {'text': bullet, 'component': commit['component']}
                for lbl, bullet in commit['paragraphs']
                if lbl == label and bullet is not None
            ]
        if len(bullets) > 0:
            click.echo(section)
            click.echo('~' * len(section))
            click.echo()
            if components:
                def key(cmt):
                    return cmt['component']

                for component, bullets in itertools.groupby(
                        sorted(bullets, key=key), key):
                    bullets = list(bullets)
                    if len(bullets) > 0:
                        click.echo('+ {}'.format(component))
                        click.echo()
                    for bullet in bullets:
                        click.echo(wrapper.fill(bullet['text']))
                    click.echo()
            else:
                for bullet in bullets:
                    click.echo(wrapper.fill(bullet['text']))
            click.echo()

    return 0
