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

import json
import operator
import os
import re
import requests

from flask import (Flask, request, jsonify, send_from_directory, url_for,
                   render_template)

app = Flask(__name__, template_folder='templates', static_folder='static',
            instance_relative_config=True)

# Load default configuration
app.config.from_object('invenio_kwalitee.config')

# Load invenio_kwalitee.cfg from instance folder
app.config.from_pyfile('invenio_kwalitee.cfg', silent=True)
app.config.from_envvar('INVENIO_KWALITEE_CONFIG', silent=True)

# Create instance path
try:
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
except Exception:
    pass


def check_1st_line(line):
    errors = []
    if len(line) > 50:
        errors.append('First line is too long')

    if ':' not in line:
        errors.append('Missing component name')
    else:
        component, msg = line.split(':', 1)
        if component not in app.config['COMPONENTS']:
            errors.append('Unknown "%s" component name' % (component, ))

    return errors


def check_signatures(lines):
    errors = []
    test = operator.methodcaller(
        'startswith',
        tuple(['Signed-off-by: ', 'Tested-by: ', 'Reviewed-by:']))
    matching = filter(test, lines)
    if len(matching) == 0:
        errors.append('Signature missing')
    elif len(matching) <= 2:
        pattern = re.compile('|'.join(map(re.escape,
                                          app.config['TRUSTED_DEVELOPERS'])))
        if len(map(pattern.match, matching)) == 0:
            errors.append('Needs more reviewers')

    return errors


def check_bullets(lines):
    errors = []
    if len(lines) <= 0:
        return errors

    for (i, line) in enumerate(lines[1:]):
        if line.startswith('*'):
            if lines[i].strip() != '':
                errors.append('Missing empty line before %d' % (i, ))

    return errors


def check_messages(url):
    resp = requests.get(url)
    data = json.loads(resp.content)
    errors = []
    for m in data:
        csha = m['sha']
        lines = m['commit']['message'].split('\n')
        errs = map(lambda x: '%s: %s' % (csha, x),
                   check_1st_line(lines[0]) +
                   check_signatures(lines) +
                   check_bullets(lines))
        body = {'body': '\n'.join(errs)}
        requests.post(m['comments_url'],
                      data=json.dumps(body),
                      headers=app.config['HEADERS'])
        errors += errs
    return errors


@app.route('/status/<commit_sha>')
def status(commit_sha):
    with app.open_instance_resource(
            'status_{sha}.txt'.format(sha=commit_sha), 'r') as f:
        status = f.read()
    status = status if len(status) > 0 else commit_sha + ': Everything OK'
    return render_template('status.html', status=status)


@app.route('/', methods=['GET'])
def index():
    key = lambda x: os.path.getctime(os.path.join(app.instance_path, x))
    test = operator.methodcaller('startswith', 'status_')
    files = map(lambda x: x[7:-4], filter(test, sorted(
        os.listdir(app.instance_path), key=key, reverse=True)))
    return render_template('index.html', files=files)


@app.route('/payload', methods=['POST'])
def payload():
    errors = []
    state = 'failure'
    try:
        data = json.loads(request.data)
        url = data['pull_request']['commits_url']
        errors = check_messages(url)
        state = 'error' if len(errors) > 0 else 'success'
    except Exception as e:
        import traceback
        traceback.print_exc()
        errors = [str(e)]

    commit_sha = data['pull_request']['head']['sha']

    with app.open_instance_resource(
            'status_{sha}.txt'.format(sha=commit_sha), 'w+') as f:
        f.write('\n'.join(errors))

    body = dict(state=state,
                target_url=url_for('status', commit_sha=commit_sha, _external=True),
                description='\n'.join(errors)[:130])
    requests.post(data['pull_request']['statuses_url'],
                  data=json.dumps(body),
                  headers=app.config['HEADERS'])
    return jsonify(payload=body)


def main():
    app.run(debug=True)
