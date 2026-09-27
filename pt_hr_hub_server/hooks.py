# -*- coding: utf-8 -*-

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

HUB_ATTENDANCE_ROUTE = "/api/v1/hr_hub/attendance"


def _find_first_available_model(env, candidates):
    for model_name in candidates:
        if model_name in env:
            return env[model_name]
    return None


def _build_vals(model, values):
    return {key: value for key, value in values.items() if key in model._fields}


def _setup_muk_rest_objects(env):
    rule_model = _find_first_available_model(env, ["muk_rest.access_rules"])
    expr_model = _find_first_available_model(env, ["muk_rest.access_rules.expression"])
    oauth_model = _find_first_available_model(env, ["muk_rest.oauth"])

    if not rule_model or not expr_model or not oauth_model:
        _logger.info("MuK REST access rule models not found. Skipping dynamic setup.")
        return

    oauths = oauth_model.search([("security", "=", "advanced"), ("active", "=", True)])
    if not oauths:
        _logger.warning(
            "No active MuK REST OAuth config with advanced security found. "
            "Create one to enforce route-level access rules for %s.",
            HUB_ATTENDANCE_ROUTE,
        )
        return

    required_params = ["employee_id", "device_uuid", "lat", "long"]
    forbidden_params = ["model", "domain", "fields", "values", "ids", "method", "args", "kwargs"]

    for oauth in oauths:
        rule = rule_model.search(
            [
                ("oauth_id", "=", oauth.id),
                ("route", "=", HUB_ATTENDANCE_ROUTE),
            ],
            limit=1,
        )
        rule_vals = _build_vals(
            rule_model,
            {
                "oauth_id": oauth.id,
                "sequence": 5,
                "applied": True,
                "route": HUB_ATTENDANCE_ROUTE,
            },
        )
        if rule:
            rule.write(rule_vals)
        else:
            rule = rule_model.create(rule_vals)

        if "expression_ids" in rule._fields:
            rule.expression_ids.unlink()

        expression_vals_list = []
        for param in required_params:
            expression_vals_list.append(
                _build_vals(
                    expr_model,
                    {
                        "rule_id": rule.id,
                        "param": param,
                        "operation": "*",
                    },
                )
            )
        for param in forbidden_params:
            expression_vals_list.append(
                _build_vals(
                    expr_model,
                    {
                        "rule_id": rule.id,
                        "param": param,
                        "operation": "!",
                    },
                )
            )

        for vals in expression_vals_list:
            expr_model.create(vals)

    _logger.info("MuK REST access-rule setup completed for HR hub attendance endpoint %s.", HUB_ATTENDANCE_ROUTE)


def post_init_hook(cr_or_env, registry=None):
    if hasattr(cr_or_env, "cr") and hasattr(cr_or_env, "uid"):
        env = cr_or_env
    else:
        env = api.Environment(cr_or_env, SUPERUSER_ID, {})
    try:
        _setup_muk_rest_objects(env)
    except Exception:
        _logger.exception("Failed to set up MuK REST access rules for HR hub module.")
