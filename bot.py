import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN, ADMIN_ID

from database import (
    init_db,
    add_user,
    update_activity
)

from subscription import check_access

from tools.caption import create_caption
from tools.ads import create_ad
from tools.customer_reply import create_customer_reply

from admin.statistics import get_statistics


bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()



keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📝 ساخت کپشن"),
            KeyboardButton(text="🔥 متن تبلیغ")
        ],
        [
            KeyboardButton(text="💬 پاسخ مشتری")
        ],
        [
            KeyboardButton(text="📊 آمار")
        ]
    ],
    resize_keyboard=True
)



@dp.message(Command("start"))
async def start(message: types.Message):

    add_user(
        message.from_user.id,
        message.from_user.username
    )


    await message.answer(
        """
سلام 👋

به Vista AI Tools خوش آمدید 🤖

ابزارهای هوشمند:

📝 ساخت کپشن
🔥 ساخت متن تبلیغ
💬 پاسخ مشتری

یک گزینه را انتخاب کنید:
        """,
        reply_markup=keyboard
    )



@dp.message()
async def handler(message: types.Message):

    user_id = message.from_user.id


    update_activity(user_id)



    # آمار ادمین

    if message.text == "📊 آمار":

        if user_id == ADMIN_ID:

            await message.answer(
                get_statistics()
            )

        else:

            await message.answer(
                "❌ این بخش فقط برای مدیر است."
            )

        return



    # بررسی اشتراک

    allowed, status = check_access(user_id)


    if not allowed:

        await message.answer(status)

        return



    # ساخت کپشن

    if message.text == "📝 ساخت کپشن":

        await message.answer(
            """
اطلاعات محصول را بفرست:

نام محصول:
ویژگی‌ها:
مخاطب:
            """
        )

        return



    # تبلیغ

    if message.text == "🔥 متن تبلیغ":

        await message.answer(
            """
اطلاعات تبلیغ:

محصول:
مخاطب:
مزیت:
            """
        )

        return



    # پاسخ مشتری

    if message.text == "💬 پاسخ مشتری":

        await message.answer(
            "پیام مشتری را ارسال کن:"
        )

        return



    text = message.text



    # اگر پیام مربوط به تبلیغ باشد

    if "محصول:" in text:

        result = create_ad(
            text,
            "مشتریان",
            "کیفیت بالا"
        )


        await message.answer(result)

        return



    # پاسخ مشتری

    if "قیمت" in text or "موجود" in text:

        result = create_customer_reply(text)

        await message.answer(result)

        return



    # کپشن پیش فرض

    result = create_caption(
        text,
        "کیفیت عالی",
        "مشتریان"
    )


    await message.answer(result)





async def main():

    init_db()

    print("Vista AI Tools Started ✅")


   
