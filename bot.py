import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# =========================================================
# CONFIG / ENV
# =========================================================

TOKEN = os.getenv("TOKEN", "").strip()

CHANNEL_1 = os.getenv("CHANNEL_1", "").strip()
CHANNEL_2 = os.getenv("CHANNEL_2", "").strip()

CHANNEL_LINK_1 = os.getenv("CHANNEL_LINK_1", "").strip()
CHANNEL_LINK_2 = os.getenv("CHANNEL_LINK_2", "").strip()

VIP_PRICE = os.getenv("VIP_PRICE", "199000").strip()
VIP_DAYS = int(os.getenv("VIP_DAYS", "30").strip() or "30")

CARD_NUMBER = os.getenv("CARD_NUMBER", "").strip()

SUPPORT_USERNAME = os.getenv(
    "SUPPORT_USERNAME", ""
).strip().replace("@", "")

ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()

try:
    ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW else 0
except ValueError:
    ADMIN_ID = 0


if not TOKEN:
    raise RuntimeError(
        "❌ ENV به نام TOKEN در Render تنظیم نشده است."
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

DB_PATH = "saas.db"

db = sqlite3.connect(
    DB_PATH,
    check_same_thread=False
)

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT DEFAULT '',
    plan TEXT DEFAULT 'FREE',
    vip_expire TEXT DEFAULT '',
    daily_usage INTEGER DEFAULT 0,
    last_usage_date TEXT DEFAULT '',
    created_at TEXT DEFAULT '',
    last_seen TEXT DEFAULT ''
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount TEXT,
    created_at TEXT,
    status TEXT DEFAULT 'pending'
)
""")

db.commit()


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_text():
    return datetime.now().strftime("%Y-%m-%d")


def add_user(user_id, username=""):
    current = now_text()

    db.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, username, created_at, last_seen)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            username,
            current,
            current
        )
    )

    db.execute(
        """
        UPDATE users
        SET username = ?, last_seen = ?
        WHERE user_id = ?
        """,
        (
            username,
            current,
            user_id
        )
    )

    db.commit()


def get_user(user_id):
    return db.execute(
        """
        SELECT
            user_id,
            username,
            plan,
            vip_expire,
            daily_usage,
            last_usage_date
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()


def reset_daily_if_needed(user_id):
    user = get_user(user_id)

    if not user:
        return

    last_date = user[5]

    if last_date != today_text():
        db.execute(
            """
            UPDATE users
            SET daily_usage = 0,
                last_usage_date = ?
            WHERE user_id = ?
            """,
            (
                today_text(),
                user_id
            )
        )
        db.commit()


def get_usage(user_id):
    reset_daily_if_needed(user_id)

    user = get_user(user_id)

    if not user:
        return 0

    return user[4]


def increase_usage(user_id):
    reset_daily_if_needed(user_id)

    db.execute(
        """
        UPDATE users
        SET daily_usage = daily_usage + 1,
            last_usage_date = ?
        WHERE user_id = ?
        """,
        (
            today_text(),
            user_id
        )
    )

    db.commit()


def activate_vip(user_id, days=None):
    if days is None:
        days = VIP_DAYS

    current = datetime.now()

    user = get_user(user_id)

    if user and user[3]:
        try:
            old_expire = datetime.strptime(
                user[3],
                "%Y-%m-%d %H:%M:%S"
            )

            if old_expire > current:
                start_date = old_expire
            else:
                start_date = current

        except ValueError:
            start_date = current
    else:
        start_date = current

    expire = start_date + timedelta(days=days)

    db.execute(
        """
        UPDATE users
        SET plan = 'VIP',
            vip_expire = ?
        WHERE user_id = ?
        """,
        (
            expire.strftime("%Y-%m-%d %H:%M:%S"),
            user_id
        )
    )

    db.commit()

    return expire


def is_vip(user_id):
    user = get_user(user_id)

    if not user:
        return False

    plan = user[2]
    expire_text = user[3]

    if plan != "VIP":
        return False

    if not expire_text:
        return False

    try:
        expire = datetime.strptime(
            expire_text,
            "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        return False

    if expire <= datetime.now():

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

        return False

    return True


def create_purchase(user_id):
    cursor = db.execute(
        """
        INSERT INTO purchases
        (user_id, amount, created_at, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            VIP_PRICE,
            now_text(),
            "pending"
        )
    )

    db.commit()

    return cursor.lastrowid


def count_users():
    row = db.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()

    return row[0]


def count_purchases():
    row = db.execute(
        """
        SELECT COUNT(*)
        FROM purchases
        WHERE status = 'approved'
        """
    ).fetchone()

    return row[0]


def total_income():
    rows = db.execute(
        """
        SELECT amount
        FROM purchases
        WHERE status = 'approved'
        """
    ).fetchall()

    total = 0

    for row in rows:
        try:
            total += int(row[0])
        except Exception:
            pass

    return total


# =========================================================
# STATES
# =========================================================

class ToolState(StatesGroup):
    caption = State()
    video_caption = State()
    comment = State()
    reply = State()
    bio = State()
    hashtag = State()
    title = State()
    post_idea = State()
    advertisement = State()
    announcement = State()
    rewrite = State()
    summary = State()
    product = State()
    poll = State()
    faq = State()
    content_plan = State()
    instagram_bio = State()
    instagram_caption = State()
    instagram_idea = State()
    instagram_hashtag = State()
    vip_payment = State()


# =========================================================
# HELPERS
# =========================================================

def user_allowed(user_id):
    """
    سهمیه رایگان:
    روزانه 5 استفاده.
    VIP:
    بدون محدودیت این نسخه.
    """

    if is_vip(user_id):
        return True

    return get_usage(user_id) < 5


async def check_required_channels(user_id):

    channels = [
        CHANNEL_1,
        CHANNEL_2
    ]

    for channel in channels:

        if not channel:
            continue

        try:

            member = await bot.get_chat_member(
                chat_id=channel,
                user_id=user_id
            )

            if member.status not in (
                "member",
                "administrator",
                "creator"
            ):
                return False

        except Exception as error:

            logger.warning(
                "Channel check failed for %s: %s",
                channel,
                error
            )

            return False

    return True


async def access_ok(user_id):

    if not await check_required_channels(user_id):
        return False, (
            "🔐 ابتدا باید در کانال‌های الزامی عضو شوی."
        )

    if not user_allowed(user_id):
        return False, (
            "⛔ سهمیه روزانه نسخه رایگان تو تمام شده است.\n\n"
            "⭐ با VIP می‌توانی از ابزارها بدون این محدودیت "
            "استفاده کنی."
        )

    return True, ""


# =========================================================
# KEYBOARDS
# =========================================================

def join_keyboard():

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


def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧠 ابزارها",
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


def tools_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 کانال تلگرام",
                    callback_data="channel_tools"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 گروه",
                    callback_data="group_tools"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📸 اینستاگرام",
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
                    text="🔙 منوی اصلی",
                    callback_data="back_main"
                )
            ]
        ]
    )


def channel_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ کپشن پست",
                    callback_data="tool_caption"
                ),
                InlineKeyboardButton(
                    text="🎬 کپشن ویدیو",
                    callback_data="tool_video_caption"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💡 ایده پست",
                    callback_data="tool_post_idea"
                ),
                InlineKeyboardButton(
                    text="🏷 هشتگ",
                    callback_data="tool_hashtag"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📰 عنوان",
                    callback_data="tool_title"
                ),
                InlineKeyboardButton(
                    text="📢 تبلیغ",
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


def group_menu():

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
                    text="📢 اطلاعیه گروه",
                    callback_data="tool_announcement"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 نظرسنجی",
                    callback_data="tool_poll"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❓ ساخت FAQ",
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


def instagram_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 ساخت Bio",
                    callback_data="tool_instagram_bio"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📸 کپشن عکس",
                    callback_data="tool_instagram_caption"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💡 ایده پست/Reels",
                    callback_data="tool_instagram_idea"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏷 هشتگ اینستاگرام",
                    callback_data="tool_instagram_hashtag"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎯 عنوان جذاب",
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


def text_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ بازنویسی",
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
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]
        ]
    )


def content_menu():

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
                    text="🎯 عنوان جذاب",
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


def back_tools_keyboard():

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
# TOOL START
# =========================================================

async def start_tool(
    callback: CallbackQuery,
    state: FSMContext,
    state_obj: State,
    title: str,
    description: str
):

    allowed, reason = await access_ok(
        callback.from_user.id
    )

    if not allowed:

        await callback.answer(
            reason,
            show_alert=True
        )

        return

    await state.set_state(state_obj)

    await callback.message.edit_text(
        f"🧠 <b>{title}</b>\n\n"
        f"{description}\n\n"
        "📩 اطلاعاتت را در یک پیام بفرست.\n\n"
        "برای لغو: /cancel"
    )

    await callback.answer()


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

    if not await check_required_channels(user.id):

        await message.answer(
            "🚀 <b>به SaaS خوش آمدی!</b>\n\n"
            "برای استفاده از ربات باید ابتدا "
            "در کانال‌های الزامی عضو شوی.\n\n"
            "بعد از عضویت روی «بررسی عضویت» بزن.",
            reply_markup=join_keyboard()
        )

        return

    await message.answer(
        "🧠 <b>SaaS</b>\n\n"
        "مرکز حرفه‌ای ابزارهای مدیریت محتوا.\n\n"
        "📢 کانال تلگرام\n"
        "👥 گروه\n"
        "📸 اینستاگرام\n"
        "✍️ ابزارهای متن\n"
        "📅 برنامه محتوا\n\n"
        "از منوی زیر شروع کن:",
        reply_markup=main_menu()
    )

# =========================================================
# JOIN CHECK
# =========================================================

@dp.callback_query(F.data == "check_join")
async def check_join(callback: CallbackQuery):

    try:
        user_id = callback.from_user.id

        if not await is_member(user_id):
            await callback.answer(
                "❌ هنوز عضو کانال نشده‌ای.",
                show_alert=True
            )
            return

        await callback.message.edit_text(
            "✅ <b>عضویت تأیید شد!</b>\n\n"
            "🎉 حالا می‌توانی از امکانات ربات استفاده کنی.",
            reply_markup=main_menu()
        )

        await callback.answer("عضویت تأیید شد ✅")

    except Exception as e:
        logging.exception(f"Join check error: {e}")

        await callback.answer(
            "⚠️ خطایی رخ داد. دوباره تلاش کن.",
            show_alert=True
        )


# =========================================================
# MAIN MENU
# =========================================================

@dp.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):

    try:
        await callback.message.edit_text(
            "🏠 <b>منوی اصلی SaaS</b>\n\n"
            "چه کاری می‌خواهی انجام بدهی؟",
            reply_markup=main_menu()
        )

        await callback.answer()

    except Exception as e:
        logging.exception(f"Back main error: {e}")


# =========================================================
# TOOLS MENU
# =========================================================

@dp.callback_query(F.data == "tools")
async def tools_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "🧠 <b>مرکز ابزارهای SaaS</b>\n\n"
        "یک بخش را انتخاب کن:",
        reply_markup=tools_menu()
    )

    await callback.answer()


# =========================================================
# CHANNEL TOOLS
# =========================================================

def channel_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ ساخت کپشن",
                    callback_data="tool_caption"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎬 کپشن ویدیو",
                    callback_data="tool_video"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💡 ایده پست",
                    callback_data="tool_idea"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏷 هشتگ ساز",
                    callback_data="tool_hashtag"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📰 عنوان جذاب",
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


@dp.callback_query(F.data == "channel_tools")
async def channel_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "📢 <b>ابزارهای کانال تلگرام</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=channel_menu()
    )

    await callback.answer()


# =========================================================
# GROUP TOOLS
# =========================================================

def group_menu():

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
                    text="📢 اطلاعیه گروه",
                    callback_data="tool_group_notice"
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
                    text="❓ ساخت FAQ",
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


@dp.callback_query(F.data == "group_tools")
async def group_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "👥 <b>ابزارهای گروه</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=group_menu()
    )

    await callback.answer()


# =========================================================
# INSTAGRAM TOOLS
# =========================================================

def instagram_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 کپشن اینستاگرام",
                    callback_data="tool_caption"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎬 کپشن ریلز",
                    callback_data="tool_video"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 ساخت Bio",
                    callback_data="tool_bio"
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
                    text="💡 ایده ریلز",
                    callback_data="tool_idea"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎯 عنوان پست",
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


@dp.callback_query(F.data == "insta_tools")
async def insta_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "📸 <b>ابزارهای اینستاگرام</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=instagram_menu()
    )

    await callback.answer()


# =========================================================
# TEXT TOOLS
# =========================================================

def text_menu():

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
                    text="🛍 متن محصول",
                    callback_data="tool_product"
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
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]
        ]
    )


@dp.callback_query(F.data == "text_tools")
async def text_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "✍️ <b>ابزارهای متن</b>\n\n"
        "یکی از ابزارها را انتخاب کن:",
        reply_markup=text_menu()
    )

    await callback.answer()


# =========================================================
# CONTENT TOOLS
# =========================================================

def content_menu():

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
                    text="📅 برنامه ۳۰ روزه",
                    callback_data="tool_plan30"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💡 ایده‌های محتوا",
                    callback_data="tool_idea"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎯 تقویم محتوایی",
                    callback_data="tool_calendar"
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


@dp.callback_query(F.data == "content_tools")
async def content_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "📅 <b>برنامه‌ریزی محتوا</b>\n\n"
        "نوع برنامه را انتخاب کن:",
        reply_markup=content_menu()
    )

    await callback.answer()


# =========================================================
# TOOL STARTER
# =========================================================

async def start_tool(
    callback: CallbackQuery,
    state: FSMContext,
    state_name,
    title: str,
    description: str
):

    try:

        if not await is_member(
            callback.from_user.id
        ):

            await callback.answer(
                "❌ ابتدا باید عضو کانال شوی.",
                show_alert=True
            )

            return

        await state.set_state(state_name)

        await callback.message.edit_text(
            f"🛠 <b>{title}</b>\n\n"
            f"{description}\n\n"
            "📩 اطلاعاتت را در یک پیام بفرست.\n\n"
            "برای لغو: /cancel"
        )

        await callback.answer()

    except Exception as e:

        logging.exception(
            f"Tool starter error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# TOOL CALLBACKS
# =========================================================

@dp.callback_query(F.data == "tool_caption")
async def tool_caption(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.caption,
        "✍️ ساخت کپشن",
        "موضوع یا متن پستت را بفرست."
    )


@dp.callback_query(F.data == "tool_video")
async def tool_video(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.video_caption,
        "🎬 کپشن ویدیو",
        "موضوع ویدیو یا توضیح کوتاهی درباره آن را بفرست."
    )


@dp.callback_query(F.data == "tool_comment")
async def tool_comment(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.comment,
        "💬 ساخت کامنت",
        "موضوع پست یا متن موردنظر را بفرست."
    )


@dp.callback_query(F.data == "tool_reply")
async def tool_reply(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.reply,
        "🗣 پاسخ به کاربر",
        "پیام کاربر را بفرست."
    )


@dp.callback_query(F.data == "tool_bio")
async def tool_bio(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.bio,
        "👤 ساخت Bio",
        "موضوع پیج، زمینه فعالیت و سبک موردنظرت را بفرست."
    )


@dp.callback_query(F.data == "tool_hashtag")
async def tool_hashtag(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.hashtag,
        "🏷 هشتگ ساز",
        "موضوع پست یا پیج را بفرست."
    )


@dp.callback_query(F.data == "tool_title")
async def tool_title(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.title,
        "📰 عنوان جذاب",
        "موضوع محتوا را بفرست."
    )


@dp.callback_query(F.data == "tool_idea")
async def tool_idea(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.post_idea,
        "💡 ایده محتوا",
        "زمینه فعالیت یا موضوع پیج/کانالت را بفرست."
    )


@dp.callback_query(F.data == "tool_ad")
async def tool_ad(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.ad,
        "📢 متن تبلیغ",
        "محصول، خدمات یا کانالت را توضیح بده."
    )


@dp.callback_query(F.data == "tool_announcement")
async def tool_announcement(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.announcement,
        "📌 اطلاعیه",
        "موضوع اطلاعیه و اطلاعاتی که باید اعلام شود را بفرست."
    )


@dp.callback_query(F.data == "tool_rewrite")
async def tool_rewrite(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.rewrite,
        "✏️ بازنویسی متن",
        "متنی که می‌خواهی بازنویسی شود را بفرست."
    )


@dp.callback_query(F.data == "tool_summary")
async def tool_summary(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.summary,
        "📋 خلاصه‌سازی",
        "متن موردنظر را بفرست."
    )


@dp.callback_query(F.data == "tool_product")
async def tool_product(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.product,
        "🛍 متن محصول",
        "نام محصول، ویژگی‌ها و اطلاعات آن را بفرست."
    )


@dp.callback_query(F.data == "tool_poll")
async def tool_poll(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.poll,
        "📊 ساخت نظرسنجی",
        "موضوع نظرسنجی و گزینه‌های موردنظر را بفرست."
    )


@dp.callback_query(F.data == "tool_faq")
async def tool_faq(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.faq,
        "❓ ساخت FAQ",
        "موضوع، محصول یا خدماتت را بفرست."
    )


@dp.callback_query(F.data == "tool_plan")
async def tool_plan(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        ToolState.plan,
        "📅 برنامه ۷ روزه",
        "زمینه فعالیت و هدفت را بفرست."
    )


# =========================================================
# CANCEL
# =========================================================

@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "✅ عملیات لغو شد.",
        reply_markup=main_menu()
    )


# =========================================================
# ACCOUNT
# =========================================================

@dp.callback_query(F.data == "account")
async def account_callback(
    callback: CallbackQuery
):

    try:

        user_id = callback.from_user.id

        user = get_user(user_id)

        if not user:

            add_user(user_id)

            user = get_user(user_id)

        plan = "FREE"
        expire = None

        if user and len(user) >= 3:

            plan = user[1] or "FREE"
            expire = user[2]

        plan_text = (
            "⭐ VIP"
            if plan == "VIP"
            else "🆓 FREE"
        )

        text = (
            "👤 <b>حساب کاربری</b>\n\n"
            f"🆔 شناسه: <code>{user_id}</code>\n"
            f"📦 پلن: <b>{plan_text}</b>\n"
        )

        if expire:
            text += (
                f"⏳ انقضا: <b>{expire}</b>\n"
            )

        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⭐ خرید VIP",
                            callback_data="vip"
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
        )

        await callback.answer()

    except Exception as e:

        logging.exception(
            f"Account error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی در حساب کاربری رخ داد.",
            show_alert=True
        )


# =========================================================
# VIP
# =========================================================

@dp.callback_query(F.data == "vip")
async def vip_callback(
    callback: CallbackQuery
):

    buttons = []

    if SUPPORT_USERNAME:

        buttons.append([
            InlineKeyboardButton(
                text="💬 پشتیبانی",
                url=f"https://t.me/{SUPPORT_USERNAME}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_main"
        )
    ])

    await callback.message.edit_text(
        "⭐ <b>VIP SaaS</b>\n\n"
        f"💰 قیمت: <b>{VIP_PRICE}</b> تومان\n"
        "⏳ مدت: <b>۳۰ روز</b>\n\n"
        "مزایا:\n"
        "• سهمیه بیشتر\n"
        "• دسترسی گسترده‌تر\n"
        "• ابزارهای بیشتر\n"
        "• مناسب مدیریت کانال، گروه و پیج\n\n"
        "برای فعال‌سازی با پشتیبانی تماس بگیر.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )

    await callback.answer()


# =========================================================
# HELP
# =========================================================

@dp.callback_query(F.data == "help")
async def help_callback(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "📚 <b>راهنمای SaaS</b>\n\n"
        "🛠 از بخش ابزارها می‌توانی ابزارهای مختلف "
        "تولید محتوا را انتخاب کنی.\n\n"
        "📢 کانال\n"
        "👥 گروه\n"
        "📸 اینستاگرام\n"
        "✍️ متن\n"
        "📅 برنامه محتوا\n\n"
        "برای لغو هر عملیات:\n"
        "/cancel",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 بازگشت",
                        callback_data="back_main"
                    )
                ]
            ]
        )
    )

    await callback.answer()

# =========================================================
# FALLBACK
# =========================================================

@dp.message()
async def fallback(message: Message, state: FSMContext):

    current_state = await state.get_state()

    # اگر کاربر داخل یکی از ابزارهاست ولی
    # برای آن ابزار handler اختصاصی نوشته نشده
    if current_state:

        await message.answer(
            "📩 پیام دریافت شد.\n\n"
            "⚠️ پردازش این ابزار هنوز برای این نسخه فعال نشده است.\n\n"
            "برای خروج از ابزار:\n"
            "/cancel",
        )

        return

    # پیام عادی خارج از ابزارها
    await message.answer(
        "🤖 <b>SaaS</b>\n\n"
        "پیامت دریافت شد.\n\n"
        "برای استفاده از امکانات، یکی از گزینه‌های زیر را انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# ERROR HANDLER
# =========================================================

@dp.error()
async def global_error_handler(event):

    logging.exception(
        "Unhandled bot error: %s",
        event.exception
    )

    return True


# =========================================================
# BOT STARTUP
# =========================================================

async def main():

    logging.info("====================================")
    logging.info("Starting SaaS Bot...")
    logging.info("====================================")

    try:

        # اگر webhook قبلی وجود داشته باشد،
        # حذف می‌شود تا polling بتواند اجرا شود.
        await bot.delete_webhook(
            drop_pending_updates=True
        )

        me = await bot.get_me()

        logging.info(
            "Bot connected successfully: @%s | ID: %s",
            me.username,
            me.id
        )

        logging.info(
            "Starting polling..."
        )

        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )

    except Exception as e:

        logging.exception(
            "Fatal bot error: %s",
            e
        )

        raise

    finally:

        await bot.session.close()

        logging.info(
            "Bot session closed."
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logging.info(
            "Bot stopped manually."
        )

    except Exception as e:

        logging.exception(
            "Bot stopped because of an error: %s",
            e
        )
