import re
import requests
import operator
from flask import current_app, json, url_for


def check_1st_line(line):
    errors = []
    if len(line) > 50:
        errors.append('First line is too long')

    if ':' not in line:
        errors.append('Missing component name')
    else:
        component, msg = line.split(':', 1)
        if component not in current_app.config['COMPONENTS']:
            errors.append('Unknown "%s" component name' % (component, ))

    return errors


def check_signatures(lines):
    errors = []
    test = operator.methodcaller(
        'startswith',
        ('Signed-off-by: ', 'Tested-by: ', 'Reviewed-by:'))
    matching = filter(test, lines)
    if len(matching) == 0:
        errors.append('Signature missing')
    elif len(matching) <= 2:
        trusted = current_app.config['TRUSTED_DEVELOPERS']
        pattern = re.compile('|'.join(map(lambda x: '.*' + re.escape(x) + '.*',
                                          trusted)))
        if len(filter(None, map(pattern.match, matching))) == 0:
            errors.append('Needs more reviewers')

    return errors


def check_bullets(lines):
    errors = []
    if len(lines) <= 0:
        return errors

    for (i, line) in enumerate(lines[1:]):
        if line.startswith('*'):
            if lines[i].strip() != '':
                errors.append('Missing empty line before line %d' % (i+1, ))
            for (j, indented) in enumerate(lines[i+2:]):
                if indented.strip() == '':
                    break
                if not indented.startswith('  '):
                    errors.append('Wrong indentation on line %d' % (i+j+3, ))

        if len(line) > 72:
            errors.append('Line %d is too long' % (i+2, ))

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
                      headers=current_app.config['HEADERS'])
        errors += errs
    return errors


class Kwalitee(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, request):
        self.request = request
        if "X-GitHub-Event" in request.headers:
            event = request.headers["X-GitHub-Event"]
        else:
            raise ValueError("No X-Github-Event header found.")

        data = json.loads(request.data)
        fn = getattr(self, "on_{0}".format(event))

        return fn(data)

    def __getattr__(self, command):
        raise NotImplementedError("{0} is missing".format(command))

    def on_ping(self, data):
        return dict(message="Hi there!")

    def on_pull_request(self, data):
        errors = []
        state = 'failure'

        url = data['pull_request']['commits_url']
        errors = check_messages(url)
        state = 'error' if len(errors) > 0 else 'success'

        commit_sha = data['pull_request']['head']['sha']

        with current_app.open_instance_resource(
                'status_{sha}.txt'.format(sha=commit_sha), 'w+') as f:
            f.write('\n'.join(errors))

        body = dict(state=state,
                    target_url=url_for('status', commit_sha=commit_sha,
                                       _external=True),
                    description='\n'.join(errors)[:130])
        requests.post(data['pull_request']['statuses_url'],
                      data=json.dumps(body),
                      headers=current_app.config['HEADERS'])
        return body
