# Employee Mobile App API — Contract

Base URL: `{API_BASE_URL}/api/mobile`

This contract is shared with the Flutter app (`archdeco_employee`). Endpoint
paths, JSON shapes, field names, error codes and HTTP statuses here must
match the app exactly — do not change one side without the other.

## Conventions

- Headers: `Authorization: Bearer <token>` (all routes except `/ping` and
  `/login`), `Accept-Language: en|ar|ur` (or `?lang=en|ar|ur`),
  `Content-Type: application/json` on every request with a body.
- Success envelope: `{"success": true, "data": {...}}`.
- Error envelope: `{"success": false, "error": {"code": "OUTSIDE_LOCATION", "message": "<translated>", "details": {...}}}`.
  `details` is omitted when there is nothing extra to report.
- **Datetimes** are ISO-8601 **in the employee's timezone, with UTC offset**
  (e.g. `2026-09-22T07:52:00+03:00`). Show the wall-clock part as-is —
  do not convert to the device's timezone.
- Dates are `YYYY-MM-DD`. Hours/days are decimal floats.
- All endpoints below other than `/ping` and `/login` require the
  `Authorization` header. A missing/unknown/expired token returns 401 and
  the app should log the user out.

## Endpoints

### `GET /ping` — no auth

```
curl -s http://localhost:8099/api/mobile/ping
```
`data`: `{"ok": true, "version": "18.0.1.0.0"}`

### `POST /login` — no auth

Request: `{"email", "pin", "device": {"id", "name", "platform", "app_version"}}`

```
curl -s -X POST http://localhost:8099/api/mobile/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","pin":"1234","device":{"id":"abc123","name":"Pixel 8","platform":"android","app_version":"1.0.0"}}'
```
`data`: `{"token", "expires_at", "employee": Profile}`

### `POST /logout`

```
curl -s -X POST http://localhost:8099/api/mobile/logout \
  -H "Authorization: Bearer $TOKEN"
```
`data`: `{}` — deactivates the token.

### `GET /profile`

```
curl -s http://localhost:8099/api/mobile/profile -H "Authorization: Bearer $TOKEN"
```
`data`: `Profile`

### `GET /profile/image`

Returns the employee's photo (256px) as raw image bytes
(`Content-Type: image/png|image/jpeg|...`). `404 NOT_FOUND` (JSON envelope)
when no photo is on file. Only download it when `Profile.image_version`
is non-null, and re-download when that value changes.

```
curl -s http://localhost:8099/api/mobile/profile/image \
  -H "Authorization: Bearer $TOKEN" -o photo.png
```

### `POST /change-pin`

Request: `{"current_pin", "new_pin"}`. New PIN: 4-8 digits, different from
the current one. Revokes every other active session.

```
curl -s -X POST http://localhost:8099/api/mobile/change-pin \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"current_pin":"1234","new_pin":"4321"}'
```
`data`: `{}`

### `GET /home`

```
curl -s http://localhost:8099/api/mobile/home -H "Authorization: Bearer $TOKEN"
```
`data`:
```json
{
  "server_time": "2026-09-22T07:52:00+03:00",
  "attendance": AttendanceStatus,
  "restriction": "work_location|company|none",
  "geofence": Geofence | null,
  "geofence_error": null | "LOCATION_NOT_CONFIGURED",
  "shift": Shift | null,
  "month_present_days": 12,
  "latest_payslip": {"id": 1, "date_from": "2026-08-01"} | null
}
```

### `POST /attendance/check-in`

Request: `{"latitude", "longitude", "accuracy", "is_mocked": bool}` —
coordinates are always required, even for `none`-restriction employees
(audit trail).

```
curl -s -X POST http://localhost:8099/api/mobile/attendance/check-in \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"latitude":24.7136,"longitude":46.6753,"accuracy":8.0,"is_mocked":false}'
```
`data`: `{"attendance": AttendanceStatus, "distance": float|null, "location_name": str|null}`

### `POST /attendance/check-out`

Same request/response shape as check-in.

```
curl -s -X POST http://localhost:8099/api/mobile/attendance/check-out \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"latitude":24.7136,"longitude":46.6753,"accuracy":8.0,"is_mocked":false}'
```

### `GET /attendance?month=YYYY-MM`

Default: current month.

```
curl -s "http://localhost:8099/api/mobile/attendance?month=2026-08" \
  -H "Authorization: Bearer $TOKEN"
```
`data`: `{"month", "summary": {"present","late","leave"}, "days": [AttendanceDay]}` (newest first).

### `GET /payslips?year=YYYY`

Default: the latest year that has a payslip.

```
curl -s "http://localhost:8099/api/mobile/payslips?year=2026" \
  -H "Authorization: Bearer $TOKEN"
```
`data`: `{"years": [2026, 2025], "payslips": [PayslipSummary]}`

### `GET /payslips/<id>`

```
curl -s http://localhost:8099/api/mobile/payslips/1 -H "Authorization: Bearer $TOKEN"
```
`data`: `PayslipDetail`

### `GET /payslips/<id>/pdf`

Returns raw `application/pdf` bytes with
`Content-Disposition: attachment; filename="Payslip-2026-08.pdf"`. Errors
(e.g. not found) use the normal JSON envelope instead.

```
curl -s http://localhost:8099/api/mobile/payslips/1/pdf \
  -H "Authorization: Bearer $TOKEN" -o payslip.pdf
file payslip.pdf   # -> PDF document
```

## Object shapes

**Profile**
```json
{
  "id": 1, "name": "Jane Doe", "code": "EMP001",
  "job_title": "Site Engineer", "department": "Engineering", "company": "ArchDeco",
  "work_email": "jane@example.com", "mobile_phone": "+966500000000",
  "work_location": "HQ Site",
  "manager": {"name": "John Smith", "email": "john@example.com", "phone": "+96650..."} | null,
  "shift": Shift | null,
  "attendance_restriction": "work_location",
  "image_version": "3f9a1c0b7d2e" | null
}
```
`name` is `arabic_name` when the language is `ar` and that field is set (and
present — `pt_employee.arabic_name` is optional). `code` is
`registration_number`, else `barcode`, else `str(id)`. `image_version` is a
short fingerprint of the photo (`null` = no photo); it changes whenever HR
uploads a new one.

**Shift**: `{"name": "Mobile Test Calendar", "start": "08:00", "end": "17:00"}`.
Computed for today from the employee's working calendar; `null` on a day off
or for a flexible-hours calendar.

**Geofence**: `{"mode", "name", "latitude", "longitude", "radius"}`.

**AttendanceStatus**
```json
{
  "state": "checked_in|checked_out",
  "check_in": "2026-09-22T07:52:00+03:00" | null,
  "today_worked_hours": 3.25,
  "today_sessions": [{"id": 10, "check_in": "...", "check_out": "..."|null, "worked_hours": 3.25, "location_name": "HQ Site"|null}]
}
```
`check_in` is the check-in of the currently open attendance record; it can
be from a previous day if the employee forgot to check out (standard Odoo
behaviour — the employee just checks out).

**AttendanceDay**
```json
{
  "date": "2026-08-10", "check_in": "...", "check_out": "..."|null,
  "worked_hours": 8.0, "status": "working|on_time|late|leave",
  "location_name": "HQ Site"|null, "sessions": [...]
}
```
Sessions are grouped per local day (first check-in, last check-out, sum of
hours). **Late**: first check-in after the day's first scheduled interval
start + `mobile_late_grace_minutes`. **Leave**: days up to today covered by
a validated `hr.leave` (`state='validate'`) that have scheduled work and no
attendance — only present when `hr_holidays` is installed.

**PayslipSummary**
```json
{
  "id": 1, "name": "...", "number": "SLIP/2026/08"|null,
  "date_from": "2026-08-01", "date_to": "2026-08-31",
  "state": "done|paid", "paid_date": "2026-09-01"|null,
  "net_wage": 5200.0, "gross_wage": 5500.0, "currency": "SAR"
}
```
Only payslips in `state in ('done', 'paid')` are ever returned.

**PayslipDetail**: `PayslipSummary` plus:
```json
{
  "worked_days": 22.0,
  "earnings": [{"name": "Basic Salary", "code": "BASIC", "amount": 5000.0}],
  "deductions": [{"name": "Deduction", "code": "DED1", "amount": -300.0}],
  "total_deductions": 300.0
}
```
Lines are `line_ids` with `appears_on_payslip = True`, excluding category
codes `GROSS`/`NET`. A line with `total >= 0` is an earning, `total < 0` is
a deduction (`amount` keeps the line's own sign; `total_deductions` is the
positive sum of the deducted amounts). `worked_days` is the sum of
`number_of_days` over `worked_days_line_ids` with `code == 'WORK100'`.

## Error codes

| Code | HTTP | When |
|---|---|---|
| `VALIDATION_ERROR` | 400 | invalid input; also core `UserError`/`ValidationError` |
| `LOCATION_REQUIRED` | 400 | no coordinates sent on check-in/out |
| `PIN_INCORRECT` | 400 | change-pin with a wrong current PIN |
| `PIN_FORMAT` | 400 | new PIN not 4-8 digits, or equal to the current one |
| `INVALID_CREDENTIALS` | 401 | unknown email, disabled account, or wrong PIN (all indistinguishable) |
| `TOKEN_MISSING` | 401 | no bearer token — the app should log out |
| `TOKEN_INVALID` | 401 | unknown, revoked or expired token — the app should log out |
| `ACCESS_DISABLED` | 403 | an existing token's employee had Mobile App Access turned off after login |
| `MOCK_LOCATION` | 403 | `is_mocked` is true and the company blocks mock locations |
| `OUTSIDE_LOCATION` | 403 | outside the geofence; `details: {distance, radius, location_name}` |
| `NOT_FOUND` | 404 | record missing or not owned by the caller |
| `LOCATION_NOT_CONFIGURED` | 409 | the work location/company has no coordinates or radius |
| `ALREADY_CHECKED_IN` | 409 | check-in while an attendance is already open |
| `NOT_CHECKED_IN` | 409 | check-out with no open attendance |
| `ACCOUNT_LOCKED` | 429 | too many failed logins; `details: {retry_after_seconds}` |
| `SERVER_ERROR` | 500 | unexpected error |

### A note on `INVALID_CREDENTIALS` vs `ACCESS_DISABLED`

At **login**, an unknown email, a wrong PIN, *and* a correct email+PIN for
an employee whose Mobile App Access is off are all indistinguishable
(`INVALID_CREDENTIALS`) — this avoids leaking account existence/status to
an unauthenticated caller. `ACCESS_DISABLED` is only returned to an
**already authenticated** session (valid bearer token) whose employee had
access revoked *after* they logged in — e.g. HR disables the employee
mid-session — so the app can show a clear "access disabled" message and log
out, rather than a generic "invalid credentials" on a call that isn't a
login.
