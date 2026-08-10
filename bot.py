import os
import re
import html
import sqlite3
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.client.default import DefaultBotProperties


# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("TOKEN", "").strip()

CHANNEL_1 = os.getenv("CHANNEL_1", "").strip()
CHANNEL_2 = os.getenv("CHANNEL_2", "").strip()

CHANNEL_LINK_1 = os.getenv("CHANNEL_LINK_1", "").strip()
CHANNEL_LINK_2 = os.getenv("CHANNEL_LINK_2", "").strip()

VIP_PRICE = os.getenv("VIP_PRICE", "199000").strip()
VIP_DAYS = int(os.getenv("VIP_DAYS", "30"))

CARD_NUMBER = os.getenv("CARD_NUMBER", "").strip()
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "").strip().replace("@", "")

ADMIN_ID = os.getenv("ADMIN_ID", "").strip()

if not TOKEN:
    raise RuntimeError(
        "TOKEN تنظیم نشده است. "
        "در Render یک Environment Variable با نام TOKEN بساز."
    )


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("SaaS")


# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# =========================================================
# DATABASE
# =========================================================

DB_FILE = "bot.db"

db = sqlite3.connect(
    DB_FILE,
    check_same_thread=False
)

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT DEFAULT '',
    plan TEXT DEFAULT 'FREE',
    vip_expire TEXT DEFAULT '',
    usage INTEGER DEFAULT 0,
    joined_at TEXT DEFAULT '',
    last_activity TEXT DEFAULT ''
)
""")

db.commit()


def add_user(user_id: int, username: str = ""):
    now = datetime.now().isoformat()

    db.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, username, joined_at, last_activity)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            username,
            now,
            now
        )
    )

    db.execute(
        """
        UPDATE users
        SET username = ?, last_activity = ?
        WHERE user_id = ?
        """,
        (
            username,
            now,
            user_id
        )
    )

    db.commit()


def get_user(user_id: int):
    return db.execute(
        """
        SELECT user_id, username, plan,
               vip_expire, usage,
               joined_at, last_activity
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()


def increment_usage(user_id: int):
    db.execute(
        """
        UPDATE users
        SET usage = usage + 1,
            last_activity = ?
        WHERE user_id = ?
        """,
        (
            datetime.now().isoformat(),
            user_id
        )
    )

    db.commit()


def activate_vip(user_id: int):
    user = get_user(user_id)

    now = datetime.now()

    if user and user[3]:
        try:
            current_expire = datetime.fromisoformat(user[3])

            if current_expire > now:
                start_date = current_expire
            else:
                start_date = now

        except Exception:
            start_date = now
    else:
        start_date = now

    expire = start_date + timedelta(days=VIP_DAYS)

    db.execute(
        """
        UPDATE users
        SET plan = 'VIP',
            vip_expire = ?
        WHERE user_id = ?
        """,
        (
            expire.isoformat(),
            user_id
        )
    )

    db.commit()

    return expire


# =========================================================
# ACCESS
# =========================================================

async def is_member(channel: str, user_id: int) -> bool:

    if not channel:
        return True

    try:

        member = await bot.get_chat_member(
            chat_id=channel,
            user_id=user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception as e:

        logger.warning(
            "Channel check failed: %s | %s",
            channel,
            e
        )

        return False


async def check_channels(user_id: int) -> bool:

    first = await is_member(
        CHANNEL_1,
        user_id
    )

    second = await is_member(
        CHANNEL_2,
        user_id
    )

    return first and second


async def has_access(user_id: int) -> bool:

    if not await check_channels(user_id):
        return False

    user = get_user(user_id)

    if not user:
        return False

    plan = user[2]
    expire = user[3]

    if plan == "VIP" and expire:

        try:

            expire_date = datetime.fromisoformat(
                expire
            )

            if expire_date > datetime.now():
                return True

            db.execute(
                """
                UPDATE users
                SET plan = 'FREE',
                    vip_expire = ''
                WHERE user_id = ?
                """,
                (user_id,)
            )

            db.commit()

        except Exception:
            pass

    # FREE هم اجازه استفاده دارد.
    return True


# =========================================================
# HELPERS
# =========================================================

def safe(text: str, limit: int = 4000):

    text = text or ""
    text = text.strip()

    if len(text) > limit:
        text = text[:limit] + "..."

    return html.escape(text)


def channel_join_keyboard():

    rows = []

    if CHANNEL_LINK_1:

        rows.append([
            InlineKeyboardButton(
                text="📢 عضویت کانال اول",
                url=CHANNEL_LINK_1
            )
        ])

    if CHANNEL_LINK_2:

        rows.append([
            InlineKeyboardButton(
                text="📢 عضویت کانال دوم",
                url=CHANNEL_LINK_2
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="✅ بررسی عضویت",
            callback_data="check_join"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


# =========================================================
# STATES
# =========================================================

class ToolState(StatesGroup):

    caption = State()
    video_caption = State()

    comment = State()
    reply = State()

    bio = State()
    instagram_caption = State()
    instagram_idea = State()

    hashtag = State()
    title = State()

    post_idea = State()
    ad = State()
    announcement = State()

    rewrite = State()
    summary = State()
    product = State()

    content_plan = State()

    poll = State()
    faq = State()

    welcome = State()
    rules = State()

    vip_payment = State()


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🛠 ابزارها",
                    callback_data="tools"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⭐ خرید VIP",
                    callback_data="vip"
                ),
                InlineKeyboardButton(
                    text="👤 حساب من",
                    callback_data="account"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📚 راهنما",
                    callback_data="help"
                )
            ]

        ]
    )


# =========================================================
# TOOLS MENU
# =========================================================

def tools_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📢 مدیریت کانال تلگرام",
                    callback_data="channel_tools"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 مدیریت گروه",
                    callback_data="group_tools"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📸 ابزارهای اینستاگرام",
                    callback_data="instagram_tools"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✍️ ابزارهای متن",
                    callback_data="text_tools"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📅 برنامه محتوا",
                    callback_data="content_tools"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="back_main"
                )
            ]

        ]
    )


# =========================================================
# CHANNEL MENU
# =========================================================

def channel_tools_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✍️ کپشن پست",
                    callback_data="tool_caption"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎬 کپشن ویدیو",
                    callback_data="tool_video_caption"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💡 ایده پست",
                    callback_data="tool_post_idea"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏷 هشتگ‌ساز",
                    callback_data="tool_hashtag"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📰 عنوان پست",
                    callback_data="tool_title"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 متن تبلیغ",
                    callback_data="tool_ad"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📌 اطلاعیه",
                    callback_data="tool_announcement"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]

        ]
    )


# =========================================================
# GROUP MENU
# =========================================================

def group_tools_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💬 ساخت کامنت",
                    callback_data="tool_comment"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🗣 پاسخ به کاربر",
                    callback_data="tool_reply"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👋 پیام خوش‌آمد",
                    callback_data="tool_welcome"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📜 قوانین گروه",
                    callback_data="tool_rules"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 اطلاعیه گروه",
                    callback_data="tool_announcement"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📊 ساخت نظرسنجی",
                    callback_data="tool_poll"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❓ FAQ",
                    callback_data="tool_faq"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]

        ]
    )


# =========================================================
# INSTAGRAM MENU
# =========================================================

def instagram_tools_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👤 ساخت Bio",
                    callback_data="tool_bio"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📸 کپشن اینستاگرام",
                    callback_data="tool_instagram_caption"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎬 ایده ریلز",
                    callback_data="tool_instagram_idea"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏷 هشتگ اینستاگرام",
                    callback_data="tool_hashtag"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💡 ایده پست",
                    callback_data="tool_post_idea"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]

        ]
    )


# =========================================================
# TEXT MENU
# =========================================================

def text_tools_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✏️ بازنویسی متن",
                    callback_data="tool_rewrite"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📋 خلاصه‌سازی",
                    callback_data="tool_summary"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📰 عنوان‌سازی",
                    callback_data="tool_title"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏷 هشتگ‌سازی",
                    callback_data="tool_hashtag"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🛍 متن محصول",
                    callback_data="tool_product"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💬 ساخت کامنت",
                    callback_data="tool_comment"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]

        ]
    )


# =========================================================
# CONTENT MENU
# =========================================================

def content_tools_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📅 برنامه ۷ روزه",
                    callback_data="tool_plan"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💡 ایده‌های محتوا",
                    callback_data="tool_post_idea"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎯 عنوان‌های جذاب",
                    callback_data="tool_title"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]

        ]
    )


def back_tools():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 بازگشت به ابزارها",
                    callback_data="tools"
                )
            ]
        ]
    )


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    user = message.from_user

    add_user(
        user.id,
        user.username or ""
    )

    if not await check_channels(user.id):

        await message.answer(
            "🚀 <b>به SaaS خوش آمدی!</b>\n\n"
            "برای استفاده از ربات ابتدا باید در "
            "کانال‌های الزامی عضو شوی.\n\n"
            "بعد از عضویت روی «بررسی عضویت» بزن.",
            reply_markup=channel_join_keyboard()
        )

        return

    await message.answer(
        "🧠 <b>SaaS</b>\n\n"
        "دستیار مدیریت محتوا آماده است.\n\n"
        "📢 مدیریت کانال\n"
        "👥 مدیریت گروه\n"
        "📸 ابزارهای اینستاگرام\n"
        "✍️ ابزارهای متن\n"
        "📅 برنامه محتوا\n\n"
        "یک گزینه را انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# CHECK JOIN
# =========================================================

@dp.callback_query(F.data == "check_join")
async def check_join(callback: CallbackQuery):

    user_id = callback.from_user.id

    if not await check_channels(user_id):

        await callback.answer(
            "❌ هنوز عضویتت تأیید نشده.",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "✅ <b>عضویت تأیید شد!</b>\n\n"
        "حالا می‌توانی از SaaS استفاده کنی 🧠",
        reply_markup=main_menu()
    )

    await callback.answer(
        "تأیید شد ✅"
    )


# =========================================================
# TOOLS
# =========================================================

@dp.callback_query(F.data == "tools")
async def tools_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "🛠 <b>مرکز ابزارهای SaaS</b>\n\n"
        "بخش موردنظر را انتخاب کن:",
        reply_markup=tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "channel_tools")
async def channel_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "📢 <b>مدیریت کانال تلگرام</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=channel_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "group_tools")
async def group_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "👥 <b>مدیریت گروه</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=group_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "instagram_tools")
async def instagram_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "📸 <b>ابزارهای اینستاگرام</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=instagram_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "text_tools")
async def text_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "✍️ <b>ابزارهای متن</b>\n\n"
        "ابزار مورد
