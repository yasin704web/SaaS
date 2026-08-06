from database import (
    count_users,
    count_purchases,
    total_income
)


def get_statistics():

    users = count_users()

    purchases = count_purchases()

    income = total_income()


    text = f"""
📊 آمار Vista AI Tools


👥 تعداد کل کاربران:
{users} نفر


💰 تعداد خریدها:
{purchases} عدد


💵 درآمد کل:
{income:,} تومان


🚀 وضعیت سیستم:
فعال ✅
"""


    return text
