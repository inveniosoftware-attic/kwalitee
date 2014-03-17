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
import operator

from flask import Flask, jsonify, render_template, request, make_response

from .kwalitee import Kwalitee

app = Flask(__name__, template_folder='templates', static_folder='static',
            instance_relative_config=True)

# Load default configuration
app.config.from_object('invenio_kwalitee.config')

# Load invenio_kwalitee.cfg from instance folder
app.config.from_pyfile('invenio_kwalitee.cfg', silent=True)
app.config.from_envvar('INVENIO_KWALITEE_CONFIG', silent=True)

# Create kwalitee instance
kw = Kwalitee()

# Create instance path
try:
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
except Exception:
    pass


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
    try:
        return jsonify(payload=kw(request))
    except Exception as e:
        import traceback
        return make_response(jsonify(status="failure",
                                     stacktrace=traceback.format_exc(),
                                     exception=str(e)),
                             500)


def main():
    app.run(debug=True)
