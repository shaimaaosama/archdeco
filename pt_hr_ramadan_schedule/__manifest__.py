{
    'name': "Ramadan Working Schedule",
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Employees',
    'summary': "Switch working schedules to reduced Ramadan hours during "
               "the yearly Ramadan period, without touching contracts.",
    'description': """
Ramadan Working Schedule
========================

* Define the Ramadan period of each year (Employees > Configuration >
  Ramadan Periods). The dates follow the Hijri calendar and are announced
  yearly, so HR enters them once per year.
* Link every normal working schedule to its Ramadan schedule (field
  "Ramadan Schedule" on the working schedule form).
* During a Ramadan period the Ramadan schedule replaces the normal one
  everywhere Odoo computes working time: time off durations, attendance
  overtime, work entries / payroll, the employee mobile app, etc.
  Employees and contracts keep their normal schedule, so past Ramadan
  periods are always recomputed correctly.
* Public holidays (Eid...) stay on the normal schedule's time off and keep
  applying during Ramadan.
""",
    'author': "Shaimaa Osama El-Marsafawy",
    'maintainer': "Shaimaa Osama El-Marsafawy",
    'license': 'LGPL-3',
    'depends': ['hr', 'resource'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_ramadan_period_views.xml',
        'views/resource_calendar_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
