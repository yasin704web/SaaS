import sqlite3
from datetime import datetime


DB_NAME = "vista.db"


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        join_date TEXT,
        last_activity TEXT,
        plan TEXT DEFAULT 'FREE',
        expire_date TEXT,
        daily_usage INTEGER DEFAULT 0,
        last_reset TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        package TEXT,
        price INTEGER,
        purchase_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        action TEXT,
        input_text TEXT,
        output_text TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vip_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        username TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'PENDING'
    )
    """)

    conn.commit()
    conn.close()


def add_user(telegram_id, username=None):
    conn = connect()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    cursor.execute("""
    INSERT OR IGNORE INTO users
    (
        telegram_id,
        username,
        join_date,
        last_activity,
        last_reset
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        telegram_id,
        username,
        now,
        now,
        now
    ))

    cursor.execute("""
    UPDATE users
    SET username = ?,
        last_activity = ?
    WHERE telegram_id = ?
    """, (
        username,
        now,
        telegram_id
    ))

    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        telegram_id,
        username,
        join_date,
        last_activity,
        plan,
        expire_date,
        daily_usage,
        last_reset
    FROM users
    WHERE telegram_id = ?
    """, (telegram_id,))

    user = cursor.fetchone()

    conn.close()

    return user


def update_activity(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET last_activity = ?
    WHERE telegram_id = ?
    """, (
        datetime.now().isoformat(),
        telegram_id
    ))

    conn.commit()
    conn.close()


def increase_usage(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET daily_usage = daily_usage + 1
    WHERE telegram_id = ?
    """, (telegram_id,))

    conn.commit()
    conn.close()


def reset_usage(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET daily_usage = 0,
        last_reset = ?
    WHERE telegram_id = ?
    """, (
        datetime.now().isoformat(),
        telegram_id
    ))

    conn.commit()
    conn.close()


def set_vip(telegram_id, expire_date):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET plan = 'VIP',
        expire_date = ?
    WHERE telegram_id = ?
    """, (
        expire_date,
        telegram_id
    ))

    conn.commit()
    conn.close()


def remove_vip(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE users
    SET plan = 'FREE',
        expire_date = NULL
    WHERE telegram_id = ?
    """, (telegram_id,))

    conn.commit()
    conn.close()


def add_purchase(telegram_id, package, price):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO purchases
    (
        telegram_id,
        package,
        price,
        purchase_date
    )
    VALUES (?, ?, ?, ?)
    """, (
        telegram_id,
        package,
        price,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def count_users():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")

    result = cursor.fetchone()[0]

    conn.close()

    return result


def count_purchases():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM purchases")

    result = cursor.fetchone()[0]

    conn.close()

    return result


def total_income():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(price) FROM purchases")

    result = cursor.fetchone()[0] or 0

    conn.close()

    return result


def count_vips():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM users
    WHERE plan = 'VIP'
    """)

    result = cursor.fetchone()[0]

    conn.close()

    return result


def save_memory(
    telegram_id,
    action,
    input_text,
    output_text
):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO memory
    (
        telegram_id,
        action,
        input_text,
        output_text,
        created_at
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        telegram_id,
        action,
        input_text,
        output_text,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def create_vip_request(telegram_id, username):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO vip_requests
    (
        telegram_id,
        username,
        created_at
    )
    VALUES (?, ?, ?)
    """, (
        telegram_id,
        username,
        datetime.now().isoformat()
    ))

    request_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return request_id
