# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Premium Tech Employee Advanced Info',
    'version': '18.0.1.0.0',
    'summary': "Adds advanced employee fields: notice periods, document expiry notifications, and contract-day settings.",
    'description': 'Extends Odoo employee records with notice period configuration, Iqama/passport expiry reminder settings, and contract-days configuration.',
    'category': 'Human Resources',
    "author": "Premium Tech",
    "website": "https://ptech.sh",
    'depends': ['base', 'hr', 'mail', 'hr_gamification', 'hr_contract', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/contract_days_view.xml',
        'views/updation_config.xml',

        'views/hr_employee_view.xml',
        'views/hr_notification.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
