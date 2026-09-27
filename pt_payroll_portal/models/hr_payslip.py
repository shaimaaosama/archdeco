from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    portal_visible = fields.Boolean(
        string='Visible in Portal',
        default=True,
        help="If checked, this payslip will be visible to the employee in the portal"
    )
    
    access_token = fields.Char(
        string='Access Token',
        copy=False,
        help="Used to access the payslip from portal without being logged in"
    )
    
    def _portal_ensure_token(self):
        """Ensure that each payslip has an access token."""
        for payslip in self:
            if not payslip.access_token:
                payslip.access_token = payslip._portal_generate_token()
    

    def _portal_generate_token(self):
        """Generate a secure token for portal access."""
        db_uuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid') or ''
        db_prefix = db_uuid[:8] if isinstance(db_uuid, str) else 'dbprefix'
        seq = self.env['ir.sequence'].next_by_code('portal.payslip.token') or '0000'
        return f"{db_prefix}-{seq}"

    @api.model
    def create(self, vals):
        """Generate access token on creation."""
        res = super(HrPayslip, self).create(vals)
        res._portal_ensure_token()
        return res
    
    def action_payslip_done(self):
        """When payslip is done, ensure it has an access token."""
        res = super(HrPayslip, self).action_payslip_done()
        self._portal_ensure_token()
        return res
