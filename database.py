import sqlite3
from datetime import datetime


DB_NAME = "vista.db"



def connect():
    return sqlite3.connect(DB_NAME)



def init_db():

    conn = connect()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(

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
    CREATE TABLE IF NOT EXISTS purchases(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        telegram_id INTEGER,

        package TEXT,

        price INTEGER,

        purchase_date TEXT

    )
    """)


    conn.commit()
    conn.close()





def add_user(telegram_id, username):

    conn = connect()
    cursor = conn.cursor()


    now = str(datetime.now())


    cursor.execute("""
    INSERT OR IGNORE INTO users
    (
        telegram_id,
        username,
        join_date,
        last_activity,
        last_reset
    )

    VALUES (?,?,?,?,?)
    """,

    (
        telegram_id,
        username,
        now,
        now,
        now
    ))


    conn.commit()
    conn.close()





def get_user(telegram_id):

    conn = connect()
    cursor = conn.cursor()


    cursor.execute("""
    SELECT *
    FROM users
    WHERE telegram_id = ?
    """,

    (telegram_id,))


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

    """,

    (
        str(datetime.now()),
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

    """,

    (telegram_id,))


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

    """,

    (
        str(datetime.now()),
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

    """,

    (
        expire_date,
        telegram_id
    ))


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

    VALUES (?,?,?,?)

    """,

    (
        telegram_id,
        package,
        price,
        str(datetime.now())
    ))


    conn.commit()
    conn.close()





def count_users():

    conn = connect()
    cursor = conn.cursor()


    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )


    result = cursor.fetchone()[0]


    conn.close()


    return result





def count_purchases():

    conn = connect()
    cursor = conn.cursor()


    cursor.execute(
        "SELECT COUNT(*) FROM purchases"
    )


    result = cursor.fetchone()[0]


    conn.close()


    return result





def total_income():

    conn = connect()
    cursor = conn.cursor()


    cursor.execute(
        "SELECT SUM(price) FROM purchases"
    )


    result = cursor.fetchone()[0]


    conn.close()


    return result or 0
