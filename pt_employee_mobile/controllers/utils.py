# -*- coding: utf-8 -*-
import functools
import hashlib
import json
import logging
import math
from datetime import timedelta

import psycopg2
import pytz

from odoo import _, fields
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY, PG_CONCURRENCY_EXCEPTIONS_TO_RETRY

from ..exceptions import MobileApiError

_logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6371000.0


# --------------------------------------------------------------------------
# Envelope helpers
# --------------------------------------------------------------------------

def success_envelope(data):
    return {'success': True, 'data': data}


def error_envelope(code, message, details=None):
    error = {'code': code, 'message': message}
    if details:
        error['details'] = details
    return {'success': False, 'error': error}


# --------------------------------------------------------------------------
# Misc helpers
# --------------------------------------------------------------------------

def haversine_distance(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres between two WGS84 lat/lon points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    a = min(1.0, max(0.0, a))
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def get_json_body():
    """Parse the raw JSON request body into a dict (never raises on empty body)."""
    raw = request.httprequest.get_data(as_text=True) or '{}'
    try:
        data = json.loads(raw)
    except ValueError:
        raise MobileApiError('VALIDATION_ERROR', 400, _("The request body is not valid JSON."))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise MobileApiError('VALIDATION_ERROR', 400, _("The request body must be a JSON object."))
    return data


def to_employee_iso(dt, employee):
    """Format a naive UTC datetime as ISO-8601 in the employee's timezone, with offset."""
    if not dt:
        return None
    tz = pytz.timezone(employee._get_tz() or 'UTC')
    if not dt.tzinfo:
        dt = pytz.utc.localize(dt)
    local_dt = dt.astimezone(tz).replace(microsecond=0)
    return local_dt.isoformat()


def resolve_lang(env):
    """Resolve the request's language (``?lang=`` then ``Accept-Language``) to an
    installed res.lang code. ``ar`` -> first active ``ar_*``. ``ur`` -> ``ur_PK`` if
    active, else English. Anything else (including plain ``en``) -> ``en_US``.
    """
    requested = (request.params.get('lang') or '').strip().lower()
    if not requested:
        accept = request.httprequest.headers.get('Accept-Language', '') or ''
        requested = accept.split(',')[0].split('-')[0].split(';')[0].strip().lower()

    Lang = env['res.lang'].sudo()
    if requested == 'ar':
        lang = Lang.search([('code', 'like', 'ar\\_%'), ('active', '=', True)], limit=1)
        if lang:
            return lang.code
    elif requested == 'ur':
        lang = Lang.search([('code', '=', 'ur_PK'), ('active', '=', True)], limit=1)
        if lang:
            return lang.code
    return 'en_US'


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------

def _authenticate(env):
    """Validate the ``Authorization: Bearer <token>`` header.

    :returns: ``(employee, token_record)`` — ``employee`` is sudo()'d and switched
        to its own company. Raises :class:`MobileApiError` on any failure.
    """
    auth_header = request.httprequest.headers.get('Authorization', '') or ''
    if not auth_header.startswith('Bearer '):
        raise MobileApiError('TOKEN_MISSING', 401, _("Authentication token is missing."))
    token = auth_header[len('Bearer '):].strip()
    if not token:
        raise MobileApiError('TOKEN_MISSING', 401, _("Authentication token is missing."))

    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    Token = env['hr.employee.mobile.token'].sudo()
    token_rec = Token.search([('token_hash', '=', token_hash), ('active', '=', True)], limit=1)

    now = fields.Datetime.now()
    if not token_rec or not token_rec.expires_at or token_rec.expires_at < now:
        raise MobileApiError('TOKEN_INVALID', 401, _("Your session has expired. Please sign in again."))

    employee = token_rec.employee_id.sudo()
    if not employee.exists() or not employee.active:
        raise MobileApiError('TOKEN_INVALID', 401, _("Your session is no longer valid. Please sign in again."))
    if not employee.mobile_app_access:
        raise MobileApiError('ACCESS_DISABLED', 403, _("Your mobile app access has been disabled. Contact HR."))

    # Slide the expiry and bump last_used, but at most once per hour to avoid a
    # write on every single request.
    if not token_rec.last_used or (now - token_rec.last_used) >= timedelta(hours=1):
        validity_days = int(env['ir.config_parameter'].sudo().get_param(
            'pt_employee_mobile.token_validity_days', 30))
        token_rec.write({
            'last_used': now,
            'expires_at': now + timedelta(days=validity_days),
        })

    employee = employee.with_company(employee.company_id)
    return employee, token_rec


# --------------------------------------------------------------------------
# The route decorator
# --------------------------------------------------------------------------

def mobile_endpoint(auth_required=True):
    """Wrap a controller method to: resolve the request language, optionally
    authenticate the Bearer token (passing ``employee``/``token`` kwargs to the
    handler), and turn any error into the mobile API's JSON error envelope.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped(self, *args, **kwargs):
            env = request.env
            try:
                lang_code = resolve_lang(env)
                request.update_context(lang=lang_code)

                if auth_required:
                    employee, token = _authenticate(request.env)
                    kwargs['employee'] = employee
                    kwargs['token'] = token

                return func(self, *args, **kwargs)
            except MobileApiError as exc:
                request.env.cr.rollback()
                return request.make_json_response(
                    error_envelope(exc.code, exc.message, exc.details), status=exc.http_status)
            except (UserError, ValidationError) as exc:
                request.env.cr.rollback()
                return request.make_json_response(
                    error_envelope('VALIDATION_ERROR', str(exc)), status=400)
            except PG_CONCURRENCY_EXCEPTIONS_TO_RETRY:
                # A concurrent request (e.g. two simultaneous check-ins for the
                # same employee) collided at the database level -- our own
                # `SELECT ... FOR NO KEY UPDATE` lock, or a downstream
                # recompute (hr.employee.last_attendance_id and friends), hit
                # a serialization failure / lock timeout / deadlock. Do NOT
                # roll back or swallow this here: it must propagate all the
                # way up to odoo.http's dispatcher, whose retrying() wrapper
                # rolls back and replays the *entire* request from scratch.
                # On replay, this request's own domain check (e.g. "is there
                # already an open attendance?") runs again against the
                # winner's now-committed data, so the loser of the race gets
                # the correct 409 ALREADY_CHECKED_IN instead of a bogus 500.
                raise
            except psycopg2.OperationalError as exc:
                # Fallback for a concurrency error that arrives as a bare
                # OperationalError instead of one of the specific subclasses
                # above (can happen depending on the psycopg2/libpq version):
                # check the SQLSTATE code directly so it still gets retried.
                if getattr(exc, 'pgcode', None) in PG_CONCURRENCY_ERRORS_TO_RETRY:
                    raise
                request.env.cr.rollback()
                _logger.exception("Unexpected error while handling a mobile API request")
                return request.make_json_response(
                    error_envelope('SERVER_ERROR', _("Something went wrong. Please try again.")),
                    status=500)
            except Exception:
                request.env.cr.rollback()
                _logger.exception("Unexpected error while handling a mobile API request")
                return request.make_json_response(
                    error_envelope('SERVER_ERROR', _("Something went wrong. Please try again.")),
                    status=500)
        return wrapped
    return decorator
