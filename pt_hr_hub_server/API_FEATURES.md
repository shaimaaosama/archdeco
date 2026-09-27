# PT HR Hub Server - API Features & Integration Guide

## Overview
The `pt_hr_hub_server` module provides complete **FaceIO facial recognition integration** with Odoo 18, supporting:
- ✅ **Employee Enrollment** with facial ID registration
- ✅ **Attendance Check-in** via facial recognition  
- ✅ **Attendance Check-out** via facial recognition
- ✅ **REST API** with OAuth2 protection (MuK REST)
- ✅ **Postman Collection** with ready-to-use examples
- ✅ **Web UI** for kiosk and browser-based enrollment

---

## 1. EMPLOYEE ENROLLMENT

### 1.1 Web UI (Browser-based)
**URL:** `http://your-odoo/hr_hub/faceio/enroll`
- HR Manager navigates to enrollment page
- Selects or searches for employee
- Clicks "Scan Face" to trigger FaceIO enrollment
- Saves facial ID to employee profile (field: `x_faceio_id`)

**Access:** HR Manager only (`hr.group_hr_manager`)

---

### 1.2 REST API (Programmatic)

#### Create Employee with Facial ID

**Endpoint:**
```
POST /api/v1/create?db={database_name}
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "hr.employee",
  "values": {
    "name": "John Doe",
    "work_email": "john.doe@company.com",
    "x_device_uuid": "e6fd8ef5-6d8e-4f72-99f5-9f5bb1dc8fd6",
    "x_faceio_id": "faceio_facial_id_from_enrollment"
  }
}
```

**Response:**
```json
[42]  // Returns employee ID
```

#### Update Employee with Facial ID (Post-Enrollment)

**Endpoint:**
```
PUT /api/v1/write?db={database_name}
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "hr.employee",
  "ids": [42],
  "values": {
    "x_faceio_id": "new_faceio_facial_id_from_enrollment",
    "x_device_uuid": "device_uuid_optional"
  }
}
```

**Response:**
```json
true
```

#### Read Employee Enrollment Status

**Endpoint:**
```
POST /api/v1/read?db={database_name}
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "hr.employee",
  "ids": [42],
  "fields": ["name", "x_faceio_id", "x_device_uuid"]
}
```

**Response:**
```json
[
  {
    "id": 42,
    "name": "John Doe",
    "x_faceio_id": "faceio_facial_id_from_enrollment",
    "x_device_uuid": "e6fd8ef5-6d8e-4f72-99f5-9f5bb1dc8fd6"
  }
]
```

---

## 2. ATTENDANCE CHECK-IN / CHECK-OUT

### 2.1 Web UI (Kiosk)
**URL:** `http://your-odoo/hr_hub/faceio/kiosk`
- Employee or receptionist clicks "Scan My Face"
- FaceIO authenticates the face
- System automatically:
  - Finds employee by facial ID
  - Creates check-in record (if no open attendance)
  - OR creates check-out record (if open attendance exists)
- Shows result: employee name, action (IN/OUT), timestamps, worked hours

**Access:** HR Users (`hr.group_hr_user`)

---

### 2.2 REST API (Mobile / External Systems)

#### Post Attendance via FaceIO ID

**Endpoint:**
```
POST /api/v1/hr_hub/attendance?db={database_name}
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "employee_id": 42,
  "device_uuid": "e6fd8ef5-6d8e-4f72-99f5-9f5bb1dc8fd6",
  "faceio_id": "faceio_facial_id_from_authenticate",
  "lat": 24.7136,
  "long": 46.6753
}
```

**Response (Check-in):**
```json
{
  "success": true,
  "attendance_id": 1024,
  "sync_state": "pending"
}
```

**What Happens Behind:**
- System finds employee where `x_faceio_id = faceio_id`
- Checks if employee has open (unclosed) attendance
- If NO open attendance → Creates **check-in** record with timestamps + geolocation
- If open attendance exists → Updates with **check-out** timestamp

#### Generic Attendance Create (via CRUD)

**Endpoint:**
```
POST /api/v1/create?db={database_name}
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "hr.attendance",
  "values": {
    "employee_id": 42,
    "check_in": "2026-04-21 08:30:00",
    "x_latitude": 24.7136,
    "x_longitude": 46.6753,
    "x_device_id_used": "e6fd8ef5-6d8e-4f72-99f5-9f5bb1dc8fd6"
  }
}
```

#### Update Attendance Check-out (via CRUD)

**Endpoint:**
```
PUT /api/v1/write?db={database_name}
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "hr.attendance",
  "ids": [1024],
  "values": {
    "check_out": "2026-04-21 17:30:00"
  }
}
```

#### Search Attendance Records

**Endpoint:**
```
POST /api/v1/search?db={database_name}
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "hr.attendance",
  "domain": [["employee_id", "=", 42]],
  "fields": ["employee_id", "check_in", "check_out", "x_latitude", "x_longitude"],
  "limit": 20,
  "order": "id desc"
}
```

---

## 3. POSTMAN COLLECTION EXAMPLES

All examples are in: `examples/pt_hr_hub_server.postman_collection.json`

### Workflow Flow:

1. **Auth** → OAuth2 Token (Client Credentials)
2. **Employee Data (CRUD)**
   - Create Employee (with x_faceio_id)
   - Read Employee
   - Update Employee
   - Delete Employee
3. **Hub Attendance Endpoint**
   - Create Attendance via pt_hr_hub_server (FaceIO method)
4. **Attendance (CRUD)**
   - Create Attendance (Generic)
   - Update Attendance (check_out)
   - Search Attendance
   - Delete Attendance

### Setup Instructions:

1. Import `pt_hr_hub_server.postman_collection.json` into Postman
2. Set Collection Variables:
   - `base_url`: `https://your-odoo-instance.com`
   - `db`: `HR_Community` (or your database)
   - `client_id`: OAuth2 client ID
   - `client_secret`: OAuth2 client secret
   - `employee_id`: Employee ID to test with
   - `faceio_id`: FaceIO facial ID from enrollment
   - `device_uuid`: Device identifier (UUID format)

3. Run Auth tab first to get `access_token`
4. Use other requests with the token

---

## 4. PYTHON CLIENT EXAMPLE

**File:** `examples/mobile_post_sample.py`

```python
#!/usr/bin/env python3
"""Sample mobile client flow for MuK REST + HR Hub attendance POST."""

import requests

BASE_URL = "https://your-hub-odoo.example.com"
DB_NAME = "hub_database_name"
CLIENT_ID = "oauth_client_id"
CLIENT_SECRET = "oauth_client_secret"

payload = {
    "employee_id": 42,
    "device_uuid": "e6fd8ef5-6d8e-4f72-99f5-9f5bb1dc8fd6",
    "faceio_id": "faceio_facial_id_from_authenticate",
    "lat": 24.7136,
    "long": 46.6753,
}

def fetch_oauth2_token():
    token_url = f"{BASE_URL}/api/v1/authentication/oauth2/token?db={DB_NAME}"
    response = requests.post(
        token_url,
        data={"grant_type": "client_credentials"},
        auth=(CLIENT_ID, CLIENT_SECRET),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]

def post_attendance(token):
    endpoint = f"{BASE_URL}/api/v1/hr_hub/attendance?db={DB_NAME}"
    response = requests.post(
        endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    access_token = fetch_oauth2_token()
    result = post_attendance(access_token)
    print(result)
```

---

## 5. GLOBAL FACEIO SETTINGS

**Location:** HR → Settings → FaceIO Configuration

**Parameters (stored in `ir.config_parameter`):**

| Parameter | Type | Purpose |
|-----------|------|---------|
| `pt_hr_hub_server.faceio_enabled` | Boolean | Enable/disable FaceIO globally |
| `pt_hr_hub_server.faceio_app_public_id` | String | FaceIO public app ID (from faceio.net) |
| `pt_hr_hub_server.faceio_secret_key_encrypted` | String | Encrypted FaceIO secret key (for server-side verification) |
| `pt_hr_hub_server.faceio_identity_endpoint` | String | FaceIO identity verification REST endpoint |

---

## 6. FIELD REFERENCE

### HR Employee Fields

| Field | Type | Purpose |
|-------|------|---------|
| `x_faceio_id` | Char | Unique facial ID from FaceIO enrollment |
| `x_device_uuid` | Char | Device UUID for mobile/kiosk device |
| `hub_client_config_id` | Many2one | Link to remote hub client (for sync) |

### HR Attendance Fields

| Field | Type | Purpose |
|-------|------|---------|
| `check_in` | Datetime | Check-in timestamp |
| `check_out` | Datetime | Check-out timestamp |
| `x_latitude` | Float | Latitude from geolocation |
| `x_longitude` | Float | Longitude from geolocation |
| `x_device_id_used` | Char | Device that recorded the attendance |
| `x_hub_verified` | Boolean | Marked as verified by hub |
| `x_sync_state` | Selection | Sync state to remote Odoo |

---

## 7. SECURITY NOTES

✅ **Authentication:** OAuth2 with Client Credentials flow (MuK REST)  
✅ **Authorization:** Role-based access control (hr.group_hr_user, hr.group_hr_manager)  
✅ **Data Encryption:** Facial IDs stored as-is; secret keys encrypted via Fernet  
✅ **Geolocation:** Optional but stored for audit trail  
✅ **Device Identification:** Device UUID optional but recommended for multi-location tracking  

---

## 8. INTEGRATION CHECKLIST

- [x] FaceIO SDK loaded via CDN
- [x] Global FaceIO settings in HR Settings
- [x] Employee model extended with facial ID fields
- [x] Attendance model extended with geolocation fields
- [x] REST API endpoint for attendance posting
- [x] Enrollment web UI (browser-based)
- [x] Attendance kiosk UI (browser-based)
- [x] Postman collection with full examples
- [x] Python client sample
- [x] OAuth2 authentication
- [x] Multi-tenant support (hub_client_config)
- [x] Sync to remote Odoo instances via XML-RPC

---

## 9. TROUBLESHOOTING

**Q: FaceIO SDK not loading?**  
A: Check `faceio_enabled` and `faceio_app_public_id` in HR Settings

**Q: Employee not found during attendance POST?**  
A: Ensure employee is enrolled first (x_faceio_id must match the faceio_id in request)

**Q: OAuth2 token invalid?**  
A: Verify client_id, client_secret, and database name in token request

**Q: Attendance not syncing to remote Odoo?**  
A: Check hub_client_config credentials and ensure "sync to hub" is enabled

---

## 10. SUMMARY TABLE

| Feature | Web UI | REST API | Postman | Python |
|---------|--------|----------|---------|--------|
| Enroll Employee | ✅ | ✅ | ✅ | ✅ |
| Check-in Attendance | ✅ | ✅ | ✅ | ✅ |
| Check-out Attendance | ✅ (auto) | ✅ (auto) | ✅ (auto) | ✅ (auto) |
| Read Employee Data | ✅ | ✅ | ✅ | ✅ |
| Search Attendance | ✅ | ✅ | ✅ | ✅ |
| OAuth2 Auth | N/A | ✅ | ✅ | ✅ |

**All features are fully supported across all integration methods!** ✅
