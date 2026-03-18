# ============================================================
#  modules/admin.py – Admin utilities
# ============================================================


def get_dashboard_stats(mysql) -> dict:
    """Return counts used on the admin dashboard."""
    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) AS cnt FROM halls WHERE is_active = 1")
    total_halls = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM bookings")
    total_bookings = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM bookings WHERE status = 'pending'")
    pending = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM bookings WHERE status = 'approved'")
    approved = cur.fetchone()['cnt']

    cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE role = 'faculty' AND is_active = 1")
    total_faculty = cur.fetchone()['cnt']

    cur.execute("""
        SELECT COUNT(*) AS cnt FROM bookings
        WHERE date = CURDATE() AND status = 'approved'
    """)
    today_bookings = cur.fetchone()['cnt']

    cur.close()
    return {
        'total_halls':    total_halls,
        'total_bookings': total_bookings,
        'pending':        pending,
        'approved':       approved,
        'total_faculty':  total_faculty,
        'today_bookings': today_bookings,
    }


def get_all_bookings(mysql, status_filter: str = None) -> list:
    """Return all bookings with hall and user details, optionally filtered."""
    cur = mysql.connection.cursor()
    sql = """
        SELECT b.*, u.name AS faculty_name, u.department,
               h.hall_name, h.location
        FROM   bookings b
        JOIN   users    u ON u.id = b.user_id
        JOIN   halls    h ON h.id = b.hall_id
    """
    if status_filter and status_filter != 'all':
        sql += " WHERE b.status = %s"
        cur.execute(sql + " ORDER BY b.created_at DESC", (status_filter,))
    else:
        cur.execute(sql + " ORDER BY b.created_at DESC")

    rows = cur.fetchall()
    cur.close()
    return rows


def add_hall(mysql, hall_name: str, capacity: int, location: str,
             description: str, facilities: str) -> tuple[bool, str]:
    """Add a new seminar/webinar hall."""
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO halls (hall_name, capacity, location, description, facilities)
        VALUES (%s, %s, %s, %s, %s)
    """, (hall_name, capacity, location, description, facilities))
    mysql.connection.commit()
    cur.close()
    return True, f'Hall "{hall_name}" added successfully.'


def update_hall(mysql, hall_id: int, hall_name: str, capacity: int,
                location: str, description: str, facilities: str) -> tuple[bool, str]:
    """Update hall details."""
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE halls
        SET hall_name=%s, capacity=%s, location=%s, description=%s, facilities=%s
        WHERE id=%s
    """, (hall_name, capacity, location, description, facilities, hall_id))
    mysql.connection.commit()
    cur.close()
    return True, 'Hall updated successfully.'


def toggle_hall_status(mysql, hall_id: int) -> tuple[bool, str]:
    """Activate / deactivate a hall."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT is_active FROM halls WHERE id = %s", (hall_id,))
    hall = cur.fetchone()
    if not hall:
        cur.close()
        return False, 'Hall not found.'
    new_status = 0 if hall['is_active'] else 1
    cur.execute("UPDATE halls SET is_active = %s WHERE id = %s", (new_status, hall_id))
    mysql.connection.commit()
    cur.close()
    label = 'activated' if new_status else 'deactivated'
    return True, f'Hall {label} successfully.'


def get_all_faculty(mysql) -> list:
    """Return all faculty accounts."""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.*, COUNT(b.id) AS booking_count
        FROM   users u
        LEFT JOIN bookings b ON b.user_id = u.id
        WHERE  u.role = 'faculty'
        GROUP  BY u.id
        ORDER  BY u.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


def toggle_faculty_status(mysql, user_id: int) -> tuple[bool, str]:
    """Enable / disable a faculty account."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT is_active, name FROM users WHERE id = %s AND role = 'faculty'", (user_id,))
    user = cur.fetchone()
    if not user:
        cur.close()
        return False, 'Faculty not found.'
    new_status = 0 if user['is_active'] else 1
    cur.execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id))
    mysql.connection.commit()
    cur.close()
    label = 'activated' if new_status else 'deactivated'
    return True, f'Account for {user["name"]} {label}.'
