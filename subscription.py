from datetime import datetime

from database import (
    get_user,
    increase_usage,
    reset_usage
)


FREE_LIMIT = 5



def check_access(user_id):

    user = get_user(user_id)


    if not user:
        return False, "کاربر پیدا نشد"



    plan = user[6]

    usage = user[8]

    last_reset = user[9]


    today = datetime.now().date()


    try:

        reset_date = datetime.fromisoformat(
            last_reset
        ).date()


    except:

        reset_date = today



    if reset_date != today:

        reset_usage(user_id)

        usage = 0



    if plan == "VIP":

        return True, "VIP"



    if usage >= FREE_LIMIT:

        return False, """
⚠️ محدودیت روزانه شما تمام شد.

⭐ برای استفاده نامحدود VIP شوید.
"""



    increase_usage(user_id)

    return True, "FREE"
