import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from config import BOT_TOKEN, ADMIN_ID, CARD_NUMBER

from database import (
    init_db,
    add_user,
    get_user,
    update_activity,
    count_users,
    count_purchases,
    total_income,
    add_purchase,
)

from subscription import check_access
from vip import activate_vip


# =========================
# تنظیمات
# =========================

VIP_PRICE = 150000

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# منوی اصلی
# =========================

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👑 خرید VIP"),
            KeyboardButton(text="👤 حساب من"),
        ],
        [
            KeyboardButton(text="🛠 ابزارها"),
        ],
    ],
    resize_keyboard=True,
)


# =========================
# START
# =========================

@dp.message(Command("start"))
async def start_handler(message: Message):

    user = message.from_user

    add_user(
        telegram_id=user.id,
        username=user.username
    )

    update_activity(user.id)

    await message.answer(
        f"""
سلام {user.first_name} 👋

به Vista AI Tools خوش آمدی.

🤖 مجموعه ابزارهای هوشمند
👑 اشتراک VIP
🆓 استفاده رایگان محدود

از منوی پایین انتخاب کن.
""",
        reply_markup=main_keyboard
    )


# =========================
# خرید VIP
# =========================

@dp.message(F.text == "👑 خرید VIP")
async def buy_vip_handler(message: Message):

    await message.answer(
        f"""
👑 اشتراک VIP Vista

⏱ مدت: ۳۰ روز
💰 قیمت: {VIP_PRICE:,} تومان

💳 شماره کارت:

{CARD_NUMBER}

━━━━━━━━━━━━━━

بعد از واریز، عکس رسید پرداخت را همینجا ارسال کن.

📌 پس از بررسی رسید، VIP توسط ادمین فعال می‌شود.
""",
    )


# =========================
# دریافت رسید
# =========================

@dp.message(F.photo)
async def receipt_handler(message: Message):

    user = message.from_user

    username = (
        f"@{user.username}"
        if user.username
        else "ندارد"
    )

    caption = f"""
🔔 درخواست خرید VIP

👤 نام:
{user.full_name}

🆔 Telegram ID:
{user.id}

👤 Username:
{username}

💰 مبلغ:
{VIP_PRICE:,} تومان

📦 اشتراک:
VIP - 30 روز

━━━━━━━━━━━━━━

برای فعال‌سازی:

/vip {user.id}
"""

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=caption
    )

    await message.answer(
        """
✅ رسید شما برای ادمین ارسال شد.

بعد از بررسی پرداخت، اشتراک VIP شما فعال خواهد شد.
"""
    )


# =========================
# حساب کاربری
# =========================

@dp.message(F.text == "👤 حساب من")
async def account_handler(message: Message):

    user_id = message.from_user.id

    user = get_user(user_id)

    if not user:
        add_user(
            user_id,
            message.from_user.username
        )

        user = get_user(user_id)

    plan = user[5]
    expire_date = user[6]
    daily_usage = user[7]

    if plan == "VIP":

        await message.answer(
            f"""
👑 حساب کاربری

پلن: VIP

📅 تاریخ پایان:
{expire_date}

♾️ محدودیت:
ندارد
"""
        )

    else:

        await message.answer(
            f"""
👤 حساب کاربری

پلن: FREE

📊 استفاده امروز:
{daily_usage}

🔒 محدودیت روزانه:
۵ استفاده

برای استفاده بدون محدودیت، VIP تهیه کن.
"""
        )


# =========================
# ابزارها
# =========================

@dp.message(F.text == "🛠 ابزارها")
async def tools_handler(message: Message):

    user_id = message.from_user.id

    add_user(
        user_id,
        message.from_user.username
    )

    allowed, result = check_access(user_id)

    if not allowed:

        await message.answer(result)

        return

    await message.answer(
        """
🛠 ابزارهای Vista

فعلاً ابزارهای اصلی پروژه از همین بخش قابل استفاده هستند.

🤖 ابزارهای بیشتر در نسخه‌های بعدی اضافه می‌شوند.
"""
    )


# =========================
# آمار ادمین
# =========================

@dp.message(Command("آمار"))
async def statistics_handler(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    users = count_users()
    purchases = count_purchases()
    income = total_income()

    await message.answer(
        f"""
📊 آمار Vista AI Tools

👥 کل کاربران:
{users}

🛒 تعداد خریدها:
{purchases}

💰 درآمد ثبت‌شده:
{income:,} تومان
"""
    )


# =========================
# فعال کردن VIP
# =========================

@dp.message(Command("vip"))
async def activate_vip_handler(message: Message):

    if message.from_user.id != ADMIN_ID:

        await message.answer(
            "⛔ شما اجازه استفاده از این دستور را ندارید."
        )

        return

    parts = message.text.split()

    if len(parts) != 2:

        await message.answer(
            """
❌ فرمت دستور اشتباه است.

مثال:

/vip 123456789
"""
        )

        return

    try:
        user_id = int(parts[1])

    except ValueError:

        await message.answer(
            "❌ Telegram ID باید عدد باشد."
        )

        return

    user = get_user(user_id)

    if not user:

        await message.answer(
            "❌ این کاربر هنوز ربات را Start نکرده است."
        )

        return

    success, result = activate_vip(user_id)

    if not success:

        await message.answer(result)

        return

    expire_date = result

    # ثبت خرید در دیتابیس
    add_purchase(
        telegram_id=user_id,
        package="VIP 30 Days",
        price=VIP_PRICE
    )

    await message.answer(
        f"""
✅ VIP فعال شد.

🆔 کاربر:
{user_id}

👑 پلن:
VIP

⏱ مدت:
۳۰ روز

📅 تاریخ پایان:
{expire_date}

💰 مبلغ ثبت‌شده:
{VIP_PRICE:,} تومان
"""
    )

    try:

        await bot.send_message(
            chat_id=user_id,
            text=f"""
🎉 اشتراک VIP شما فعال شد!

👑 پلن: VIP
⏱ مدت: ۳۰ روز

📅 تاریخ پایان:
{expire_date}

♾️ محدودیت استفاده:
ندارید

از Vista AI Tools لذت ببرید 🚀
"""
        )

    except Exception as e:

        logging.warning(
            f"Could not notify user {user_id}: {e}"
        )


# =========================
# اجرای ربات
# =========================

async def main():

    init_db()

    print("Vista AI Tools is running...")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:

        print("Bot stopped.")
