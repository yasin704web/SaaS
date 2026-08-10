import os
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ================= ENV =================
TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

if not TOKEN:
    raise ValueError("TOKEN تنظیم نشده!")

if not CHANNEL_USERNAME:
    raise ValueError("CHANNEL_USERNAME تنظیم نشده!")

# ================= SETUP =================
logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# ================= DATABASE =================
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    plan TEXT DEFAULT 'FREE',
    expire_date TEXT
)
""")
conn.commit()

# ================= DB FUNCTIONS =================
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# ================= CHECK CHANNEL =================
async def is_member(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= KEYBOARDS =================
def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 حساب کاربری", callback_data="account")],
            [InlineKeyboardButton(text="🧠 ابزارها", callback_data="tools")]
        ]
    )

def back_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_main")]
        ]
    )

# ================= START =================
@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    add_user(user_id)

    if not await is_member(user_id):
        await message.answer(
            "❗ برای استفاده از ربات باید عضو کانال شوید",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📢 عضویت",
                        url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
                    )],
                    [InlineKeyboardButton(text="✅ بررسی", callback_data="check_join")]
                ]
            )
        )
        return

    await message.answer(
        "👋 خوش اومدی!\n\nیکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=main_menu()
    )

# ================= CHECK JOIN =================
@dp.callback_query(F.data == "check_join")
async def check_join(callback: CallbackQuery):
    if await is_member(callback.from_user.id):
        await callback.message.edit_text(
            "✅ عضویت تایید شد",
            reply_markup=main_menu()
        )
    else:
        await callback.answer("❌ هنوز عضو نشدی", show_alert=True)

# ================= ACCOUNT =================
@dp.callback_query(F.data == "account")
async def account(callback: CallbackQuery):
    try:
        user = get_user(callback.from_user.id)

        if not user:
            await callback.answer("کاربر یافت نشد", show_alert=True)
            return

        plan = user[1]
        expire = user[2]

        text = (
            "👤 <b>حساب شما</b>\n\n"
            f"📦 پلن: <b>{plan}</b>\n"
        )

        if plan == "VIP" and expire:
            text += f"⏳ انقضا: {expire}\n"

        await callback.message.edit_text(
            text,
            reply_markup=back_menu()
        )
        await callback.answer()

    except Exception as e:
        logging.exception(f"Account error: {e}")
        await callback.answer("⚠️ خطا", show_alert=True)

# ================= TOOLS =================
@dp.callback_query(F.data == "tools")
async def tools(callback: CallbackQuery):
    await callback.message.edit_text(
        "🧠 ابزارها:\n\nبه زودی اضافه میشه...",
        reply_markup=back_menu()
    )
    await callback.answer()

# ================= BACK =================
@dp.callback_query(F.data == "back_main")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 منوی اصلی",
        reply_markup=main_menu()
    )
    await callback.answer()

# ================= RUN =================
if __name__ == "__main__":
    dp.run_polling(bot)
    
