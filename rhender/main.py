import os
import urllib.parse

from vibora import Vibora, Request
from vibora.responses import JsonResponse, Response
from werkzeug._reloader import run_with_reloader
from pystache import Renderer
from jinja2 import Environment, FileSystemLoader

from rhender.config import Config
from rhender.cd import cd

app = Vibora()


@app.route('/')
async def home(request: Request):
    return JsonResponse({'hello': 'world'})


@app.route('/v1/render', methods=['POST'])
async def render(request: Request):
    body = await request.json()
    repository_url = body.get('repository_url')
    encoded_url = urllib.parse.quote_plus(repository_url)
    project_path = Config.DATA_DIR + '/' + encoded_url

    # this is either the first time and we need to clone the repo, or it
    # is not the first time, and we should pull to make sure it is up to
    # date
    if not os.path.isdir(project_path):
        with cd(Config.DATA_DIR):
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





if __name__ == '__main__':
    def run():
        app.run(debug=Config.DEBUG, host='0.0.0.0', port=Config.PORT)

    run_with_reloader(run)
