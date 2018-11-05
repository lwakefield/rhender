import os
import urllib.parse
import subprocess
import re
from base64 import b64encode, b64decode

from flask import Flask, jsonify, Response, request

from pystache import Renderer
from jinja2 import Environment, FileSystemLoader

from rhender import config
from rhender.cd import cd
from rhender.db import Project

app = Flask(__name__)


@app.route('/v1/render', methods=['POST'])
def render():
    body = request.json
    assert body is not None

    repository_url = body.get('repository_url')
    encoded_url = urllib.parse.quote_plus(repository_url)
    project_path = config.DATA_DIR + '/' + encoded_url

    # this is either the first time and we need to clone the repo, or it
    # is not the first time, and we should pull to make sure it is up to
    # date
    if not os.path.isdir(project_path):
        with cd(config.DATA_DIR):
            os.system('git clone %s %s' % (repository_url, encoded_url))
    else:
        with cd(project_path):
            os.system('git pull origin master')

    entry = body.get('entry')
    data = body.get('data')
    template_type = body.get('type')

    result = None
    if template_type == 'mustache':
        with cd(project_path):
            renderer = Renderer()
            result = renderer.render_path(entry, data)
    elif template_type == 'jinja':
        env = Environment(loader=FileSystemLoader(project_path))
        template = env.get_template(entry)
        result = template.render(**data)
    else:
        return Response(status=400)

    return Response(
        content=bytes(result, 'utf-8'),
        content_type='text/plain'
    )


@app.route('/v1/project/<project_id>/files', methods=['GET'])
def files(project_id):
    project = Project.find_or_fail(project_id)
    project.pull()
    paths = project.list_files()
    return JsonResponse(paths)


# TODO we want pattern matching to do this for us...
@app.route('/v1/project/<project_id>/files/.+', methods=['GET'])
def get_file(project_id, request):
    pattern = re.compile(b'/v1/project/[^/]+/files/(.+)')
    match = pattern.match(request.url)
    path = str(match.group(1), 'utf-8')

    project = Project.find_or_fail(project_id)
    project.pull()

    with open(project.local_path + '/' + path) as f:
        file_data = f.read()

    encoded_file_data = b64encode(bytes(file_data, 'utf-8'))

    return jsonify({'data': encoded_file_data})


# TODO we want pattern matching to do this for us...
@app.route('/v1/project/<project_id>/files/.+', methods=['PUT'])
def put_file(project_id, request):
    pattern = re.compile(b'/v1/project/[^/]+/files/(.+)')
    match = pattern.match(request.url)
    path = str(match.group(1), 'utf-8')

    body = request.json

    project = Project.find_or_fail(project_id)
    project.pull()

    if body.get('head_hash') != project.head_hash():
        return Response(status=409)

    filename = project.local_path + '/' + path
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w') as f:
        data = b64decode(body.get('data'))
        f.write(str(data, 'utf-8'))

    project.commit()

    import pdb; pdb.set_trace()

    # return new hash?
    return jsonify({'head_hash': project.head_hash()})
