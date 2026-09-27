# -*- coding: utf-8 -*-

import json
import logging

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class HrHubFaceIoWebhookController(http.Controller):

    _DEFAULT_WEBHOOK_TOKEN = "9270a7367905bacc8512ad54653fd9de"

    def _json_response(self, payload, status=200):
        return Response(
            response=json.dumps(payload),
            status=status,
            headers=[("Content-Type", "application/json")],
        )

    def _get_expected_token(self):
        token = request.env["ir.config_parameter"].sudo().get_param(
            "pt_hr_hub_server.faceio_webhook_token"
        )
        return token or self._DEFAULT_WEBHOOK_TOKEN

    def _get_bearer_token(self):
        headers = request.httprequest.headers
        for header_name in ("WWW-Authenticate", "Authorization"):
            header_value = headers.get(header_name)
            if not header_value:
                continue
            scheme, separator, token = header_value.partition(" ")
            if separator and scheme.lower() == "bearer" and token:
                return token.strip()
        return False

    @http.route(
        "/hr_hub/faceio/webhook",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def faceio_webhook(self, **kwargs):
        bearer_token = self._get_bearer_token()
        expected_token = self._get_expected_token()

        if not bearer_token or bearer_token != expected_token:
            _logger.warning(
                "Rejected FACEIO webhook: invalid bearer token from %s",
                request.httprequest.remote_addr,
            )
            return self._json_response({
                "success": False,
                "error": "invalid_token",
                "message": "Invalid FACEIO webhook token.",
            }, status=401)

        raw_body = request.httprequest.get_data(cache=False, as_text=True) or "{}"
        try:
            payload = json.loads(raw_body)
        except ValueError:
            return self._json_response({
                "success": False,
                "error": "invalid_json",
                "message": "Request body must be valid JSON.",
            }, status=400)

        if not isinstance(payload, dict):
            return self._json_response({
                "success": False,
                "error": "invalid_payload",
                "message": "FACEIO webhook payload must be a JSON object.",
            }, status=400)

        event_name = payload.get("event") or payload.get("type") or payload.get("action") or "unknown"
        facial_id = (
            payload.get("facialId")
            or payload.get("faceio_id")
            or payload.get("faceioId")
            or payload.get("id")
        )

        _logger.info(
            "FACEIO webhook received: event=%s facial_id=%s payload=%s",
            event_name,
            facial_id,
            payload,
        )

        return self._json_response({
            "success": True,
            "message": "FACEIO webhook received.",
            "event": event_name,
            "facial_id": facial_id,
        })