# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    penalties_awards_ids = fields.Many2many('gs.penalties.awards', string='Penalties & Awards Deduction',
                                            domain="[('employee_id', '=', employee_id)]")
    deduction_amount = fields.Float('Deduction Amount', compute='get_penalties_awards_amount')
    awards_amount = fields.Float('Awards Amount', compute='get_penalties_awards_amount')
    pa_installment_ids = fields.Many2many('gs.penalties.awards.installment')
    total_penalties_awards = fields.Float(
        string='Total Penalties & Awards',
        compute='_compute_total_penalties_awards',
        store=True
    )

    @api.depends('penalties_awards_ids')
    def _compute_total_penalties_awards(self):
        for payslip in self:
            total = 0
            installment = []
            # payslip.total_penalties_awards = sum(p.installment_amount for p in payslip.penalties_awards_ids)
            for record in payslip.penalties_awards_ids:
                for rec in record.pa_installment_ids:
                    if rec.date >= payslip.date_from and rec.date <= payslip.date_to and not rec.is_paid and rec.payroll_paid:
                        total += rec.installment_amt
                        installment.append(rec)
            payslip.pa_installment_ids = [(4,line.id) for line in installment]
            payslip.total_penalties_awards = total

    def compute_sheet(self):
        for rec in self:
            penalties_awards_ids = self.env['gs.penalties.awards'].search([('employee_id', '=', rec.employee_id.id),
                                                                           ('state', 'in', ['approve','paid']),
                                                                           ('start_date', '<=', rec.date_to),
                                                                           ])
            if penalties_awards_ids:
                rec.penalties_awards_ids = [(6, 0, penalties_awards_ids.ids)]
        return super(hr_payslip, self).compute_sheet()

    @api.depends('penalties_awards_ids')
    def get_penalties_awards_amount(self):
        for payslip in self:
            deduction_amount = 0
            awards_amount = 0
            if payslip.penalties_awards_ids:
                for penalties_awards in payslip.penalties_awards_ids:
                    if penalties_awards.type == 'deduction':
                        deduction_amount += penalties_awards.amount
                    elif penalties_awards.type == 'award':
                        awards_amount += penalties_awards.amount

            payslip.deduction_amount = deduction_amount
            payslip.awards_amount = awards_amount

    @api.onchange('employee_id')
    def onchange_employee(self):
        for rec in self:
            if self.employee_id:
                penalties_awards_ids = self.env['gs.penalties.awards'].search([('employee_id', '=', rec.employee_id.id),
                                                                               ('state', '=', 'approve'),
                                                                               ('date', '>=', rec.date_from),
                                                                               ('date', '<=', rec.date_to),
                                                                               ])
                if penalties_awards_ids:
                    rec.penalties_awards_ids = [(6, 0, penalties_awards_ids.ids)]

    def action_payslip_done(self):
        res = super(hr_payslip, self).action_payslip_done()
        for rec in self:
            if rec.pa_installment_ids:

                for record in rec.pa_installment_ids:
                    record.payslip_id = rec.id
                    record.is_paid = True

        return res

    def action_payslip_draft(self):
        res = super().action_payslip_draft()
        for rec in self:
            if rec.pa_installment_ids:

                for record in rec.pa_installment_ids:
                    record.payslip_id = False
                    record.is_paid = False
        return res

    def action_payslip_cancel(self):
        res = super().action_payslip_cancel()
        for rec in self:
            if rec.pa_installment_ids:

                for record in rec.pa_installment_ids:
                    record.payslip_id = False
                    record.is_paid = False
        return res
