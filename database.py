import sqlite3
from datetime import datetime


DB_NAME = "vista.db"


def connect():
    return sqlite3.connect(DB_NAME)



# ساخت جدول‌ها
def init_db():

    conn = connect()
    cursor = conn.cursor()


    # کاربران
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        join_date TEXT,
        last_activity TEXT,
        plan TEXT DEFAULT 'FREE',
        expire_date TEXT
    )
    """)



    # خریدها
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        package TEXT,
        price INTEGER,
        purchase_date TEXT
    )
    """)



    # استفاده از ابزارها
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usage(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        tool TEXT,
        use_date TEXT
    )
    """)


    conn.commit()
    conn.close()



# اضافه کردن کاربر
def add_user(telegram_id, username):

    conn = connect()
    cursor = conn.cursor()


    cursor.execute("""
    INSERT OR IGNORE INTO users
    (telegram_id, username, join_date, last_activity)
    VALUES (?, ?, ?, ?)
    """,
    (
        telegram_id,
        username,
        str(datetime.now()),
        str(datetime.now())
    ))


    conn.commit()
    conn.close()



# بروزرسانی فعالیت کاربر
def update_activity(telegram_id):

    conn = connect()
    cursor = conn.cursor()


    cursor.execute("""
    UPDATE users
    SET last_activity=?
    WHERE telegram_id=?
    """,
    (
        str(datetime.now()),
        telegram_id
    ))


    conn.commit()
    conn.close()



# ثبت خرید
def add_purchase(telegram_id, package, price):

    conn = connect()
    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO purchases
    (telegram_id, package, price, purchase_date)
    VALUES (?, ?, ?, ?)
    """,
    (
        telegram_id,
        package,
        price,
        str(datetime.now())
    ))


    conn.commit()
    conn.close()



# ثبت استفاده از ابزار
def add_usage(telegram_id, tool):

    conn = connect()
    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO usage
    (telegram_id, tool, use_date)
    VALUES (?, ?, ?)
    """,
    (
        telegram_id,
        tool,
        str(datetime.now())
    ))


    conn.commit()
    conn.close()



# گرفتن تعداد کاربران
def count_users():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    result = cursor.fetchone()[0]

    conn.close()

    return result



# تعداد خریدها
def count_purchases():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM purchases"
    )

    result = cursor.fetchone()[0]

    conn.close()

    return result



# درآمد کل
def total_income():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT SUM(price) FROM purchases"
    )

    result = cursor.fetchone()[0]

    conn.close()

    return result or 0
