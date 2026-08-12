# =========================================================
# PART 1/5 — IMPORTS, SETTINGS, BOT, STATES, KEYBOARDS
# =========================================================

import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
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
# ENVIRONMENT VARIABLES
# =========================================================

TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ TOKEN یا BOT_TOKEN در Render تنظیم نشده است.")

CHANNEL_USERNAME = os.getenv(
    "CHANNEL_USERNAME",
    ""
).strip()

CHANNEL_USERNAME2 = os.getenv(
    "CHANNEL_USERNAME2",
    ""
).strip()

VIP_PRICE = os.getenv(
    "VIP_PRICE",
    "199000"
).strip()

VIP_DAYS = os.getenv(
    "VIP_DAYS",
    "30"
).strip()

CARD_NUMBER = os.getenv(
    "CARD_NUMBER",
    ""
).strip()

SUPPORT_USERNAME = os.getenv(
    "SUPPORT_USERNAME",
    ""
).strip().replace("@", "")

ADMIN_ID = os.getenv(
    "ADMIN_ID",
    ""
).strip()


# =========================================================
# REQUIRED ENV CHECK
# =========================================================

if not TOKEN:
    raise RuntimeError(
        "❌ ENV با نام TOKEN تنظیم نشده است."
    )

if not CHANNEL_USERNAME:
    raise RuntimeError(
        "❌ ENV با نام CHANNEL_USERNAME تنظیم نشده است."
    )


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )
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
# STATES
# =========================================================

class ToolState(StatesGroup):

    # Channel
    caption = State()
    video_caption = State()
    post_idea = State()
    hashtag = State()
    title = State()
    advertisement = State()
    announcement = State()

    # Group
    comment = State()
    reply = State()
    poll = State()
    faq = State()

    # Instagram / profile
    bio = State()
    instagram_caption = State()

    # Text
    rewrite = State()
    summary = State()
    product = State()

    # Content
    content_plan = State()

    # VIP
    vip_payment = State()


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(
    text: str,
    limit: int = 5000
) -> str:

    if not text:
        return ""

    text = str(text).strip()

    if len(text) > limit:
        return text[:limit] + "..."

    return text


def username_without_at(
    username: str
) -> str:

    return str(username or "").strip().replace("@", "")


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
                    text="📸 اینستاگرام / پیج",
                    callback_data="insta_tools"
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
# CHANNEL TOOLS
# =========================================================

def channel_tools_menu():

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
# GROUP TOOLS
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
                    text="🗣 ساخت پاسخ",
                    callback_data="tool_reply"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 متن اطلاعیه گروه",
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


# =========================================================
# INSTAGRAM TOOLS
# =========================================================

def insta_tools_menu():

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
                    text="📸 کپشن پست",
                    callback_data="tool_instagram_caption"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎯 ایده محتوا",
                    callback_data="tool_post_idea"
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
                    text="📰 عنوان جذاب",
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


# =========================================================
# TEXT TOOLS
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
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]

        ]
    )


# =========================================================
# CONTENT TOOLS
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
                    text="💡 ایده‌های محتوایی",
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


# =========================================================
# BACK BUTTONS
# =========================================================

def back_main_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 منوی اصلی",
                    callback_data="back_main"
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
# CHANNEL JOIN KEYBOARD
# =========================================================

def join_keyboard():

    username = username_without_at(
        CHANNEL_USERNAME
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📢 عضویت در کانال",
                    url=f"https://t.me/{username}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✅ بررسی عضویت",
                    callback_data="check_join"
                )
            ]

        ]
    )


# =========================================================
# END OF PART 1/5
# =========================================================

# =========================================================
# bot.py — PART 2/5
# KEYBOARDS + REQUIRED CHANNELS + MAIN MENU
# =========================================================


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
                    text="📢 کانال تلگرام",
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
                    text="📸 اینستاگرام",
                    callback_data="insta_tools"
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
# CHANNEL TOOLS MENU
# =========================================================

def channel_tools_menu():

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
# GROUP TOOLS MENU
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


# =========================================================
# INSTAGRAM TOOLS MENU
# =========================================================

def insta_tools_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📝 کپشن اینستاگرام",
                    callback_data="tool_caption"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎬 کپشن ریلز",
                    callback_data="tool_video_caption"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👤 Bio ساز",
                    callback_data="tool_bio"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💡 ایده ریلز",
                    callback_data="tool_post_idea"
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


# =========================================================
# TEXT TOOLS MENU
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
                    text="🔙 بازگشت",
                    callback_data="tools"
                )
            ]

        ]
    )


# =========================================================
# CONTENT TOOLS MENU
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


# =========================================================
# BACK BUTTONS
# =========================================================

def back_main_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🔙 منوی اصلی",
                    callback_data="back_main"
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
# REQUIRED CHANNEL CHECK
# =========================================================

async def is_member(
    channel: str,
    user_id: int
) -> bool:

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
            "Channel check failed | "
            f"channel={channel} | "
            f"user={user_id} | "
            f"error={e}"
        )

        return False


async def check_channels(
    user_id: int
) -> bool:

    # اگر CHANNEL_1 و CHANNEL_2 تنظیم شده باشند
    # هر دو بررسی می‌شوند.

    if CHANNEL_1:

        first = await is_member(
            CHANNEL_1,
            user_id
        )

        if not first:
            return False

    # اگر CHANNEL_1/2 استفاده نکرده‌ای
    # CHANNEL_USERNAME نیز قابل استفاده است.

    if CHANNEL_2:

        second = await is_member(
            CHANNEL_2,
            user_id
        )

        if not second:
            return False

    elif CHANNEL_USERNAME:

        single = await is_member(
            CHANNEL_USERNAME,
            user_id
        )

        if not single:
            return False

    return True


# =========================================================
# JOIN KEYBOARD
# =========================================================

def join_keyboard():

    rows = []

    # کانال اول
    if CHANNEL_LINK_1:

        rows.append(
            [
                InlineKeyboardButton(
                    text="📢 عضویت کانال اول",
                    url=CHANNEL_LINK_1
                )
            ]
        )

    # کانال دوم
    if CHANNEL_LINK_2:

        rows.append(
            [
                InlineKeyboardButton(
                    text="📢 عضویت کانال دوم",
                    url=CHANNEL_LINK_2
                )
            ]
        )

    # اگر فقط CHANNEL_USERNAME وجود داشته باشد
    if (
        not CHANNEL_LINK_1
        and not CHANNEL_LINK_2
        and CHANNEL_USERNAME
    ):

        rows.append(
            [
                InlineKeyboardButton(
                    text="📢 عضویت کانال",
                    url=(
                        "https://t.me/"
                        + CHANNEL_USERNAME.replace("@", "")
                    )
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="✅ بررسی عضویت",
                callback_data="check_join"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


# =========================================================
# ACCESS CHECK
# =========================================================

async def user_has_access(
    user_id: int
) -> bool:

    if not await check_channels(user_id):
        return False

    return True


# =========================================================
# END OF PART 2/5
# =========================================================

# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext
):
    try:
        await state.clear()

        user_id = message.from_user.id

        add_user(user_id)

        if not await check_channels(user_id):
            await message.answer(
                "🚀 <b>به SaaS خوش آمدی!</b>\n\n"
                "برای استفاده از ربات ابتدا باید "
                "عضو کانال شوید.\n\n"
                "بعد از عضویت روی دکمه "
                "«بررسی عضویت» بزن.",
                reply_markup=join_keyboard()
            )
            return

        await message.answer(
            "🧠 <b>SaaS</b>\n\n"
            "دستیار مدیریت محتوا آماده است.\n\n"
            "📢 مدیریت کانال\n"
            "👥 ابزارهای گروه\n"
            "📸 ابزارهای اینستاگرام\n"
            "✍️ ابزارهای متن\n"
            "📅 برنامه محتوا\n\n"
            "از منوی زیر انتخاب کن:",
            reply_markup=main_menu()
        )

    except Exception as e:
        logging.exception(
            f"Start error: {e}"
        )

        await message.answer(
            "⚠️ مشکلی هنگام اجرای ربات رخ داد.\n"
            "لطفاً دوباره /start را بزن."
        )


# =========================================================
# CANCEL
# =========================================================

@dp.message(Command("cancel"))
async def cancel(
    message: Message,
    state: FSMContext
):
    await state.clear()

    await message.answer(
        "✅ عملیات لغو شد.",
        reply_markup=main_menu()
    )


# =========================================================
# JOIN CHECK
# =========================================================

@dp.callback_query(
    F.data == "check_join"
)
async def check_join(
    callback: CallbackQuery
):
    try:
        user_id = callback.from_user.id

        if not await check_channels(user_id):

            await callback.answer(
                "❌ هنوز عضو کانال نشده‌ای.",
                show_alert=True
            )

            return

        await callback.message.edit_text(
            "✅ <b>عضویت تأیید شد!</b>\n\n"
            "SaaS با موفقیت فعال شد 🧠",
            reply_markup=main_menu()
        )

        await callback.answer(
            "عضویت تأیید شد ✅"
        )

    except Exception as e:

        logging.exception(
            f"Join check error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی در بررسی عضویت رخ داد.",
            show_alert=True
        )


# =========================================================
# END OF PART 3/5
# =========================================================

# =========================================================
# PART 4/5 — MENUS + VIP + ACCOUNT
# =========================================================

# =========================================================
# TOOLS MENU
# =========================================================

@dp.callback_query(F.data == "tools")
async def tools_callback(
    callback: CallbackQuery
):
    try:
        await callback.message.edit_text(
            "🛠 <b>مرکز ابزارهای SaaS</b>\n\n"
            "دسته موردنظر را انتخاب کن:",
            reply_markup=tools_menu()
        )

        await callback.answer()

    except Exception as e:
        logging.exception(
            f"Tools menu error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# CHANNEL TOOLS
# =========================================================

@dp.callback_query(F.data == "channel_tools")
async def channel_tools(
    callback: CallbackQuery
):
    try:
        await callback.message.edit_text(
            "📢 <b>ابزارهای کانال تلگرام</b>\n\n"
            "✍️ ساخت کپشن\n"
            "🎬 کپشن ویدیو\n"
            "💡 ایده پست\n"
            "🏷 هشتگ‌ساز\n"
            "📰 عنوان پست\n"
            "📢 متن تبلیغ\n"
            "📌 اطلاعیه\n\n"
            "ابزار موردنظر را انتخاب کن:",
            reply_markup=channel_tools_menu()
        )

        await callback.answer()

    except Exception as e:
        logging.exception(
            f"Channel tools error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# GROUP TOOLS
# =========================================================

@dp.callback_query(F.data == "group_tools")
async def group_tools(
    callback: CallbackQuery
):
    try:
        await callback.message.edit_text(
            "👥 <b>ابزارهای گروه</b>\n\n"
            "💬 ساخت کامنت\n"
            "🗣 پاسخ به کاربر\n"
            "📢 اطلاعیه\n"
            "📊 نظرسنجی\n"
            "❓ FAQ\n\n"
            "ابزار موردنظر را انتخاب کن:",
            reply_markup=group_tools_menu()
        )

        await callback.answer()

    except Exception as e:
        logging.exception(
            f"Group tools error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# INSTAGRAM TOOLS
# =========================================================

@dp.callback_query(F.data == "insta_tools")
async def insta_tools(
    callback: CallbackQuery
):
    try:
        await callback.message.edit_text(
            "📸 <b>ابزارهای اینستاگرام</b>\n\n"
            "📝 کپشن پست\n"
            "🎬 کپشن ریلز\n"
            "👤 Bio ساز\n"
            "🏷 هشتگ‌ساز\n"
            "💡 ایده محتوا\n"
            "🎯 عنوان جذاب\n\n"
            "ابزار موردنظر را انتخاب کن:",
            reply_markup=insta_tools_menu()
        )

        await callback.answer()

    except Exception as e:
        logging.exception(
            f"Instagram tools error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# TEXT TOOLS
# =========================================================

@dp.callback_query(F.data == "text_tools")
async def text_tools(
    callback: CallbackQuery
):
    try:
        await callback.message.edit_text(
            "✍️ <b>ابزارهای متن</b>\n\n"
            "✏️ بازنویسی متن\n"
            "📋 خلاصه‌سازی\n"
            "📰 عنوان‌سازی\n"
            "🏷 هشتگ‌سازی\n"
            "🛍 متن محصول\n\n"
            "ابزار موردنظر را انتخاب کن:",
            reply_markup=text_tools_menu()
        )

        await callback.answer()

    except Exception as e:
        logging.exception(
            f"Text tools error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# CONTENT TOOLS
# =========================================================

@dp.callback_query(F.data == "content_tools")
async def content_tools(
    callback: CallbackQuery
):
    try:
        await callback.message.edit_text(
            "📅 <b>برنامه محتوا</b>\n\n"
            "📅 برنامه ۷ روزه\n"
            "💡 ایده‌های محتوا\n"
            "🎯 عنوان‌های پیشنهادی\n\n"
            "ابزار موردنظر را انتخاب کن:",
            reply_markup=content_tools_menu()
        )

        await callback.answer()

    except Exception as e:
        logging.exception(
            f"Content tools error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# BACK TO MAIN
# =========================================================

@dp.callback_query(F.data == "back_main")
async def back_main(
    callback: CallbackQuery
):
    try:
        await callback.message.edit_text(
            "🏠 <b>منوی اصلی SaaS</b>\n\n"
            "یک گزینه را انتخاب کن:",
            reply_markup=main_menu()
        )

        await callback.answer()

    except Exception as e:
        logging.exception(
            f"Back main error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# VIP
# =========================================================

@dp.callback_query(F.data == "vip")
async def vip(
    callback: CallbackQuery
):
    try:

        buttons = []

        if CARD_NUMBER:

            buttons.append([
                InlineKeyboardButton(
                    text="💳 خرید VIP",
                    callback_data="vip_payment"
                )
            ])

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
            "⏳ مدت اعتبار: <b>۳۰ روز</b>\n\n"
            "مزایای VIP:\n"
            "✅ دسترسی گسترده‌تر به ابزارها\n"
            "✅ سهمیه بیشتر\n"
            "✅ مناسب مدیریت کانال و گروه\n"
            "✅ ابزارهای تولید محتوا\n"
            "✅ استفاده حرفه‌ای‌تر\n\n"
            "برای خرید VIP گزینه زیر را انتخاب کن.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=buttons
            )
        )

        await callback.answer()

    except Exception as e:

        logging.exception(
            f"VIP error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# ACCOUNT
# =========================================================

@dp.callback_query(F.data == "account")
async def account(
    callback: CallbackQuery
):
    try:

        user = get_user(
            callback.from_user.id
        )

        if not user:

            add_user(
                callback.from_user.id
            )

            user = get_user(
                callback.from_user.id
            )

        plan = "FREE"
        expire = None

        if user:

            if len(user) > 1:
                plan = user[1] or "FREE"

            if len(user) > 2:
                expire = user[2]

        plan_text = (
            "⭐ VIP"
            if plan == "VIP"
            else "🆓 FREE"
        )

        text = (
            "👤 <b>حساب کاربری</b>\n\n"
            f"🆔 شناسه: "
            f"<code>{callback.from_user.id}</code>\n\n"
            f"📦 پلن: <b>{plan_text}</b>\n"
        )

        if plan == "VIP" and expire:

            text += (
                f"⏳ تاریخ انقضا: "
                f"<b>{escape_html(str(expire))}</b>\n"
            )

        text += (
            "\n⭐ برای فعال‌سازی VIP "
            "از گزینه خرید VIP استفاده کن."
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
            "⚠️ خطایی در نمایش حساب رخ داد.",
            show_alert=True
        )


# =========================================================
# HELP
# =========================================================

@dp.callback_query(F.data == "help")
async def help_callback(
    callback: CallbackQuery
):
    try:

        await callback.message.edit_text(
            "📚 <b>راهنمای SaaS</b>\n\n"
            "1️⃣ ابتدا عضو کانال شوید.\n"
            "2️⃣ وارد بخش ابزارها شوید.\n"
            "3️⃣ دسته موردنظر را انتخاب کنید.\n"
            "4️⃣ ابزار موردنظر را انتخاب کنید.\n"
            "5️⃣ اطلاعات لازم را ارسال کنید.\n"
            "6️⃣ نتیجه را دریافت کنید.\n\n"
            "❌ برای لغو هر عملیات:\n"
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

    except Exception as e:

        logging.exception(
            f"Help error: {e}"
        )

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# END OF PART 4/5
# =========================================================


# =========================================================
# PART 5/5 — TOOLS + FALLBACK + RUN
# =========================================================

# =========================================================
# TOOL STARTER
# =========================================================

async def start_tool(
    callback: CallbackQuery,
    state: FSMContext,
    tool_name: str,
    state_obj: State,
    description: str
):

    try:

        if not await check_channels(
            callback.from_user.id
        ):
            await callback.answer(
                "❌ ابتدا باید عضو کانال شوید.",
                show_alert=True
            )
            return

        await state.set_state(
            state_obj
        )

        await callback.message.edit_text(
            f"🛠 <b>{tool_name}</b>\n\n"
            f"{description}\n\n"
            "📩 اطلاعات موردنظر را در یک پیام ارسال کن.\n\n"
            "❌ لغو: /cancel"
        )

        await callback.answer()

    except Exception as e:

        logging.exception(
            f"Start tool error: {e}"
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
        "✍️ ساخت کپشن",
        ToolState.caption,
        "موضوع، محصول یا متن پست را بفرست."
    )


@dp.callback_query(F.data == "tool_video_caption")
async def tool_video_caption(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "🎬 کپشن ویدیو",
        ToolState.video_caption,
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
        "💬 ساخت کامنت",
        ToolState.comment,
        "موضوع پست یا متنی که می‌خواهی برایش کامنت بسازی را بفرست."
    )


@dp.callback_query(F.data == "tool_reply")
async def tool_reply(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "🗣 پاسخ به کاربر",
        ToolState.reply,
        "پیام کاربر را بفرست تا چند مدل پاسخ مناسب دریافت کنی."
    )


@dp.callback_query(F.data == "tool_bio")
async def tool_bio(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "👤 Bio ساز",
        ToolState.bio,
        "موضوع پیج، زمینه فعالیت و سبک موردنظر را بنویس."
    )


@dp.callback_query(F.data == "tool_hashtag")
async def tool_hashtag(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "🏷 هشتگ‌ساز",
        ToolState.hashtag,
        "موضوع محتوا را بفرست."
    )


@dp.callback_query(F.data == "tool_title")
async def tool_title(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "📰 عنوان‌ساز",
        ToolState.title,
        "موضوع یا متن پست را بفرست."
    )


@dp.callback_query(F.data == "tool_post_idea")
async def tool_post_idea(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "💡 ایده محتوا",
        ToolState.post_idea,
        "زمینه فعالیت یا موضوع پیج/کانال را بفرست."
    )


@dp.callback_query(F.data == "tool_ad")
async def tool_ad(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "📢 متن تبلیغ",
        ToolState.ad,
        "محصول، خدمات یا کانالی که می‌خواهی تبلیغ شود را توضیح بده."
    )


@dp.callback_query(F.data == "tool_announcement")
async def tool_announcement(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "📌 اطلاعیه",
        ToolState.announcement,
        "موضوع اطلاعیه و اطلاعات مهم را بفرست."
    )


@dp.callback_query(F.data == "tool_rewrite")
async def tool_rewrite(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "✏️ بازنویسی متن",
        ToolState.rewrite,
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
        "📋 خلاصه‌سازی",
        ToolState.summary,
        "متن موردنظر را بفرست."
    )


@dp.callback_query(F.data == "tool_plan")
async def tool_plan(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "📅 برنامه ۷ روزه",
        ToolState.plan,
        "زمینه فعالیت، نوع پیج یا کانال و موضوع موردنظر را بفرست."
    )


@dp.callback_query(F.data == "tool_product")
async def tool_product(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "🛍 متن محصول",
        ToolState.product,
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
        "📊 نظرسنجی",
        ToolState.poll,
        "موضوع نظرسنجی را بفرست."
    )


@dp.callback_query(F.data == "tool_faq")
async def tool_faq(
    callback: CallbackQuery,
    state: FSMContext
):

    await start_tool(
        callback,
        state,
        "❓ FAQ",
        ToolState.faq,
        "موضوع کسب‌وکار، کانال یا گروه را بفرست."
    )


# =========================================================
# LOCAL CONTENT ENGINE
# =========================================================

def make_result(
    tool: str,
    text: str
) -> str:

    text = clean_text(text, 3000)

    if not text:
        return "⚠️ متن دریافت نشد."

    if tool == "caption":

        return (
            "✍️ <b>کپشن پیشنهادی</b>\n\n"
            f"{text}\n\n"
            "━━━━━━━━━━━━\n"
            "💡 پیشنهاد: در پایان کپشن یک دعوت به تعامل "
            "مثل «نظرت چیه؟» اضافه کن."
        )

    if tool == "video_caption":

        return (
            "🎬 <b>قالب کپشن ویدیو</b>\n\n"
            f"🔥 {text}\n\n"
            "این محتوا را از دست نده!\n"
            "اگر برات مفید بود ذخیره‌اش کن و برای دوستات بفرست."
        )

    if tool == "comment":

        return (
            "💬 <b>کامنت پیشنهادی</b>\n\n"
            f"«{text}»\n\n"
            "🔥 خیلی خوب و کاربردی بود!\n"
            "منتظر ادامه این محتوا هستم."
        )

    if tool == "reply":

        return (
            "🗣 <b>پاسخ پیشنهادی</b>\n\n"
            f"سلام! ممنون که نظرت رو گفتی 🙏\n\n"
            f"در مورد «{text}» حتماً بررسی می‌کنیم."
        )

    if tool == "bio":

        return (
            "👤 <b>Bio پیشنهادی</b>\n\n"
            f"🚀 {text}\n"
            "✨ محتوا | آموزش | تجربه\n"
            "📩 برای همکاری و ارتباط پیام بده"
        )

    if tool == "hashtag":

        words = re.findall(
            r"[\wآ-ی]+",
            text
        )

        tags = []

        for word in words[:12]:

            if len(word) >= 2:
                tags.append(
                    "#" + word.replace(" ", "")
                )

        if not tags:
            tags = [
                "#محتوا",
                "#تلگرام",
                "#اینستاگرام",
                "#تولید_محتوا"
            ]

        return (
            "🏷 <b>هشتگ‌های پیشنهادی</b>\n\n"
            + " ".join(tags)
        )

    if tool == "title":

        return (
            "📰 <b>عنوان‌های پیشنهادی</b>\n\n"
            f"1️⃣ {text} | چیزی که باید بدانید\n"
            f"2️⃣ {text}؛ ۵ نکته مهم\n"
            f"3️⃣ چرا {text} مهم است؟\n"
            f"4️⃣ راهنمای کامل {text}\n"
            f"5️⃣ قبل از شروع {text} این را بخوان"
        )

    if tool == "post_idea":

        return (
            "💡 <b>ایده‌های محتوا</b>\n\n"
            f"1️⃣ آموزش سریع درباره {text}\n"
            f"2️⃣ اشتباهات رایج در {text}\n"
            f"3️⃣ مقایسه دو روش در {text}\n"
            f"4️⃣ تجربه شخصی درباره {text}\n"
            f"5️⃣ پرسش و پاسخ درباره {text}\n"
            f"6️⃣ چک‌لیست کاربردی {text}\n"
            f"7️⃣ یک داستان کوتاه درباره {text}"
        )

    if tool == "ad":

        return (
            "📢 <b>متن تبلیغاتی</b>\n\n"
            f"🔥 اگر به «{text}» علاقه داری، این فرصت رو از دست نده!\n\n"
            "✅ کاربردی\n"
            "✅ سریع\n"
            "✅ مناسب استفاده روزمره\n\n"
            "📩 برای اطلاعات بیشتر پیام بده."
        )

    if tool == "announcement":

        return (
            "📌 <b>اطلاعیه</b>\n\n"
            f"🔔 موضوع: {text}\n\n"
            "لطفاً این اطلاعیه را مطالعه کنید و "
            "در صورت نیاز اقدامات لازم را انجام دهید.\n\n"
            "🙏 ممنون از همراهی شما."
        )

    if tool == "rewrite":

        return (
            "✏️ <b>نسخه بازنویسی‌شده</b>\n\n"
            f"{text}\n\n"
            "━━━━━━━━━━━━\n"
            "نسخه بالا را می‌توانی با لحن رسمی، دوستانه "
            "یا تبلیغاتی شخصی‌سازی کنی."
        )

    if tool == "summary":

        sentences = re.split(
            r"[.!؟\n]+",
            text
        )

        sentences = [
            s.strip()
            for s in sentences
            if s.strip()
        ]

        short = " ".join(
            sentences[:3]
        )

        return (
            "📋 <b>خلاصه</b>\n\n"
            f"{short}"
        )

    if tool == "plan":

        return (
            "📅 <b>برنامه محتوایی ۷ روزه</b>\n\n"
            f"شنبه: آموزش {text}\n"
            f"یکشنبه: نکته کوتاه {text}\n"
            f"دوشنبه: پرسش از مخاطب درباره {text}\n"
            f"سه‌شنبه: معرفی یک تجربه در {text}\n"
            f"چهارشنبه: اشتباهات رایج {text}\n"
            f"پنجشنبه: محتوای سرگرم‌کننده درباره {text}\n"
            f"جمعه: جمع‌بندی و تعامل درباره {text}"
        )

    if tool == "product":

        return (
            "🛍 <b>معرفی محصول</b>\n\n"
            f"⭐ {text}\n\n"
            "✨ ویژگی‌ها:\n"
            "• کاربردی\n"
            "• طراحی مناسب\n"
            "• استفاده آسان\n\n"
            "📩 برای سفارش و اطلاعات بیشتر پیام بده."
        )

    if tool == "poll":

        return (
            "📊 <b>نظرسنجی پیشنهادی</b>\n\n"
            f"❓ نظر شما درباره «{text}» چیست؟\n\n"
            "🟢 عالیه\n"
            "🟡 خوبه\n"
            "🔴 نیاز به تغییر داره"
        )

    if tool == "faq":

        return (
            "❓ <b>FAQ پیشنهادی</b>\n\n"
            f"سؤال ۱: {text} چیست؟\n"
            "پاسخ: توضیحات کامل درباره موضوع ارائه می‌شود.\n\n"
            f"سؤال ۲: مزیت {text} چیست؟\n"
            "پاسخ: مهم‌ترین مزایا را می‌توان اینجا توضیح داد.\n\n"
            f"سؤال ۳: چگونه از {text} استفاده کنیم؟\n"
            "پاسخ: مراحل استفاده به‌صورت ساده توضیح داده می‌شود."
        )

    return (
        "✅ <b>نتیجه</b>\n\n"
        f"{text}"
    )


# =========================================================
# STATE → TOOL
# =========================================================

STATE_TO_TOOL = {
    ToolState.caption: "caption",
    ToolState.video_caption: "video_caption",
    ToolState.comment: "comment",
    ToolState.reply: "reply",
    ToolState.bio: "bio",
    ToolState.hashtag: "hashtag",
    ToolState.title: "title",
    ToolState.post_idea: "post_idea",
    ToolState.ad: "ad",
    ToolState.announcement: "announcement",
    ToolState.rewrite: "rewrite",
    ToolState.summary: "summary",
    ToolState.plan: "plan",
    ToolState.product: "product",
    ToolState.poll: "poll",
    ToolState.faq: "faq",
}


# =========================================================
# GENERIC TOOL HANDLER
# =========================================================

@dp.message(
    F.text,
    ~F.text.startswith("/")
)
async def generic_tool_handler(
    message: Message,
    state: FSMContext
):

    current_state = await state.get_state()

    if not current_state:
        return

    try:

        tool = None

        for state_obj, tool_name in STATE_TO_TOOL.items():

            if current_state == state_obj.state:
                tool = tool_name
                break

        if not tool:
            return

        allowed = await user_has_access(
            message.from_user.id
        )

        if not allowed:

            await message.answer(
                "🔐 برای استفاده از ابزار ابتدا "
                "عضویت کانال را تکمیل کن.",
                reply_markup=main_menu()
            )

            await state.clear()

            return

        result = make_result(
            tool,
            message.text
        )

        await message.answer(
            result,
            reply_markup=back_tools()
        )

        await state.clear()

    except Exception as e:

        logging.exception(
            f"Generic tool error: {e}"
        )

        await message.answer(
            "⚠️ هنگام پردازش درخواست مشکلی رخ داد.\n"
            "دوباره امتحان کن."
        )

        await state.clear()


# =========================================================
# VIP PAYMENT
# =========================================================

@dp.message(
    F.photo,
    StateFilter(ToolState.vip_payment)
)
async def vip_receipt_photo(
    message: Message,
    state: FSMContext
):

    try:

        await message.answer(
            "✅ رسید دریافت شد.\n\n"
            "📨 برای بررسی به مدیریت ارسال شد.\n"
            "بعد از تأیید، VIP فعال می‌شود."
        )

        if ADMIN_ID:

            try:

                await bot.send_photo(
                    ADMIN_ID,
                    message.photo[-1].file_id,
                    caption=(
                        "💳 <b>رسید VIP جدید</b>\n\n"
                        f"👤 کاربر: "
                        f"{escape_html(username_of(message))}\n"
                        f"🆔 ID: "
                        f"<code>{message.from_user.id}</code>\n"
                        f"💰 مبلغ: {VIP_PRICE} تومان"
                    )
                )

            except Exception as e:

                logging.warning(
                    f"Admin receipt send failed: {e}"
                )

        await state.clear()

    except Exception:

        logging.exception(
            "VIP receipt error"
        )

        await message.answer(
            "⚠️ دریافت رسید با مشکل مواجه شد."
        )


# =========================================================
# VIP PAYMENT TEXT
# =========================================================

@dp.message(
    StateFilter(ToolState.vip_payment),
    F.text
)
async def vip_receipt_text(
    message: Message,
    state: FSMContext
):

    try:

        if ADMIN_ID:

            try:

                await bot.send_message(
                    ADMIN_ID,
                    (
                        "💳 <b>اطلاعات پرداخت VIP</b>\n\n"
                        f"👤 کاربر: "
                        f"{escape_html(username_of(message))}\n"
                        f"🆔 ID: "
                        f"<code>{message.from_user.id}</code>\n"
                        f"💰 مبلغ: {VIP_PRICE} تومان\n\n"
                        f"📝 اطلاعات:\n"
                        f"{escape_html(message.text)}"
                    )
                )

            except Exception as e:

                logging.warning(
                    f"Admin payment send failed: {e}"
                )

        await message.answer(
            "✅ اطلاعات پرداخت دریافت شد.\n\n"
            "پس از بررسی مدیریت، VIP فعال خواهد شد."
        )

        await state.clear()

    except Exception:

        logging.exception(
            "VIP payment text error"
        )

        await message.answer(
            "⚠️ خطایی رخ داد."
        )


# =========================================================
# ADMIN — ACTIVATE VIP
# =========================================================

@dp.message(Command("vip"))
async def admin_vip(
    message: Message
):

    if not ADMIN_ID:
        return

    if message.from_user.id != int(ADMIN_ID):
        return

    parts = message.text.split()

    if len(parts) < 2:

        await message.answer(
            "استفاده:\n"
            "<code>/vip USER_ID</code>"
        )

        return

    try:

        user_id = int(parts[1])

    except ValueError:

        await message.answer(
            "❌ USER_ID نامعتبر است."
        )

        return

    try:

        expire = datetime.now() + timedelta(
            days=30
        )

        set_vip(
            user_id,
            expire.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        await message.answer(
            "✅ VIP با موفقیت فعال شد."
        )

        try:

            await bot.send_message(
                user_id,
                "🎉 <b>VIP شما فعال شد!</b>\n\n"
                "⏳ اعتبار: ۳۰ روز\n"
                "⭐ از امکانات VIP استفاده کن."
            )

        except Exception:
            pass

    except Exception as e:

        logging.exception(
            f"VIP activation error: {e}"
        )

        await message.answer(
            "⚠️ فعال‌سازی VIP انجام نشد."
        )


# =========================================================
# FALLBACK
# =========================================================

@dp.message()
async def fallback(
    message: Message
):

    await message.answer(
        "🤔 متوجه درخواستت نشدم.\n\n"
        "از منوی زیر یکی از گزینه‌ها را انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# ERROR HANDLER
# =========================================================

@dp.errors()
async def global_error_handler(
    event
):

    logging.exception(
        f"Unhandled bot error: {event.exception}"
    )

    return True


# =========================================================
# STARTUP
# =========================================================

async def main():

    logging.info(
        "Starting SaaS bot..."
    )

    try:

        await bot.delete_webhook(
            drop_pending_updates=True
        )

    except Exception as e:

        logging.warning(
            f"Webhook cleanup failed: {e}"
        )

    logging.info(
        "Bot is running..."
    )

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except (KeyboardInterrupt, SystemExit):

        logging.info(
            "Bot stopped."
    )

