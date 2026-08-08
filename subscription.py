from datetime import datetime

from database import (
    get_user,
    increase_usage,
    reset_usage,
    connect
)


FREE_LIMIT = 5


def expire_vip(user_id):
    """
    اگر VIP کاربر تمام شده باشد،
    پلن او را به FREE برمی‌گرداند.
    """

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET plan = 'FREE',
            expire_date = NULL
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def check_access(user_id):

    user = get_user(user_id)

    if not user:
        return False, "❌ کاربر پیدا نشد."


    # ساختار جدول users:
    #
    # 0 = id
    # 1 = telegram_id
    # 2 = username
    # 3 = join_date
    # 4 = last_activity
    # 5 = plan
    # 6 = expire_date
    # 7 = daily_usage
    # 8 = last_reset

    plan = user[5] or "FREE"
    expire_date = user[6]
    daily_usage = user[7] or 0
    last_reset = user[8]


    # =========================
    # بررسی تاریخ VIP
    # =========================

    if plan == "VIP":

        if not expire_date:

            expire_vip(user_id)

            plan = "FREE"

        else:

            try:

                expiration = datetime.fromisoformat(
                    expire_date
                )

                if datetime.now() >= expiration:

                    expire_vip(user_id)

                    plan = "FREE"

            except (ValueError, TypeError):

                expire_vip(user_id)

                plan = "FREE"


    # =========================
    # VIP فعال
    # =========================

    if plan == "VIP":

        return True, "VIP"


    # =========================
    # ریست سهمیه روزانه
    # =========================

    today = datetime.now().date()

    if last_reset:

        try:

            reset_day = datetime.fromisoformat(
                last_reset
            ).date()

            if reset_day != today:

                reset_usage(user_id)

                daily_usage = 0

        except (ValueError, TypeError):

            reset_usage(user_id)

            daily_usage = 0

    else:

        reset_usage(user_id)

        daily_usage = 0


    # =========================
    # محدودیت FREE
    # =========================

    if daily_usage >= FREE_LIMIT:

        return False, """
⚠️ سهمیه رایگان امروز تمام شده.

👑 با خرید VIP می‌توانی بدون محدودیت از ابزارها استفاده کنی.
"""


    # =========================
    # ثبت استفاده
    # =========================

    increase_usage(user_id)

    return True, "FREE"
