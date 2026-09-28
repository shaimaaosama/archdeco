# Employee Mobile App API (`employee_mobile`)

Odoo 18 module that exposes a JSON REST API under `/api/mobile` so employees
can use the ArchDeco mobile app (login, attendance check-in/out, attendance
history, payslips) **without an Odoo user per employee**.

See [`API.md`](API.md) for the full endpoint contract and curl examples.

## Dependencies

`hr`, `hr_attendance`, `hr_payroll` (Enterprise — provides `hr.payslip`),
`resource`.

The module does **not** depend on `pt_attendance_portal`, `muk_rest`,
`hr_holidays` or `portal`. It is designed to work standalone, and to coexist
with `pt_attendance_portal` if both are installed (see "Coexistence" below).
`hr_holidays` (leave/time off in the attendance history) and a custom
`arabic_name` field on `hr.employee` (used for the Arabic display name) are
both used opportunistically **only if installed/present** — the module
never requires them.

## Setup (HR)

1. **Employees** — HR Settings tab:
   - Set **Work Email** and **PIN** (4-8 digits). This is the mobile app
     login (same PIN as Attendance Kiosk mode).
   - On the new **Mobile App** tab: confirm **Mobile App Access** is on,
     and pick the **Mobile Attendance Location** mode:
     - `Work Location` (default) — must be within the radius of the
       employee's assigned Work Location.
     - `Company` — must be within the radius of the company's own
       coordinates.
     - `None` — no geofence check (e.g. drivers, field staff). GPS
       coordinates are still sent and stored for the audit trail.
2. **Work Locations** (Employees > Configuration > Work Locations) — set
   **Attendance Latitude/Longitude** and **Attendance Radius (m)** (default
   100 m) on every location used in `Work Location` mode.
3. **Company** (Settings > Companies, "Mobile App" tab, or Attendance app >
   Configuration > Settings) — set the company's own coordinates/radius for
   employees in `Company` mode, the **Late Grace Period** (minutes after the
   scheduled start before a check-in counts as late), and whether to
   **Block Mock Locations** (rejects check-in/out when the device reports a
   mocked/fake GPS location; on by default).
4. **Payslips** — only payslips in state `done` or `paid` are visible to the
   employee.

## Security model

- No `res.users` is created per employee. Employees authenticate with
  **work email + PIN** and get back an opaque bearer token
  (`secrets.token_urlsafe(32)`); only its SHA-256 hash is stored
  (`hr.employee.mobile.token`).
- Tokens have a sliding expiry (`employee_mobile.token_validity_days`,
  default 30 days) and are revoked when: the employee logs out, HR changes
  their PIN or toggles Mobile App Access, HR clicks "Revoke App Sessions",
  or the employee is archived. The app's own "Change PIN" screen keeps the
  session that made the change and revokes every other one.
- Failed logins are rate-limited per employee
  (`employee_mobile.max_failed_attempts`, default 5) with a lockout
  (`employee_mobile.lockout_minutes`, default 15 minutes). HR can clear a
  lock from the employee's Mobile App tab ("Unlock").
- Every controller runs as the public user with `sudo()`, but every ORM
  call is scoped to the token's own employee — an unknown/foreign record id
  returns `404 NOT_FOUND`, never `403`, so nothing about other employees'
  data is leaked.
- These `ir.config_parameter` keys can be overridden without code changes:
  `employee_mobile.token_validity_days`,
  `employee_mobile.max_failed_attempts`,
  `employee_mobile.lockout_minutes`.

## Coexistence with `pt_attendance_portal`

This module can be installed alongside `pt_attendance_portal` (or on its
own):

- It redeclares `hr.attendance`'s `check_in_latitude` / `check_in_longitude`
  / `check_out_latitude` / `check_out_longitude` fields with the same name,
  type and string as the portal module (but `digits=(10, 7)`, never the
  portal's own decimal-precision record, which is deleted if the portal is
  uninstalled). Both modules declaring the same field name means the
  underlying database column and its data survive uninstalling either one.
- It also always writes the *core* `hr_attendance` fields
  (`in_latitude`/`in_longitude`/`in_ip_address`/`in_browser`/`in_mode`, and
  the `out_*` equivalents), which always exist regardless of which
  attendance-tracking modules are installed.
- It never reads `attendance_state` (the portal module overrides it as a
  stored, day-based field that can disagree with reality) — attendance
  state is always derived by searching `hr.attendance` for an open
  (`check_out = False`) record.
- It never touches the portal's own `hr.attendance.geofence` model or
  `/hr_attendance/*` routes. Its own routes only live under `/api/mobile/*`.
- Its own views only add its own fields; it does not add another display of
  `check_in_latitude`/`check_in_longitude` (the portal's view already shows
  those).

## Cron

A daily cron (`Mobile App: Clean up expired/revoked session tokens`) deletes
expired tokens, and revoked (inactive) tokens older than 30 days.

## Tests

```
cd /home/shaimaa/PycharmProjects/odoo18
.venv/bin/python odoo18/odoo-bin -c odoo.conf \
  --addons-path=odoo18/addons,odoo18/odoo/addons,enterprise-18.0,Hadeel/archdeco \
  -d pt_mobile_test -i employee_mobile --test-tags /employee_mobile \
  --http-port=8099 --stop-after-init
```

## Web app (PWA) for iPhone and browsers

The Flutter app's web build is served by this module at **`/employee-app/`**
(e.g. `https://arch.ptech.host/employee-app/`). Because it is the same origin
as `/api/mobile`, no CORS setup is needed, and one build works on any server.

- **Install on iPhone:** open the link in Safari → Share → *Add to Home Screen*.
  Android: Chrome → menu → *Install app* / *Add to Home screen*.
- **HTTPS is required** for GPS check-in (browsers only allow location on
  HTTPS or `localhost`).
- **Update it:** in the Flutter project run `tool/build_pwa.sh`, which builds
  and copies the files into `static/app/`; commit them and update the module.
  Files are served with `Cache-Control: no-cache`, so employees get the new
  version on their next launch.
- **Limits vs. the store apps:** no mock-location detection on iPhone (the
  server geofence still applies); payslip PDFs open in the browser's viewer.
  CanvasKit (Flutter's renderer) is loaded from `www.gstatic.com`.
