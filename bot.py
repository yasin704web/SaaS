import asyncio
import logging
import os
import re
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ADMIN_ID

from database import (
    init_db,
    add_user,
    get_user,
    update_activity,
    count_users,
    count_purchases,
    total_income,
    set_vip,
    add_purchase,
)

from subscription import check_access


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("SaaS")


# =========================================================
# SETTINGS
# =========================================================

CHANNEL_1 = os.getenv("CHANNEL_1", "").strip()
CHANNEL_2 = os.getenv("CHANNEL_2", "").strip()

CHANNEL_LINK_1 = os.getenv("CHANNEL_LINK_1", "").strip()
CHANNEL_LINK_2 = os.getenv("CHANNEL_LINK_2", "").strip()

VIP_PRICE = os.getenv("VIP_PRICE", "199000").strip()
CARD_NUMBER = os.getenv("CARD_NUMBER", "").strip()

SUPPORT_USERNAME = os.getenv(
    "SUPPORT_USERNAME",
    ""
).strip().replace("@", "")


# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


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
    ad = State()
    announcement = State()
    rewrite = State()
    summary = State()
    plan = State()
    product = State()
    poll = State()
    faq = State()

    vip_payment = State()


# =========================================================
# SAFE TEXT
# =========================================================

def clean_text(text: str, limit: int = 5000) -> str:
    if not text:
        return ""

    text = text.strip()

    if len(text) > limit:
        text = text[:limit] + "..."

    return text


def escape_html(text: str) -> str:
    if not text:
        return ""

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def username_of(message: Message) -> str:
    username = message.from_user.username

    if username:
        return f"@{username}"

    return str(message.from_user.id)


# =========================================================
# KEYBOARDS
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


def tools_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 ابزارهای کانال",
                    callback_data="channel_tools"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 ابزارهای گروه",
                    callback_data="group_tools"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 ابزارهای پیج",
                    callback_data="profile_tools"
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


def channel_tools_menu():
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
                    text="📊 نظرسنجی",
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


def profile_tools_menu():
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
                    text="📸 کپشن عکس",
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
                    text="💡 ایده محتوا",
                    callback_data="tool_post_idea"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏷 هشتگ",
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


def text_tools_menu():
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
                    text="💡 ایده محتوا",
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
# REQUIRED CHANNELS
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
            f"Channel check failed: {channel} | {e}"
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


# =========================================================
# ACCESS
# =========================================================

async def verify_access(user_id: int) -> tuple:

    if not await check_channels(user_id):
        return False, (
            "🔐 برای استفاده از SaaS ابتدا باید "
            "در هر دو کانال عضو شوی."
        )

    try:

        allowed, result = check_access(user_id)

        if not allowed:
            return False, result

        return True, result

    except Exception as e:

        logger.exception(
            f"Subscription error for {user_id}: {e}"
        )

        return False, (
            "⚠️ در بررسی حساب مشکلی پیش آمد.\n"
            "لطفاً دوباره تلاش کن."
        )


# =========================================================
# START
# =========================================================

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):

    try:

        await state.clear()

        user = message.from_user

        add_user(
            user.id,
            user.username or ""
        )

        update_activity(
            user.id
        )

        if not await check_channels(user.id):

            await message.answer(
                "🚀 <b>به SaaS خوش آمدی!</b>\n\n"
                "برای استفاده از ربات ابتدا باید "
                "در دو کانال ما عضو شوی.\n\n"
                "بعد از عضویت روی «بررسی عضویت» بزن.",
                reply_markup=join_keyboard()
            )

            return

        await message.answer(
            "🧠 <b>SaaS</b>\n\n"
            "دستیار حرفه‌ای مدیریت محتوا آماده است.\n\n"
            "📢 کانال\n"
            "👥 گروه\n"
            "👤 پیج شخصی\n"
            "✍️ ابزار متن\n"
            "📅 برنامه محتوا\n\n"
            "از منوی زیر شروع کن:",
            reply_markup=main_menu()
        )

    except Exception:

        logger.exception("Start handler failed")

        await message.answer(
            "⚠️ مشکلی پیش آمد. لطفاً دوباره /start را بزن."
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
# JOIN CHECK
# =========================================================

@dp.callback_query(F.data == "check_join")
async def check_join(callback: CallbackQuery):

    try:

        if not await check_channels(
            callback.from_user.id
        ):

            await callback.answer(
                "❌ هنوز عضویت هر دو کانال تأیید نشده.",
                show_alert=True
            )

            return

        await callback.message.edit_text(
            "✅ <b>عضویت تأیید شد!</b>\n\n"
            "SaaS آماده استفاده است 🧠",
            reply_markup=main_menu()
        )

        await callback.answer(
            "عضویت تأیید شد ✅"
        )

    except Exception:

        logger.exception("Join check failed")

        await callback.answer(
            "⚠️ خطایی رخ داد.",
            show_alert=True
        )


# =========================================================
# MENU CALLBACKS
# =========================================================

@dp.callback_query(F.data == "tools")
async def tools_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "🛠 <b>مرکز ابزارهای SaaS</b>\n\n"
        "دسته موردنظر را انتخاب کن:",
        reply_markup=tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "channel_tools")
async def channel_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "📢 <b>ابزارهای کانال</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=channel_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "group_tools")
async def group_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "👥 <b>ابزارهای گروه</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=group_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "profile_tools")
async def profile_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "👤 <b>ابزارهای پیج شخصی</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=profile_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "text_tools")
async def text_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "✍️ <b>ابزارهای متن</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=text_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "content_tools")
async def content_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "📅 <b>برنامه محتوا</b>\n\n"
        "ابزار موردنظر را انتخاب کن:",
        reply_markup=content_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery):

    await callback.message.edit_text(
        "🧠 <b>SaaS</b>\n\n"
        "یک بخش را انتخاب کن:",
        reply_markup=main_menu()
    )

    await callback.answer()


# =========================================================
# VIP
# =========================================================

@dp.callback_query(F.data == "vip")
async def vip_callback(
    callback: CallbackQuery,
    state: FSMContext
):

    buttons = []

    if CARD_NUMBER:

        buttons.append([
            InlineKeyboardButton(
                text="💳 پرداخت کارت‌به‌کارت",
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
        "⏳ مدت: <b>۳۰ روز</b>\n\n"
        "مزایا:\n"
        "• استفاده بدون محدودیت FREE\n"
        "• دسترسی کامل‌تر به ابزارها\n"
        "• مناسب مدیریت کانال و پیج\n"
        "• اعتبار ۳۰ روزه\n\n"
        "برای خرید گزینه زیر را انتخاب کن.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )

    await callback.answer()


@dp.callback_query(F.data == "vip_payment")
async def vip_payment(
    callback: CallbackQuery,
    state: FSMContext
):

    if not CARD_NUMBER:

        await callback.answer(
            "روش پرداخت هنوز تنظیم نشده.",
            show_alert=True
        )

        return

    await state.set_state(
        ToolState.vip_payment
    )

    await callback.message.edit_text(
        "💳 <b>خرید VIP</b>\n\n"
        f"مبلغ: <b>{VIP_PRICE}</b> تومان\n\n"
        f"شماره کارت:\n"
        f"<code>{CARD_NUMBER}</code>\n\n"
        "پس از کارت‌به‌کارت، "
        "عکس رسید یا اطلاعات پرداخت را ارسال کن.\n\n"
        "بعد از بررسی ادمین، VIP برایت فعال می‌شود.\n\n"
        "برای لغو: /cancel"
    )

    await callback.answer()


# =========================================================
# ACCOUNT
# =========================================================

@dp.callback_query(F.data == "account")
async def account_callback(callback: CallbackQuery):

    try
