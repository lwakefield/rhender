import os
import urllib.parse
from unittest.mock import patch
import pytest

from vibora.tests import TestSuite

from rhender import config
from rhender.cd import cd
from rhender.main import app
from rhender.db import Project


class TestRender(TestSuite):
    repository_url = 'file://%s/examples' % os.path.dirname(__file__)
    encoded_url = urllib.parse.quote_plus(repository_url)

    def setup_class(cls):
        with cd('tests/examples'):
            os.system('git init')
            os.system('git add *.html *.mustache')
            os.system('git config --global user.email "you@example.com"')
            os.system('git config --global user.name "Your Name"')
            os.system('git commit -m "add files"')
        cls.client = app.test_client()

    def teardown_class(cls):
        with cd('tests/examples'):
            os.system('rm -rf .git')

    def setup_method(self, method):
        self.test_project = Project()
        self.test_project.name = 'example project'
        self.test_project.repository_url = self.repository_url
        self.test_project.save()

    def teardown_method(self, method):
        os.system('rm -rf /data/*')
        self.test_project.delete()
        self.test_project = None

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

    async def test_multiple_renders(self):
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
                'repository_url': self.repository_url,
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

    async def test_get_files(self):
        response = await self.client.get('/v1/project/%s/files' % self.test_project.id)
        assert response.json() == [
            'child.html',
            'index.html',
            'inner_partial.mustache',
            'template_partial.mustache'
        ]
        # response = await self.client.post(
        #     '/v1/render',
        #     json={
        #         'repository_url': repository_url,
        #         'entry': 'index.html',
        #         'data': {
        #             'title': 'hello world',
        #         },
        #         'type': 'jinja',
        #     }
        # )

        # assert os.path.isdir(config.DATA_DIR + '/' + encoded_url)
        # # jinja trims whitespace(?), so there is no trailing \n
        # assert response.content.decode('utf-8') == \
        #     '<h1>hello world</h1>\nAgain, hello world!'


