# 📅 BookMySlot – University Hall Booking System

A full-featured seminar and webinar hall booking platform for universities, built with **Python Flask**, **MySQL**, and **Bootstrap 5**.

---

## 🚀 Features

### Admin
- Secure login with bcrypt-hashed passwords
- Dashboard: total halls, bookings, pending approvals, today's schedule
- Add / edit / activate / deactivate seminar and webinar halls
- Approve or reject faculty booking requests (with notes)
- View all bookings with status filters
- Manage faculty accounts (add, activate, deactivate)
- Real-time notifications

### Faculty
- Secure login and self-registration
- Dashboard: upcoming bookings, pending requests, notifications
- View real-time hall availability by hall + date
- Submit booking requests (with conflict detection)
- View booking status: pending / approved / rejected / cancelled
- Cancel their own bookings
- Full booking history

---

## 🏗️ Project Structure

```
BookMySlot/
├── app.py                  ← Flask app + all routes
├── config.py               ← Configuration (DB, secret key)
├── database.sql            ← MySQL schema + sample data
├── requirements.txt        ← Python dependencies
├── README.md
│
├── modules/
│   ├── __init__.py
│   ├── auth.py             ← Login, logout, decorators, bcrypt
│   ├── booking.py          ← Booking logic, conflict detection
│   └── admin.py            ← Admin utilities, dashboard stats
│
├── templates/
│   ├── base.html           ← Sidebar layout (shared)
│   ├── login.html          ← Login page
│   ├── register.html       ← Faculty self-registration
│   ├── faculty_dashboard.html
│   ├── admin_dashboard.html
│   ├── book_hall.html      ← Booking form
│   ├── view_bookings.html  ← Faculty booking history
│   ├── hall_availability.html
│   ├── admin_bookings.html ← Admin: all bookings + approve/reject
│   ├── manage_halls.html   ← Admin: hall CRUD
│   └── manage_faculty.html ← Admin: faculty management
│
└── static/
    ├── css/style.css       ← Custom styles (Navy + Amber theme)
    └── js/main.js          ← Slot checker, confirmations, search
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### Step 1 – Clone / Download the project

```bash
cd BookMySlot
```

### Step 2 – Create a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 – Install dependencies

```bash
pip install -r requirements.txt
```

> **Note (Ubuntu/Debian):** If `mysqlclient` fails, install the system library first:
> ```bash
> sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
> ```

### Step 4 – Set up MySQL

```bash
mysql -u root -p
```

```sql
SOURCE database.sql;
```

Or run it directly:
```bash
mysql -u root -p < database.sql
```

### Step 5 – Configure database credentials

Edit **`config.py`**:

```python
MYSQL_USER     = 'root'           # your MySQL username
MYSQL_PASSWORD = 'your_password'  # your MySQL password
MYSQL_DB       = 'bookmyslot'
```

### Step 6 – Run the application

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## 🔐 Demo Login Credentials

| Role    | Email                          | Password    |
|---------|--------------------------------|-------------|
| Admin   | admin@university.edu           | Admin@123   |
| Faculty | ramesh.patel@university.edu    | Faculty@123 |
| Faculty | priya.mehta@university.edu     | Faculty@123 |

> The sample data includes pre-hashed passwords. See `database.sql` for details.

> **Note:** The hashes in `database.sql` use standard bcrypt. If login fails with sample data, re-hash via:
> ```python
> import bcrypt
> print(bcrypt.hashpw(b'Admin@123', bcrypt.gensalt(12)).decode())
> ```
> Then UPDATE the password field in MySQL.

---

## 🗄️ Database Schema

| Table         | Key Columns                                                     |
|---------------|-----------------------------------------------------------------|
| `users`       | id, name, email, password (bcrypt), role, department, is_active |
| `halls`       | id, hall_name, capacity, location, facilities, is_active        |
| `bookings`    | id, user_id, hall_id, date, start_time, end_time, event_title, status |
| `notifications`| id, user_id, message, is_read, created_at                     |

---

## 🔒 Security Features

- Passwords hashed with **bcrypt** (cost factor 12)
- Flask `SECRET_KEY` for session signing
- Login-required and role-based decorators on every route
- Double-booking conflict check before insertion
- HTML form input validation (client + server side)

---

## 📦 Python Packages

```
Flask==3.0.3
Flask-MySQLdb==2.0.0
bcrypt==4.1.3
Werkzeug==3.0.3
mysqlclient==2.2.4
python-dotenv==1.0.1
```

---

## 🎨 UI Design

- **Theme:** Navy blue + Amber accent — refined academic aesthetic
- **Fonts:** Playfair Display (headings) + DM Sans (body)
- **Framework:** Bootstrap 5.3 + Bootstrap Icons 1.11
- **Layout:** Fixed sidebar + main content area
- **Responsive:** Mobile-friendly with hamburger sidebar
- **Features:** Real-time slot availability checker (AJAX), auto-dismiss alerts, confirm dialogs

---

## 📝 License

This project is for educational purposes. Adapt freely for your university's needs.

# BookMySlot