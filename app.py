import os
import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

bcrypt = Bcrypt(app)
mail   = Mail(app)

    # ── DB connection helper (replaces flask_mysqldb) ──
def get_db():
        conn = pymysql.connect(
            host        = app.config['MYSQL_HOST'],
            user        = app.config['MYSQL_USER'],
            password    = app.config['MYSQL_PASSWORD'],
            database    = app.config['MYSQL_DB'],
            cursorclass = pymysql.cursors.DictCursor
        )
        return conn
def ensure_database():
        """Ensure DB exists and load schema from database.sql if needed."""
        try:
            conn = get_db()
            conn.close()
            return
        except pymysql.err.OperationalError as exc:
            # 1049: Unknown database; 1146: table missing
            if exc.args[0] != 1049:
                raise

            # create database if not present
            base_conn = pymysql.connect(
                host        = app.config['MYSQL_HOST'],
                user        = app.config['MYSQL_USER'],
                password    = app.config['MYSQL_PASSWORD'],
                cursorclass = pymysql.cursors.DictCursor
            )
            base_cur = base_conn.cursor()
            base_cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{app.config['MYSQL_DB']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            base_conn.commit()
            base_cur.close()
            base_conn.close()

            # reload schema from SQL file
            sql_path = os.path.join(app.root_path, 'database.sql')
            if not os.path.isfile(sql_path):
                raise FileNotFoundError(f"database.sql not found at {sql_path}")

            with open(sql_path, 'r', encoding='utf8') as f:
                sql_text = f.read()

            conn = get_db()
            cur = conn.cursor()
            for statement in sql_text.split(';'):
                stmt = statement.strip()
                if not stmt:
                    continue
                cur.execute(stmt)
            conn.commit()
            cur.close()
            conn.close()


    # ── Old mysql object for backward compatibility ──
class MySQLCompat:
        @property
        def connection(self):
            return get_db()

mysql = MySQLCompat()

    # ── Imports ────────────────────────────────────────
from modules.auth    import (hash_password, check_password, login_user,
                                logout_user, login_required, admin_required,
                                faculty_required, current_user)
from modules.booking import (is_slot_available, create_booking, cancel_booking,
                                approve_booking, reject_booking,
                                get_hall_bookings_for_date,
                                create_notification_for_status_change)
from modules.admin   import (get_dashboard_stats, get_all_bookings, add_hall,
                                update_hall, toggle_hall_status, get_all_faculty,
                                toggle_faculty_status)


    # ── Jinja2 custom filter ─────────────────────────────────────
from datetime import date as _date

@app.template_filter('today_date')
def today_date_filter(_):
        """Return today's date as YYYY-MM-DD (used in templates)."""
        return _date.today().isoformat()

@app.template_filter('slice')
def slice_filter(value, length):
        """Slice a string/timedelta representation."""
        return str(value)[:length]

    # Make today_date available as a global in templates
app.jinja_env.globals['today'] = _date.today().isoformat

    # (Flask 3+ might not support before_first_request in this environment)
    # We'll initialize database on app start in the main block.

    # ── Context Processor ─────────────────────────────────────────
@app.context_processor
def inject_user():
        """Make current_user and unread_count available in all templates."""
        user = current_user()
        unread = 0
        if user:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM notifications WHERE user_id=%s AND is_read=0",
                        (user['id'],))
            unread = cur.fetchone()['cnt']
            cur.close()
            conn.close()
        return dict(current_user=user, unread_notifications=unread)


    # ═══════════════════════════════════════════════════════════════
    #  AUTH ROUTES
    # ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
        if 'user_id' in session:
            if session['user_role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('faculty_dashboard'))
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
        if 'user_id' in session:
            return redirect(url_for('index'))

        if request.method == 'POST':
            email    = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            if not email or not password:
                flash('Email and password are required.', 'danger')
                return render_template('login.html')

            conn = get_db()
            cur = conn.cursor()
            # Query both admin AND faculty users
            cur.execute("SELECT * FROM users WHERE email=%s AND is_active=1", (email,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and check_password(password, user['password']):
                login_user(user)
                flash(f'Welcome back, {user["name"]}!', 'success')
                # Redirect based on role
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('faculty_dashboard'))

            flash('Invalid email or password.', 'danger')

        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
        name = session.get('user_name', '')
        logout_user()
        flash(f'Goodbye, {name}! You have been logged out.', 'info')
        return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
        """Self-registration for faculty (admin must activate if needed)."""
        if request.method == 'POST':
            name       = request.form.get('name', '').strip()
            email      = request.form.get('email', '').strip().lower()
            password   = request.form.get('password', '')
            department = request.form.get('department', '').strip()
            phone      = request.form.get('phone', '').strip()

            if not all([name, email, password, department]):
                flash('All fields are required.', 'danger')
                return render_template('register.html')

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                flash('An account with this email already exists.', 'warning')
                cur.close()
                conn.close()
                return render_template('register.html')

            hashed = hash_password(password)
            cur.execute("""
                INSERT INTO users (name, email, password, role, department, phone)
                VALUES (%s, %s, %s, 'faculty', %s, %s)
            """, (name, email, hashed, department, phone))
            conn.commit()
            cur.close()
            conn.close()
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')


    # ═══════════════════════════════════════════════════════════════
    #  FACULTY ROUTES
    # ═══════════════════════════════════════════════════════════════

@app.route('/faculty/dashboard')
@faculty_required
def faculty_dashboard():
        user_id = session['user_id']
        conn = get_db()
        cur = conn.cursor()

        # Upcoming approved bookings
        cur.execute("""
            SELECT b.*, h.hall_name, h.location
            FROM   bookings b
            JOIN   halls    h ON h.id = b.hall_id
            WHERE  b.user_id = %s AND b.date >= CURDATE()
            AND    b.status  = 'approved'
            ORDER  BY b.date, b.start_time
            LIMIT  5
        """, (user_id,))
        upcoming = cur.fetchall()

        # Pending requests
        cur.execute("""
            SELECT b.*, h.hall_name FROM bookings b
            JOIN halls h ON h.id = b.hall_id
            WHERE b.user_id = %s AND b.status = 'pending'
            ORDER BY b.created_at DESC
        """, (user_id,))
        pending = cur.fetchall()

        # Stats
        cur.execute("SELECT COUNT(*) AS cnt FROM bookings WHERE user_id=%s", (user_id,))
        total = cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) AS cnt FROM bookings WHERE user_id=%s AND status='approved'", (user_id,))
        approved_count = cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) AS cnt FROM bookings WHERE user_id=%s AND status='pending'", (user_id,))
        pending_count = cur.fetchone()['cnt']

        # Notifications
        cur.execute("""
            SELECT * FROM notifications WHERE user_id=%s
            ORDER BY created_at DESC LIMIT 5
        """, (user_id,))
        notifs = cur.fetchall()
        cur.execute("UPDATE notifications SET is_read=1 WHERE user_id=%s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()

        return render_template('faculty_dashboard.html',
                            upcoming=upcoming, pending=pending,
                            total=total, approved_count=approved_count,
                            pending_count=pending_count, notifs=notifs)


@app.route('/faculty/book', methods=['GET', 'POST'])
@faculty_required
def book_hall():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM halls WHERE is_active=1 ORDER BY hall_name")
        halls = cur.fetchall()
        cur.close()
        conn.close()

        if request.method == 'POST':
            hall_id     = request.form.get('hall_id')
            date        = request.form.get('date')
            start_time  = request.form.get('start_time')
            end_time    = request.form.get('end_time')
            event_title = request.form.get('event_title', '').strip()
            description = request.form.get('description', '').strip()
            attendees   = int(request.form.get('attendees', 0))

            if not all([hall_id, date, start_time, end_time, event_title]):
                flash('All required fields must be filled.', 'danger')
                return render_template('book_hall.html', halls=halls)

            # Use a DB cursor with booking helper
            conn = get_db()
            cur = conn.cursor()
            try:
                # Check slot availability before creating booking
                if not is_slot_available(cur, int(hall_id), date, start_time, end_time):
                    flash('Selected slot is already booked.', 'danger')
                    return render_template('book_hall.html', halls=halls)

                booking_id = create_booking(cur, session['user_id'], int(hall_id),
                                            date, start_time, end_time,
                                            event_title, description, attendees)
                conn.commit()
                flash('Booking request submitted successfully.', 'success')
                return redirect(url_for('my_bookings'))
            finally:
                cur.close()
                conn.close()

        return render_template('book_hall.html', halls=halls)


@app.route('/faculty/bookings')
@faculty_required
def my_bookings():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT b.*, h.hall_name, h.location, h.capacity
            FROM   bookings b
            JOIN   halls    h ON h.id = b.hall_id
            WHERE  b.user_id = %s
            ORDER  BY b.id ASC
        """, (session['user_id'],))
        bookings = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('view_bookings.html', bookings=bookings)


@app.route('/faculty/cancel/<int:booking_id>', methods=['POST'])
@faculty_required
def cancel_my_booking(booking_id):
        conn = get_db()
        cur = conn.cursor()
        ok = cancel_booking(cur, booking_id, session['user_id'])
        if ok:
            conn.commit()
        cur.close()
        conn.close()
        flash('Booking cancelled.' if ok else 'Unable to cancel booking.', 'success' if ok else 'danger')
        return redirect(url_for('my_bookings'))


@app.route('/faculty/availability')
@faculty_required
def hall_availability():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM halls WHERE is_active=1 ORDER BY hall_name")
        halls = cur.fetchall()
        cur.close()
        conn.close()

        selected_hall = request.args.get('hall_id')
        selected_date = request.args.get('date')
        bookings = []
        hall_info = None

        if selected_hall and selected_date:
            conn = get_db()
            cur = conn.cursor()
            bookings = get_hall_bookings_for_date(cur, int(selected_hall), selected_date)
            cur.execute("SELECT * FROM halls WHERE id=%s", (selected_hall,))
            hall_info = cur.fetchone()
            cur.close()
            conn.close()

        return render_template('hall_availability.html',
                            halls=halls, bookings=bookings,
                            hall_info=hall_info,
                            selected_hall=selected_hall,
                            selected_date=selected_date)


    # ═══════════════════════════════════════════════════════════════
    #  NOTIFICATIONS ROUTES
    # ═══════════════════════════════════════════════════════════════ 
@app.route('/notifications')
@login_required
def notifications():
        """Display user notifications for approval/rejection decisions."""
        user_id = session['user_id']
        conn = get_db()
        cur = conn.cursor()
        
        # Get all unread notifications
        cur.execute("""
            SELECT id, message, created_at, is_read
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))
        notifications_list = cur.fetchall()
        
        # Mark notifications as read
        cur.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE user_id = %s AND is_read = 0
        """, (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return render_template('notifications.html', notifications=notifications_list)


@app.route('/api/notifications/count')
@login_required
def notifications_count():
        """API endpoint to get count of unread notifications."""
        user_id = session['user_id']
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM notifications
            WHERE user_id = %s AND is_read = 0
        """, (user_id,))
        count = cur.fetchone()['cnt']
        cur.close()
        conn.close()
        
        return jsonify({'unread_count': count})


    # ═══════════════════════════════════════════════════════════════
    #  ADMIN ROUTES
    # ═══════════════════════════════════════════════════════════════

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
        conn = get_db()
        stats = get_dashboard_stats(conn)
        cur = conn.cursor()

        cur.execute("""
            SELECT b.*, u.name AS faculty_name, h.hall_name
            FROM   bookings b JOIN users u ON u.id=b.user_id JOIN halls h ON h.id=b.hall_id
            WHERE  b.status = 'pending'
            ORDER  BY b.created_at DESC LIMIT 5
        """)
        pending_bookings = cur.fetchall()

        cur.execute("""
            SELECT b.*, u.name AS faculty_name, h.hall_name
            FROM   bookings b JOIN users u ON u.id=b.user_id JOIN halls h ON h.id=b.hall_id
            WHERE  b.date = CURDATE() AND b.status = 'approved'
            ORDER  BY b.start_time
        """)
        today_bookings = cur.fetchall()

        # Notifications for admin
        cur.execute("""
            SELECT * FROM notifications WHERE user_id=%s
            ORDER BY created_at DESC LIMIT 8
        """, (session['user_id'],))
        notifs = cur.fetchall()
        cur.execute("UPDATE notifications SET is_read=1 WHERE user_id=%s", (session['user_id'],))
        conn.commit()
        cur.close()
        conn.close()

        return render_template('admin_dashboard.html',
                            stats=stats, pending_bookings=pending_bookings,
                            today_bookings=today_bookings, notifs=notifs)


@app.route('/admin/bookings')
@admin_required
def admin_bookings():
        status_filter = request.args.get('status', 'all')
        conn = get_db()
        bookings = get_all_bookings(conn, status_filter)
        conn.close()
        return render_template('admin_bookings.html',
                            bookings=bookings, status_filter=status_filter)


@app.route('/admin/approve/<int:booking_id>', methods=['POST'])
@admin_required
def admin_approve(booking_id):
        note = request.form.get('note', '')
        conn = get_db()
        cur = conn.cursor()
        ok, msg = approve_booking(cur, booking_id, note)
        
        # Create notification and send email
        notification_data = create_notification_for_status_change(cur, booking_id, 'approved', note)
        conn.commit()
        
        # Send email notification
        if notification_data and notification_data['faculty_email']:
            try:
                email_subject = f"Booking Approved: {notification_data['event_title']}"
                email_body = f"""
    Dear {notification_data['faculty_name']},

    Your booking request has been APPROVED! 🎉

    Event Details:
    • Event: {notification_data['event_title']}
    • Date: {notification_data['booking_date']}
    • Time: {notification_data['start_time']} - {notification_data['end_time']}
    • Hall: {notification_data['hall_name']} ({notification_data['location']})

    Admin Note: {note if note else 'None'}

    Please proceed with your event preparations.

    Best regards,
    BookMySlot - Hall Booking System
                """
                email_msg = Message(email_subject, recipients=[notification_data['faculty_email']], body=email_body)
                mail.send(email_msg)
            except Exception as e:
                print(f"Error sending email: {e}")
        
        cur.close()
        flash(msg, 'success' if ok else 'danger')
        return redirect(url_for('admin_bookings'))


@app.route('/admin/reject/<int:booking_id>', methods=['POST'])
@admin_required
def admin_reject(booking_id):
        note = request.form.get('note', 'No reason provided.')
        conn = get_db()
        cur = conn.cursor()
        ok, msg = reject_booking(cur, booking_id, note)
        
        # Create notification and send email
        notification_data = create_notification_for_status_change(cur, booking_id, 'rejected', note)
        conn.commit()
        
        # Send email notification
        if notification_data and notification_data['faculty_email']:
            try:
                email_subject = f"Booking Rejected: {notification_data['event_title']}"
                email_body = f"""
    Dear {notification_data['faculty_name']},

    Unfortunately, your booking request has been REJECTED. ❌

    Event Details:
    • Event: {notification_data['event_title']}
    • Requested Date: {notification_data['booking_date']}
    • Time: {notification_data['start_time']} - {notification_data['end_time']}
    • Hall: {notification_data['hall_name']} ({notification_data['location']})

    Reason: {note}

    Please try booking a different time slot or contact us for more information.

    Best regards,
    BookMySlot - Hall Booking System
                """
                email_msg = Message(email_subject, recipients=[notification_data['faculty_email']], body=email_body)
                mail.send(email_msg)
            except Exception as e:
                print(f"Error sending email: {e}")
        
        cur.close()
        flash(msg, 'success' if ok else 'danger')
        return redirect(url_for('admin_bookings'))


@app.route('/admin/halls', methods=['GET', 'POST'])
@admin_required
def manage_halls():

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            conn = get_db()
            ok, msg = add_hall(
                conn,
                request.form.get('hall_name', '').strip(),
                int(request.form.get('capacity', 0)),
                request.form.get('location', '').strip(),
                request.form.get('description', '').strip(),
                ','.join(request.form.getlist('facilities'))
            )
            conn.close()
            flash(msg, 'success' if ok else 'danger')

        elif action == 'edit':
            conn = get_db()
            ok, msg = update_hall(
                conn,
                int(request.form.get('hall_id')),
                request.form.get('hall_name', '').strip(),
                int(request.form.get('capacity', 0)),
                request.form.get('location', '').strip(),
                request.form.get('description', '').strip(),
                ','.join(request.form.getlist('facilities'))
            )
            conn.close()
            flash(msg, 'success' if ok else 'danger')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM halls ORDER BY hall_name")
    halls = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('manage_halls.html', halls=halls)
@app.route('/admin/halls/toggle/<int:hall_id>', methods=['POST'])
@admin_required
def toggle_hall(hall_id):
    conn = get_db()
    ok, msg = toggle_hall_status(conn, hall_id)
    conn.close()
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('manage_halls'))


@app.route('/admin/faculty')
@admin_required
def manage_faculty():
    conn = get_db()
    faculty = get_all_faculty(conn)
    conn.close()
    return render_template('manage_faculty.html', faculty=faculty)


@app.route('/admin/faculty/toggle/<int:user_id>', methods=['POST'])
@admin_required
def toggle_faculty(user_id):
    conn = get_db()
    ok, msg = toggle_faculty_status(conn, user_id)
    conn.close()
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('manage_faculty'))


@app.route('/admin/faculty/add', methods=['POST'])
@admin_required
def add_faculty():
    name       = request.form.get('name', '').strip()
    email      = request.form.get('email', '').strip().lower()
    password   = request.form.get('password', '')
    department = request.form.get('department', '').strip()
    phone      = request.form.get('phone', '').strip()

    if not all([name, email, password]):
        flash('Name, email and password are required.', 'danger')
        return redirect(url_for('manage_faculty'))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        flash('Email already exists.', 'warning')
        cur.close()
        conn.close()
        return redirect(url_for('manage_faculty'))

    cur.execute("""
        INSERT INTO users (name, email, password, role, department, phone)
        VALUES (%s, %s, %s, 'faculty', %s, %s)
    """, (name, email, hash_password(password), department, phone))
    conn.commit()
    cur.close()
    conn.close()
    flash(f'Faculty account for {name} created.', 'success')
    return redirect(url_for('manage_faculty'))


# ── API: check slot availability (AJAX) ──────────────────────
@app.route('/api/check-slot')
@login_required
def api_check_slot():
    hall_id    = request.args.get('hall_id')
    date       = request.args.get('date')
    start_time = request.args.get('start_time')
    end_time   = request.args.get('end_time')

    if not all([hall_id, date, start_time, end_time]):
        return jsonify({'available': None, 'message': 'Missing parameters'})

    # Use a real DB cursor with the booking helper
    conn = get_db()
    cur = conn.cursor()
    available = is_slot_available(cur, int(hall_id), date, start_time, end_time)
    cur.close()
    conn.close()

    return jsonify({
        'available': available,
        'message': 'Slot is available!' if available else 'Slot already booked!'
    })


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    ensure_database()
    app.run(debug=True, port=5000)