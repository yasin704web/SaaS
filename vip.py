from datetime import datetime, timedelta

from config import VIP_DAYS
from database import (
    get_user,
    set_vip,
    add_purchase,
)


def activate_vip(user_id, price):
    user = get_user(user_id)

    if not user:
        return False, "کاربر پیدا نشد."

    current_expire = user[6]

    now = datetime.now()

    if current_expire:
        try:
            old_expire = datetime.fromisoformat(current_expire)

            if old_expire > now:
                start = old_expire
            else:
                start = now

        except ValueError:
            start = now
    else:
        start = now

    expire = start + timedelta(days=VIP_DAYS)

    set_vip(
        user_id,
        expire.isoformat()
    )

    add_purchase(
        user_id,
        "VIP 30 DAYS",
        price
    )

    return True, expire


def vip_status(user_id):

    user = get_user(user_id)

    if not user:
        return "کاربر پیدا نشد."

    plan = user[5]
    expire_date = user[6]

    if plan != "VIP" or not expire_date:
        return "❌ شما VIP نیستید."

    try:
        expire = datetime.fromisoformat(expire_date)
    except ValueError:
        return "❌ اطلاعات VIP خراب است."

    if expire <= datetime.now():
        return "❌ VIP شما منقضی شده است."

    remaining = expire - datetime.now()

    days = remaining.days

    return (
        "⭐ وضعیت VIP\n\n"
        "وضعیت: فعال ✅\n"
        f"تاریخ پایان: {expire.strftime('%Y-%m-%d %H:%M')}\n"
        f"زمان باقی‌مانده: حدود {days} روز"
    )
