import os
import urllib.parse
import subprocess
from base64 import b64encode, b64decode

from vibora import Vibora, Request
from vibora.responses import JsonResponse, Response
from werkzeug._reloader import run_with_reloader
from pystache import Renderer
from jinja2 import Environment, FileSystemLoader

from rhender import config
from rhender.cd import cd
from rhender.db import Project

app = Vibora()


@app.route('/v1/render', methods=['POST'])
async def render(request: Request):
    body = await request.json()
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
        headers={
            'Content-Type': 'text/plain'
        }
    )


@app.route('/v1/project/<project_id>/files', methods=['GET'])
async def files(project_id: int):
    project = Project.find_or_fail(project_id)
    project.pull()
    paths = project.list_files()
    return JsonResponse(paths)


@app.route('v1/repo/<project_id>/files/<path>', methods=['GET'])
async def file(project_id: int, path: str):
    project = Project.find_or_fail(project_id)
    project.pull()

    with open(project.local_path + '/' + path) as f:
        file_data = f.read()

    encoded_file_data = str(b64encode(file_data), 'utf-8')

    return JsonResponse({'data': encoded_file_data})


@app.route('v1/repo/<project_id>/files/<path>', methods=['PUT'])
async def write_file(project_id: int, path: str, request):
    body = await request.json()

    project = Project.find_or_fail(project_id)
    project.pull()

    if body.get('head_hash') != project.head_hash():
        return Response(status=409)

    filename = project.local_path + '/' + path
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w') as f:
        data = b64decode(body.get('data'), 'utf-8')
        f.write(data)

    project.commit()

    # return new hash?
    return JsonResponse({'head_hash': project.head_hash()})

if __name__ == '__main__':
    def run():
        app.run(debug=config.DEBUG, host='0.0.0.0', port=config.PORT)

    run_with_reloader(run)
