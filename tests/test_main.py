import os
import urllib.parse
from unittest.mock import patch

from vibora.tests import TestSuite, wrapper as asynctest

from rhender import config
from rhender.cd import cd
from rhender.main import app


class TestRender(TestSuite):
    repository_url = 'file://%s/examples' % os.path.dirname(__file__)
    encoded_url = urllib.parse.quote_plus(repository_url)

    def setup_class(cls):
        with cd('tests/examples'):
            os.system('git init')
            os.system('git add -A')
            os.system('git config --global user.email "you@example.com"')
            os.system('git config --global user.name "Your Name"')
            os.system('git commit -m "add files"')
        cls.client = app.test_client()

    def teardown_class(cls):
        with cd('tests/examples'):
            os.system('rm -rf .git')

    def teardown_method(self, method):
        os.system('rm -r /data/*')

    async def test_first_render(self):
        response = await self.client.post(
            '/v1/render',
            json={
                'repository_url': self.repository_url,
                'entry': 'template_partial.mustache',
                'data': {
                    'title': 'hello world',
                },
                'type': 'mustache',
            }
        )

        assert os.path.isdir(config.DATA_DIR + '/' + self.encoded_url)
        assert response.content.decode('utf-8') == \
            '<h1>hello world</h1>\nAgain, hello world!\n'

    # I haven't been able to get patching working...
    @asynctest
    @patch('rhender.main.os')
    async def test_multiple_renders(self, sys):
        json = {
            'repository_url': self.repository_url,
            'entry': 'template_partial.mustache',
            'data': {
                'title': 'hello world',
            },
            'type': 'mustache',
        }

        response = await self.client.post('/v1/render', json=json)
        assert response.content.decode('utf-8') == \
            '<h1>hello world</h1>\nAgain, hello world!\n'

        response = await self.client.post('/v1/render', json=json)
        assert response.content.decode('utf-8') == \
            '<h1>hello world</h1>\nAgain, hello world!\n'

    async def test_render_jinja(self):
        repository_url = 'file://%s/examples' % os.path.dirname(__file__)
        encoded_url = urllib.parse.quote_plus(repository_url)
        response = await self.client.post(
            '/v1/render',
            json={
                'repository_url': repository_url,
                'entry': 'index.html',
                'data': {
                    'title': 'hello world',
                },
                'type': 'jinja',
            }
        )

        assert os.path.isdir(config.DATA_DIR + '/' + encoded_url)
        # jinja trims whitespace(?), so there is no trailing \n
        assert response.content.decode('utf-8') == \
            '<h1>hello world</h1>\nAgain, hello world!'
