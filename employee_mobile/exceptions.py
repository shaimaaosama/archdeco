# -*- coding: utf-8 -*-
"""Shared exception used by both the models and the controllers of this module.

Kept outside of ``models``/``controllers`` so both layers can import it
without creating a controllers -> models -> controllers cycle.
"""


class MobileApiError(Exception):
    """An error that should be turned into the mobile API's JSON error envelope.

    :param code: machine readable error code, e.g. ``OUTSIDE_LOCATION`` (see API.md).
    :param http_status: HTTP status code to answer with.
    :param message: human readable, translated message.
    :param details: optional dict with extra structured info (e.g. distance/radius).
    """

    def __init__(self, code, http_status, message, details=None):
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.message = message
        self.details = details or {}
