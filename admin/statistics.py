from database import (
    count_users,
    count_purchases,
    total_income,
    count_vips
)


def get_statistics():

    users = count_users()
    purchases = count_purchases()
    income = total_income()
    vips = count_vips()

    return f"""
📊 آمار Vista

👤 کاربران:
{users}

⭐ کاربران VIP:
{vips}

🛒 خریدها:
{purchases}

💰 درآمد:
{income:,} تومان
"""
