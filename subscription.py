from datetime import datetime

from config import FREE_LIMIT
from database import (
    get_user,
    increase_usage,
    reset_usage
)


def check_access(user_id):

    user = get_user(user_id)

    if not user:
        return False, "کاربر در دیتابیس پیدا نشد."


    plan = user[5]
    expire_date = user[6]
    daily_usage = user[7]
    last_reset = user[8]


    today = datetime.now().date()


    if last_reset:

        try:
            reset_day = datetime.fromisoformat(
                last_reset
            ).date()

            if reset_day != today:
                reset_usage(user_id)
                daily_usage = 0

        except ValueError:
            reset_usage(user_id)
            daily_usage = 0


    if plan == "VIP" and expire_date:

        try:
            expire = datetime.fromisoformat(expire_date)

            if expire > datetime.now():
                return True, "VIP"

        except ValueError:
            pass


    if plan == "VIP":
        return False, "VIP شما منقضی شده است."


    if daily_usage >= FREE_LIMIT:
        return False, (
            "🚫 سهمیه رایگان امروز تمام شد.\n\n"
            "⭐ با VIP به امکانات کامل دسترسی داشته باش."
        )


    increase_usage(user_id)

    return True, "FREE"
