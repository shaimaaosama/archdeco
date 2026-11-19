{
    'name': "Special Working Schedule",
    'version': '18.0.2.0.0',
    'category': 'Human Resources/Employees',
    'summary': "Apply the Special Working Schedules (Ramadan...) of HR "
               "Customizations everywhere Odoo computes working time.",
    'description': """
Special Working Schedule
========================

* Special working schedules are defined in HR Customizations (hr_customs):
  tick "Special Working Schedule" on a working schedule, set its Start and
  End Date and, optionally, the companies, departments, employees,
  nationalities or religion it applies to. Create a new one (or update the
  dates) every year for Ramadan.
* During these days the most specific matching special schedule replaces
  the employee's schedule everywhere Odoo computes working time: time off
  durations, attendance overtime, work entries / payroll, the employee
  mobile app, attendance sheets (with Special Working Schedule -
  Attendance Sheet), etc. - the same rule as the Attendances Dashboard.
  Employees and contracts keep their normal schedule.
* Time off start / end hours and half days (morning / afternoon) also follow
  the special schedule. A special schedule with a single line per day
  (e.g. 09:00-15:00) is split in two equal halves.
* Public holidays (Eid...) stay on the normal schedule's time off and keep
  applying during Ramadan.
""",
    'author': "Shaimaa Osama El-Marsafawy",
    'maintainer': "Shaimaa Osama El-Marsafawy",
    'license': 'LGPL-3',
    'depends': ['hr', 'resource', 'hr_attendance', 'hr_holidays', 'hr_customs'],
    'data': [
        'views/resource_calendar_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
