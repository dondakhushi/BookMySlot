# ============================================================
#  config.py – BookMySlot Application Configuration
# ============================================================
import os

class Config:
    # ── Security ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bms-super-secret-key-change-in-production-2024')

    # ── MySQL Database ─────────────────────────────────────────
    # Update these credentials to match your MySQL setup
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Het157@#')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'bookmyslot')

    # ── Session ────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ── Pagination ─────────────────────────────────────────────
    ROWS_PER_PAGE = 10

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

# Active config
config = DevelopmentConfig()
