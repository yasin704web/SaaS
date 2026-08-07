from datetime import datetime, timedelta

from database import (
    get_user,
    set_vip
)



VIP_DAYS = 30



def activate_vip(user_id):

    user = get_user(user_id)


    if not user:
        return False, "❌ کاربر پیدا نشد."


    expire_date = datetime.now() + timedelta(days=VIP_DAYS)


    set_vip(
        user_id,
        str(expire_date)
    )


    return True, expire_date





def vip_status(user_id):

    user = get_user(user_id)


    if not user:
        return "❌ کاربر وجود ندارد."


    plan = user[5]

    expire = user[6]


    if plan == "VIP":

        return f"""
👑 وضعیت اشتراک:

پلن: VIP

تاریخ پایان:
{expire}
"""


    return """
🆓 پلن فعلی:
FREE

برای استفاده بدون محدودیت VIP شوید.
"""
