# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class GsEOSMonthly(models.Model):
    _name = 'gs.eos.monthly'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'End Of Service Monthly'

    name = fields.Char(string='Name')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    eos_total_amount_month = fields.Monetary('EOS Monthly', readonly=True)
    date = fields.Date(string='Date')
    journal_id = fields.Many2one('account.journal', string='Source Journal', copy=False)
    journal_eos_monthly_ids = fields.Many2many('account.move', string='Generated Journals')
    journal_monthly_count = fields.Integer(compute="_compute_journal_monthly_count", default=0)
    eos_difference = fields.Float(related='employee_id.contract_id.eos_difference', readonly=True)
    eos_total_amount = fields.Monetary('EOS Total Amount',related='employee_id.contract_id.eos_total_amount', readonly=True)



    def _compute_journal_monthly_count(self):
        if self.journal_eos_monthly_ids:
            self.journal_monthly_count = len(self.journal_eos_monthly_ids)
        else:
            self.journal_monthly_count = 0


    def action_open_monthly_journal(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "views": [[False, "list"], [False, "form"]],
            "domain": [['id', 'in', self.journal_eos_monthly_ids.ids]],
            "name": "Journal",
        }

    def your_custom_method(self):
        pass


    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.get_name()
        return records

    def get_name(self):
        for rec in self:
            rec.name = "End of service for " + str(rec.employee_id.name)

    def _check(self):
        get_conf = self.env['eos.conf'].search([('company_id', '=', self.env.company.id)], limit=1)
        if get_conf.journal_id:
            self.create_eos_monthly()
        else:
            raise UserError(_("Enable configuration settings (EOS Monthly Accrual)"))

    @api.model
    def create_eos_monthly(self):
        today = fields.Date.today()
        get_conf = self.env['eos.conf'].search([('company_id', '=', self.env.company.id)], limit=1)
        day_of_operation = get_conf.day_of_operation

        if today.day != day_of_operation:
            return

        employee_update_eos = self.env['hr.employee'].search([])
        for em_upd in employee_update_eos:
            if em_upd.contract_id.update_eos != True:
                em_upd.contract_id.update_eos = True
        employee = self.env['hr.employee'].search([('company_id', '=', self.env.company.id)])
        for emp in employee:
            if emp.contract_id.state == 'open' and emp.contract_id.update_eos == True:
                vals = {
                    'name': "End of service for " + str(emp.name),
                    'employee_id': emp.id,
                    'eos_total_amount_month': emp.contract_id.eos_total_amount_month,
                    'date': today,
                    'company_id': emp.company_id.id,
                }
                eos = self.env['gs.eos.monthly'].search([('employee_id', '=', emp.id), ('date', '=', today)])
                if not eos:
                    self.env['gs.eos.monthly'].create(vals)
                else:
                    eos.write({'eos_total_amount_month': emp.contract_id.eos_total_amount_month})



    @api.model
    def create_eos_monthly_from_hired_date(self):
        today = fields.Date.today()
        employees = self.env['hr.employee'].search([])
        for emp in employees:
            get_conf = self.env['eos.conf'].search([('company_id', '=', emp.company_id.id)], limit=1)
            day_of_operation = get_conf.day_of_operation
            if emp.contract_id and emp.contract_id.state == 'open' and emp.contract_id.update_eos:
                # if emp.contract_id.is_eos == False:
                hired_date = emp.contract_id.date_hired
                if hired_date:
                    current_date = hired_date.replace(day=28) + relativedelta(months=1)

                    while current_date <= today:
                        delta = relativedelta(current_date, hired_date)
                        total_months = delta.years * 12 + delta.months

                        eos_amount = emp.contract_id.eos_total_amount_month

                        vals = {
                            'name': f"End of service for {emp.name} - {current_date.strftime('%Y-%m')}",
                            'employee_id': emp.id,
                            'eos_total_amount_month': eos_amount,
                            'date': current_date,
                            'company_id': emp.company_id.id,
                        }

                        eos = self.env['gs.eos.monthly'].search([
                            ('employee_id', '=', emp.id),
                            ('date', '=', current_date)
                        ])

                        if not eos:
                            self.env['gs.eos.monthly'].create(vals)
                        else:
                            eos.write({'eos_total_amount_month': eos_amount})

                        current_date += relativedelta(months=1)
            # emp.contract_id.is_eos = True

    def create_journal_entry(self):
        lines = [(5, 0, 0)]
        get_conf = self.env['eos.conf'].search([('company_id', '=', self.env.company.id)], limit=1)
        journal_id = get_conf.journal_id.id
        account_id = get_conf.account_id.id
        account_credit_id = get_conf.account_credit_id.id
        # account_journal = self.env['account.journal'].search([('id', '=', journal_id)])
        # eos_monthly = self.env['gs.eos.monthly'].search([('date', '=', today)])
        # for eoss in eos_monthly:

        for rec in self:
            today = rec.date
            move_line_1 = {
                'name': rec.name,
                'partner_id': rec.employee_id.address_home_id.id,
                'account_id': account_credit_id,
                'debit': 0.0,
                'credit': rec.eos_total_amount_month,
            }
            move_line_2 = {
                'name': rec.name,
                'partner_id': rec.employee_id.address_home_id.id,
                'account_id': account_id,
                'credit': 0.0,
                'debit': rec.eos_total_amount_month,
            }
            lines.append((0, 0, move_line_1))
            lines.append((0, 0, move_line_2))
        sequence = self.env['ir.sequence'].next_by_code('eos.monthly') or '/'
        move_vals = {
            'ref': sequence,
            'move_type': 'entry',
            'journal_id': journal_id,
            'date': today,
            'line_ids': lines,
        }

        account_move = self.env['account.move'].search([('date', '=', today), ('ref', '=', sequence)])
        if not account_move:
            new_journal = self.env['account.move'].create(move_vals)
            self.journal_eos_monthly_ids += new_journal

    def delete_eos_difference(self):
        for rec in self:
            if rec.employee_id.contract_id.eos_difference:
                rec.employee_id.contract_id.eos_difference = 0






    # def create_eos_monthly(self):
    #     contracts = self.env['hr.contract'].search([('state', '=', 'open')])
    #     today = fields.Date.today()
    #     emp_ids = []
    #     lines = [(5, 0, 0)]
    #     journal_id = int(self.env['ir.config_parameter'].sudo().get_param('gs_hr_eos.journal_id'))
    #     account_id = int(self.env['ir.config_parameter'].sudo().get_param('gs_hr_eos.account_id'))
    #     account_journal = self.env['account.journal'].search([('id', '=', journal_id)])
    #     for con2 in contracts:
    #         con2._onchange_eos_total_amount()
    #         emp_ids.append(con2.employee_id.id)
    #
    #     employee = self.env['hr.employee'].search([('id', 'in', emp_ids)])
    #     for emp in employee:
    #         emp._compute_action_get_data()
    #         emp.action_get_data()
    #         if emp.contract_id.date_start and emp.contract_id.date_end:
    #             if emp.contract_id.date_end >= today:
    #                 if emp.eos_total_amount_month:
    #                     val = {
    #                         'name':  "End of service for " + str(emp.name),
    #                         'employee_id': emp.id,
    #                         'eos_total_amount_month': emp.eos_total_amount_month,
    #                         'date': today,
    #                     }
    #
    #                     eos = self.env['gs.eos.monthly'].search([('employee_id', '=', emp.id)])
    #                     if not eos:
    #                         self.env['gs.eos.monthly'].create(val)
    #
    #         elif emp.contract_id.date_start and not emp.contract_id.date_end:
    #             if emp.contract_id.date_start <= today:
    #                 if emp.eos_total_amount_month:
    #                     val = {
    #                         'name': "End of service for " + str(emp.name),
    #                         'employee_id': emp.id,
    #                         'eos_total_amount_month': emp.eos_total_amount_month,
    #                         'date': today,
    #                     }
    #
    #                     eos = self.env['gs.eos.monthly'].search([('employee_id', '=', emp.id)])
    #                     if not eos:
    #                         self.env['gs.eos.monthly'].create(val)
    #
    #     eos_monthly = self.env['gs.eos.monthly'].search([('date', '=', today)])
    #     for eos in eos_monthly:
    #         move_line_1 = {
    #             'name': eos.name,
    #             'partner_id': eos.employee_id.address_home_id.id,
    #             'account_id': account_id,
    #             'debit': 0.0,
    #             'credit': eos.eos_total_amount_month,
    #         }
    #         move_line_2 = {
    #             'name': eos.name,
    #             'partner_id': eos.employee_id.address_home_id.id,
    #             'account_id': account_journal.gs_def_debit_acc.id,
    #             'credit': 0.0,
    #             'debit': eos.eos_total_amount_month,
    #         }
    #         lines.append((0, 0, move_line_1))
    #         lines.append((0, 0, move_line_2))
    #
    #     move_vals = {
    #         'ref': 'EOS Monthly',
    #         'move_type': 'entry',
    #         'journal_id': journal_id,
    #         'date': today,
    #         'line_ids': lines,
    #     }
    #
    #     account_move = self.env['account.move'].search([('date', '=', today), ('ref', '=', 'EOS Monthly')])
    #     if not account_move:
    #         self.env['account.move'].create(move_vals)