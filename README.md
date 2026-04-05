# Finance dashboard  

A backend API for a finance dashboard system built with **Flask** and **SQLite**. It supports role-based access control, financial record management, and dashboard-level summary analytics.

## Tech stack

- **Language:** Python 3
- **Framework:** Flask
- **Database:** SQLite 
- **Auth:** Token-based 
- **Password Hashing:** Werkzeug (bcrypt-style)

## Why these choices

I chose Flask because I've used it in projects before and it gives me full control over how things are structured without too much magic. SQLite is simple to set up and works well for this scope — no need to configure a separate DB server. For auth, I went with a simple token-based approach (tokens stored in a `user_sessions` table) instead of JWT, because it's easier to invalidate on logout and straightforward to reason about.

## Project structure

```
finance_backend/
├── app.py                  # App factory, blueprint registration, DB init
├── requirements.txt
├── models/
│   ├── db.py               # SQLAlchemy instance
│   ├── user.py             # User model
│   ├── session.py          # Session/token model
│   └── record.py           # FinancialRecord model
├── routes/
│   ├── auth.py             # Login, logout, /me
│   ├── users.py            # User CRUD and role/status management
│   ├── records.py          # Financial record CRUD with filters
│   └── dashboard.py        # Summary, category, monthly, weekly, recent
└── middleware/
    └── auth.py             # login_required and role_required decorators
```

## Setup instructions

```bash
# 1. Clone or download the project
cd finance_backend

# 2. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

The server starts at `http://localhost:5000`

A default admin account is automatically created on first run:
- **Email:** admin@finance.com
- **Password:** admin123


## Roles and permissions

| Action                        | Viewer | Analyst | Admin |
|-------------------------------|--------|---------|-------|
| Login / Logout                | ✅     | ✅      | ✅    |
| View records                  | ✅     | ✅      | ✅    |
| View dashboard summaries      | ✅     | ✅      | ✅    |
| Create / update records       | ❌     | ✅      | ✅    |
| Delete records (soft)         | ❌     | ❌      | ✅    |
| View all users                | ❌     | ❌      | ✅    |
| Create users / assign roles   | ❌     | ❌      | ✅    |
| Activate / deactivate users   | ❌     | ❌      | ✅    |

## API reference

**Login request body:**
```json
{
  "email": "admin@finance.com",
  "password": "admin123"
}
```

**Login response:**
```json
{
  "token": "abc123...",
  "user": { "id": 1, "name": "Admin User", "role": "admin" }
}
```

All authenticated endpoints require the header:
```
Authorization: Bearer <token>
```

### Users (Admin only, except /users/:id for own profile)

| Method | Endpoint                   | Description              |
|--------|----------------------------|--------------------------|
| GET    | /users/                    | List all users           |
| GET    | /users/:id                 | Get user by ID           |
| POST   | /users/                    | Create a new user        |
| PATCH  | /users/:id/role            | Update user role         |
| PATCH  | /users/:id/status          | Activate/deactivate user |
| DELETE | /users/:id                 | Delete user              |

**Create user body:**
```json
{
  "name": "Rahul Sharma",
  "email": "rahul@company.com",
  "password": "pass123",
  "role": "analyst"
}
```

### Financial records

| Method | Endpoint          | Description                    | Role Required     |
|--------|-------------------|--------------------------------|-------------------|
| GET    | /records/         | List records (with filters)    | Any logged-in     |
| GET    | /records/:id      | Get one record                 | Any logged-in     |
| POST   | /records/         | Create a record                | Admin / Analyst   |
| PUT    | /records/:id      | Update a record                | Admin / Analyst   |
| DELETE | /records/:id      | Soft-delete a record           | Admin only        |

**Create record body:**
```json
{
  "amount": 50000,
  "type": "income",
  "category": "Salary",
  "date": "2026-04-01",
  "notes": "April salary credit"
}
```

**Filters (query params on GET /records/):**
- `type` — `income` or `expense`
- `category` — partial match, case-insensitive
- `start_date` — YYYY-MM-DD
- `end_date` — YYYY-MM-DD
- `page` — page number (default 1)
- `per_page` — records per page (default 10)

Example:
```
GET /records/?type=expense&category=rent&start_date=2026-01-01
```

### Dashboard

| Method | Endpoint                  | Description                           | Role Required |
|--------|---------------------------|---------------------------------------|---------------|
| GET    | /dashboard/summary        | Total income, expenses, net balance   | Any logged-in |
| GET    | /dashboard/by-category    | Totals grouped by category + type     | Any logged-in |
| GET    | /dashboard/recent         | Last N records (default 5, max 50)    | Any logged-in |
| GET    | /dashboard/monthly        | Monthly trends for a year             | Any logged-in |
| GET    | /dashboard/weekly         | Last 7 days income vs expense         | Any logged-in |

**Example responses:**

`GET /dashboard/summary`
```json
{
  "total_income": 50000.0,
  "total_expense": 15000.0,
  "net_balance": 35000.0
}
```

`GET /dashboard/monthly?year=2026`
```json
{
  "year": 2026,
  "trends": [
    { "month": "Jan", "income": 0, "expense": 0 },
    { "month": "Apr", "income": 50000.0, "expense": 15000.0 },
    ...
  ]
}
```

## Design decisions and assumptions

1. **Soft deletes** : Financial records are never permanently deleted. This is a common pattern in finance apps for audit trail purposes.

2. **Token invalidation on logout** : Unlike JWT, my tokens are stored in the DB so they can actually be revoked. I felt this made more sense for a dashboard system where sessions need to be controllable.

3. **Analysts can create/update but not delete** : I assumed analysts work with the data regularly but deletion should require admin approval to prevent accidental loss.

4. **Viewers can see everything** : The dashboard and records are read-only for viewers. They exist to consume reports, not manage data.

5. **Admin can't delete their own account** : Simple protection to prevent accidentally locking out the system.

6. **Pagination is built into GET /records/** : Defaults to 10 per page, avoids returning thousands of records in one shot.

7. **No email verification** : Out of scope for this assignment. Assumed users are created by an admin directly.

## Error response format

All errors return JSON:
```json
{
  "error": "Description of what went wrong"
}
```

HTTP status codes used:
 `200` : OK
 `201` : Created
 `400` : Bad request / validation error
 `401` : Not logged in
 `403` : Logged in but not allowed
 `404` : Resource not found
- `409` : Conflict (e.g. duplicate email)
