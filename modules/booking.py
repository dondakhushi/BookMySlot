

"""
booking.py - Booking business logic
No circular imports - all functions are self-contained
"""
 
 
def is_slot_available(cur, hall_id, date, start_time, end_time, exclude_id=None):
    """
    Returns True if the slot is FREE, False if already booked.
    Overlap condition: existing.start < new.end AND existing.end > new.start
    """
    sql = """
        SELECT id FROM bookings
        WHERE  hall_id    = %s
          AND  date       = %s
          AND  status NOT IN ('rejected', 'cancelled')
          AND  start_time < %s
          AND  end_time   > %s
    """
    params = [hall_id, date, end_time, start_time]
 
    if exclude_id:
        sql += " AND id != %s"
        params.append(exclude_id)
 
    cur.execute(sql, params)
    return cur.fetchone() is None
 
 
def check_conflict(cur, hall_id, date, start_time, end_time, exclude_id=None):
    return not is_slot_available(cur, hall_id, date, start_time, end_time, exclude_id)
 
 
def create_booking(cur, user_id, hall_id, date,
                   start_time, end_time, event_title,
                   description, attendees):
    cur.execute("""
        INSERT INTO bookings
            (user_id, hall_id, date, start_time, end_time,
             event_title, description, attendees, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
    """, (user_id, hall_id, date, start_time, end_time,
          event_title, description, attendees))
    return cur.lastrowid
 
 
def get_booking_by_id(cur, booking_id):
    cur.execute("""
        SELECT b.*, u.name AS faculty_name, u.email AS faculty_email,
               h.hall_name, h.location
        FROM   bookings b
        JOIN   users    u ON b.user_id = u.id
        JOIN   halls    h ON b.hall_id = h.id
        WHERE  b.id = %s
    """, (booking_id,))
    return cur.fetchone()
 
 
def get_user_bookings(cur, user_id):
    cur.execute("""
        SELECT b.*, h.hall_name, h.location
        FROM   bookings b
        JOIN   halls    h ON b.hall_id = h.id
        WHERE  b.user_id = %s
        ORDER  BY b.date DESC, b.start_time DESC
    """, (user_id,))
    return cur.fetchall()
 
 
def get_all_bookings(cur):
    cur.execute("""
        SELECT b.*, u.name AS faculty_name, h.hall_name, h.location
        FROM   bookings b
        JOIN   users    u ON b.user_id = u.id
        JOIN   halls    h ON b.hall_id = h.id
        ORDER  BY b.created_at DESC
    """)
    return cur.fetchall()
 
 
def get_pending_bookings(cur):
    cur.execute("""
        SELECT b.*, u.name AS faculty_name, u.email AS faculty_email,
               h.hall_name, h.location
        FROM   bookings b
        JOIN   users    u ON b.user_id = u.id
        JOIN   halls    h ON b.hall_id = h.id
        WHERE  b.status = 'pending'
        ORDER  BY b.created_at ASC
    """)
    return cur.fetchall()
 
 
def get_approved_bookings(cur):
    cur.execute("""
        SELECT b.id, b.event_title, b.date, b.start_time, b.end_time,
               u.name AS faculty_name, h.hall_name
        FROM   bookings b
        JOIN   users    u ON b.user_id = u.id
        JOIN   halls    h ON b.hall_id = h.id
        WHERE  b.status = 'approved'
        ORDER  BY b.date, b.start_time
    """)
    return cur.fetchall()
 
 
def get_hall_bookings_for_date(cur, hall_id, date):
    cur.execute("""
        SELECT b.start_time, b.end_time, b.event_title, b.status,
               u.name AS faculty_name
        FROM   bookings b
        JOIN   users    u ON b.user_id = u.id
        WHERE  b.hall_id = %s
          AND  b.date    = %s
          AND  b.status NOT IN ('rejected', 'cancelled')
        ORDER  BY b.start_time
    """, (hall_id, date))
    return cur.fetchall()
 
 
def update_booking_status(cur, booking_id, status, admin_note=""):
    cur.execute("""
        UPDATE bookings
        SET    status = %s, admin_note = %s
        WHERE  id     = %s
    """, (status, admin_note, booking_id))


def approve_booking(cur, booking_id, admin_note=""):
    update_booking_status(cur, booking_id, 'approved', admin_note)
    return True, "Booking approved."


def reject_booking(cur, booking_id, admin_note=""):
    update_booking_status(cur, booking_id, 'rejected', admin_note)
    return True, "Booking rejected."
 
 
def cancel_booking(cur, booking_id, user_id):
    cur.execute("""
        UPDATE bookings
        SET    status = 'cancelled'
        WHERE  id      = %s
          AND  user_id = %s
          AND  status  IN ('pending', 'approved')
    """, (booking_id, user_id))
    return cur.rowcount > 0
 
 
def create_notification(cur, user_id, message):
    cur.execute("""
        INSERT INTO notifications (user_id, message)
        VALUES (%s, %s)
    """, (user_id, message))
 
 
def get_user_notifications(cur, user_id, limit=10):
    cur.execute("""
        SELECT * FROM notifications
        WHERE  user_id = %s
        ORDER  BY created_at DESC
        LIMIT  %s
    """, (user_id, limit))
    return cur.fetchall()
 
 
def mark_notifications_read(cur, user_id):
    cur.execute("""
        UPDATE notifications SET is_read = 1
        WHERE  user_id = %s
    """, (user_id,))
 
 
def get_unread_notification_count(cur, user_id):
    cur.execute("""
        SELECT COUNT(*) AS cnt FROM notifications
        WHERE  user_id = %s AND is_read = 0
    """, (user_id,))
    row = cur.fetchone()
    return row['cnt'] if row else 0
 