# ============================================================
#  modules/auth.py – Authentication helpers
# ============================================================
import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash


# ── Password Helpers ─────────────────────────────────────────

def hash_password(plain_text: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(plain_text.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')


def check_password(plain_text: str, hashed: str) -> bool:
    """Return True if plain_text matches the bcrypt hash."""
    return bcrypt.checkpw(plain_text.encode('utf-8'), hashed.encode('utf-8'))


# ── Session Helpers ──────────────────────────────────────────

def login_user(user: dict):
    """Populate session after successful authentication."""
    session['user_id']   = user['id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    session['user_email']= user['email']


def logout_user():
    """Clear the session."""
    session.clear()


def current_user() -> dict | None:
    """Return a dict of current session user, or None."""
    if 'user_id' not in session:
        return None
    return {
        'id':    session['user_id'],
        'name':  session['user_name'],
        'role':  session['user_role'],
        'email': session['user_email'],
    }


# ── Decorators ───────────────────────────────────────────────

def login_required(f):
    """Redirect to login if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Allow access only to admin users."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('faculty.dashboard'))
        return f(*args, **kwargs)
    return decorated


def faculty_required(f):
    """Allow access only to faculty users."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'faculty':
            flash('Access denied.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated
