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



    # تبدیل اطلاعات دیتابیس به دیکشنری
    plan = user[5] if len(user) > 5 else "FREE"

    expire_date = user[6] if len(user) > 6 else None

    daily_usage = user[7] if len(user) > 7 else 0

    last_reset = user[8] if len(user) > 8 else None



    today = datetime.now().date()



    # ریست روزانه
    if last_reset:

        try:

            reset_day = datetime.fromisoformat(
                last_reset
            ).date()


            if reset_day != today:

                reset_usage(user_id)

                daily_usage = 0


        except:

            pass



    # VIP

    if plan == "VIP":

        return True, "VIP"



    # محدودیت رایگان

    if daily_usage >= FREE_LIMIT:

        return False, """
⚠️ سهمیه رایگان امروز تمام شد.

⭐ برای استفاده بیشتر VIP شوید.
"""



    increase_usage(user_id)


    return True, "FREE"
