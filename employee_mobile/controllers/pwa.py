# -*- coding: utf-8 -*-
"""Serves the employee app's web build (a PWA) at ``/employee-app/``.

The Flutter web build lives in ``static/app`` (see ``tools/build_pwa.sh`` in
the Flutter project). Serving it from Odoo keeps the app on the same origin
as ``/api/mobile``, so the browser needs no CORS, and iPhone users can
"Add to Home Screen" from Safari without an App Store build.
"""
import os

from odoo import http
from odoo.http import Stream, request

APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'app')


class EmployeeAppPwa(http.Controller):

    @http.route(['/employee-app/', '/employee-app/<path:subpath>'], type='http', auth='public',
                methods=['GET'], csrf=False, readonly=True, sitemap=False)
    def employee_app(self, subpath='', **kwargs):
        root = os.path.realpath(APP_DIR)
        target = os.path.realpath(os.path.join(root, subpath or 'index.html'))
        # Never serve anything outside the app folder (e.g. "../models/...").
        if os.path.commonpath([root, target]) != root or not os.path.isfile(target):
            raise request.not_found()

        stream = Stream.from_path(target)
        # No long-lived caching: Flutter's file names are not content-hashed,
        # so browsers must revalidate (cheap 304s via the ETag) to pick up a
        # new version right after a module update.
        stream.max_age = 0
        response = stream.get_response(content_security_policy=None)
        response.headers['Cache-Control'] = 'no-cache'
        return response
