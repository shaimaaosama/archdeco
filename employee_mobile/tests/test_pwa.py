# -*- coding: utf-8 -*-
import os

from odoo.tests import HttpCase, tagged

from ..controllers.pwa import APP_DIR


@tagged('post_install', '-at_install')
class TestEmployeeAppPwa(HttpCase):

    def test_serves_app_with_no_cache(self):
        if not os.path.isfile(os.path.join(APP_DIR, 'index.html')):
            self.skipTest("PWA not built into static/app")
        resp = self.url_open('/employee-app/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/html', resp.headers['Content-Type'])
        self.assertEqual(resp.headers['Cache-Control'], 'no-cache')
        self.assertNotIn('Content-Security-Policy', resp.headers)
        manifest = self.url_open('/employee-app/manifest.json')
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(manifest.json()['short_name'], 'ArchDeco')

    def test_unknown_file_is_404(self):
        self.assertEqual(self.url_open('/employee-app/nope.js').status_code, 404)

    def test_cannot_escape_app_folder(self):
        for path in ('/employee-app/..%2F..%2F__manifest__.py',
                     '/employee-app/%2E%2E/%2E%2E/controllers/main.py'):
            resp = self.url_open(path)
            self.assertEqual(resp.status_code, 404, path)
            self.assertNotIn(b"'name'", resp.content)
