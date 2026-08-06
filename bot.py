import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN, ADMIN_ID

from database import (
    init_db,
    add_user,
    update_activity,
    add_usage
)

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

ابزارهای هوشمند فروش:

📝 ساخت کپشن محصول
🔥 ساخت متن تبلیغ
💬 پاسخ حرفه‌ای مشتری

یک گزینه را انتخاب کنید:
        """,
        reply_markup=keyboard
    )



@dp.message()
async def handler(message: types.Message):

    user_id = message.from_user.id

    update_activity(user_id)



    # بخش آمار ادمین

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



    # کپشن

    if message.text == "📝 ساخت کپشن":

        await message.answer(
            """
اطلاعات محصول را این شکل بفرست:

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
اطلاعات تبلیغ را این شکل بفرست:

محصول:
مخاطب:
مزیت اصلی:
            """
        )

        return



    # پاسخ مشتری

    if message.text == "💬 پاسخ مشتری":

        await message.answer(
            "پیام مشتری را ارسال کن:"
        )

        return



    # تولید خروجی ساده

    text = message.text


    if "محصول:" in text:

        add_usage(
            user_id,
            "ads"
        )


        await message.answer(
            create_ad(
                text,
                "مشتریان",
                "کیفیت بالا"
            )
        )


    else:

        add_usage(
            user_id,
            "caption"
        )


        await message.answer(
            create_caption(
                text,
                "کیفیت عالی",
                "مشتریان"
            )
        )



async def main():

    init_db()

    print("Vista AI Tools Started ✅")

    await dp.start_polling(bot)



if __name__ == "__main__":

    asyncio.run(main())
