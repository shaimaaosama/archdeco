# -*- coding: utf-8 -*-

import base64
import hashlib

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None


class HubClientConfig(models.Model):
    _name = "hub.client.config"
    _description = "Hub Client Odoo Configuration"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    client_url = fields.Char(required=True)
    client_db = fields.Char(required=True)
    api_user = fields.Char(required=True, help="Remote Odoo login used with API key.")
    api_key_encrypted = fields.Text(string="Encrypted API Key", copy=False)
    api_key = fields.Char(
        string="API Key",
        compute="_compute_api_key",
        inverse="_inverse_api_key",
        password=True,
        store=False,
    )

    @api.model
    def _get_fernet(self):
        if Fernet is None:
            raise UserError(_("Package 'cryptography' is required to store encrypted API keys."))
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret") or self.env.cr.dbname
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
        return Fernet(key)

    def _compute_api_key(self):
        for rec in self:
            rec.api_key = rec._decrypt_secret(rec.api_key_encrypted)

    def _inverse_api_key(self):
        for rec in self:
            if rec.api_key:
                rec.api_key_encrypted = rec._get_fernet().encrypt(rec.api_key.encode("utf-8")).decode("utf-8")
            else:
                rec.api_key_encrypted = False

    def _decrypt_secret(self, encrypted_value):
        if not encrypted_value:
            return False
        try:
            return self._get_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
        except Exception:
            return False

    def get_rpc_credentials(self):
        self.ensure_one()
        if not self.api_key_encrypted:
            raise UserError(_("API key is missing for client '%s'.") % self.display_name)
        api_key = self._decrypt_secret(self.api_key_encrypted)
        if not api_key:
            raise UserError(_("Failed to decrypt API key for client '%s'.") % self.display_name)
        return {
            "url": self.client_url.rstrip("/"),
            "db": self.client_db,
            "user": self.api_user,
            "api_key": api_key,
        }

    @api.model
    def _cron_sync_subscription(self):
        """Cron job to sync subscription daily."""
        try:
            self.env['res.config.settings'].create({}).action_sync_subscription()
        except Exception as e:
            pass
