#!/usr/bin/env python
"""Quick database diagnostic script"""
import pymysql
from config import Config

try:
    print("🔍 Testing database connection...")
    conn = pymysql.connect(
        host     = Config.MYSQL_HOST,
        user     = Config.MYSQL_USER,
        password = Config.MYSQL_PASSWORD,
        database = Config.MYSQL_DB,
        cursorclass = pymysql.cursors.DictCursor
    )
    print("✅ Database connection successful!\n")
    
    cur = conn.cursor()
    
    # Check tables
    print("📋 Checking tables...")
    cur.execute("SHOW TABLES;")
    tables = cur.fetchall()
    if tables:
        print(f"✅ Found {len(tables)} tables:")
        for t in tables:
            print(f"   - {list(t.values())[0]}")
    else:
        print("❌ No tables found! Database is empty.")
    
    # Check users
    print("\n👥 Checking users table...")
    try:
        cur.execute("SELECT COUNT(*) as cnt FROM users;")
        result = cur.fetchone()
        count = result['cnt'] if result else 0
        print(f"✅ Users in database: {count}")
        
        if count > 0:
            cur.execute("SELECT id, name, email, role FROM users LIMIT 5;")
            users = cur.fetchall()
            print("   Sample users:")
            for u in users:
                print(f"   - {u['email']} ({u['role']}): {u['name']}")
    except Exception as e:
        print(f"❌ Error reading users: {e}")
    
    cur.close()
    conn.close()
    print("\n✅ All checks passed!")
    
except pymysql.err.OperationalError as e:
    print(f"❌ Database connection failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
