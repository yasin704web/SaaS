import asyncio
import logging
import os
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
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
)

from subscription import check_access


# =========================================================
# SETTINGS
# =========================================================

CHANNEL_1 = os.getenv("CHANNEL_1", "")
CHANNEL_2 = os.getenv("CHANNEL_2", "")

CHANNEL_LINK_1 = os.getenv("CHANNEL_LINK_1", "")
CHANNEL_LINK_2 = os.getenv("CHANNEL_LINK_2", "")

VIP_PRICE = os.getenv("VIP_PRICE", "199000")

FREE_LIMIT_TEXT = "محدودیت روزانه بر اساس پلن فعلی شما اعمال می‌شود."

logging.basicConfig(level=logging.INFO)


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

    waiting_caption = State()
    waiting_video_caption = State()
    waiting_comment = State()
    waiting_reply = State()
    waiting_bio = State()
    waiting_hashtag = State()
    waiting_title = State()
    waiting_post_idea = State()
    waiting_ad = State()
    waiting_announcement = State()
    waiting_rewrite = State()
    waiting_summary = State()
    waiting_content_plan = State()
    waiting_product_text = State()
    waiting_poll = State()


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
                    text="👤 ابزارهای پیج شخصی",
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
                    text="🔙 بازگشت",
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
                    text="🏷 هشتگ ساز",
                    callback_data="tool_hashtag"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📰 عنوان پست",
                    callback_data="tool_title"
                ),
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
# REQUIRED CHANNELS
# =========================================================

async def is_member(channel, user_id):

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

        logging.warning(
            f"Channel check failed: {channel} | {e}"
        )

        return False


async def check_channels(user_id):

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

    buttons = []

    if CHANNEL_LINK_1:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="📢 عضویت کانال اول",
                    url=CHANNEL_LINK_1
                )
            ]
        )

    if CHANNEL_LINK_2:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="📢 عضویت کانال دوم",
                    url=CHANNEL_LINK_2
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="✅ بررسی عضویت",
                callback_data="check_join"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


async def require_access(message: Message):

    user_id = message.from_user.id

    if not await check_channels(user_id):

        await message.answer(
            "🔐 <b>قبل از استفاده از SaaS</b>\n\n"
            "برای استفاده از ربات ابتدا باید در "
            "هر دو کانال عضو شوید.\n\n"
            "بعد از عضویت روی «بررسی عضویت» بزنید.",
            reply_markup=join_keyboard()
        )

        return False

    allowed, result = check_access(user_id)

    if not allowed:

        await message.answer(
            result
        )

        return False

    return True


# =========================================================
# START
# =========================================================

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):

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
            "برای شروع باید ابتدا عضو دو کانال ما شوی.\n\n"
            "بعد از عضویت روی «بررسی عضویت» بزن.",
            reply_markup=join_keyboard()
        )

        return

    await message.answer(
        "🧠 <b>SaaS</b>\n\n"
        "دستیار مدیریت و تولید محتوای تو آماده است.\n\n"
        "🛠 ابزارهای تولید محتوا\n"
        "📢 ابزارهای کانال\n"
        "👥 ابزارهای گروه\n"
        "👤 ابزارهای پیج\n"
        "📅 برنامه‌ریزی محتوا\n\n"
        "یک بخش را انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================================================
# JOIN CHECK
# =========================================================

@dp.callback_query(F.data == "check_join")
async def check_join(callback: CallbackQuery):

    user_id = callback.from_user.id

    if not await check_channels(user_id):

        await callback.answer(
            "❌ هنوز در هر دو کانال عضو نشده‌ای.",
            show_alert=True
        )

        return

    await callback.message.edit_text(
        "✅ عضویت تأیید شد!\n\n"
        "به SaaS خوش آمدی 🧠",
        reply_markup=main_menu()
    )

    await callback.answer(
        "عضویت تأیید شد ✅"
    )


# =========================================================
# MAIN CALLBACKS
# =========================================================

@dp.callback_query(F.data == "tools")
async def tools_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "🛠 <b>مرکز ابزارهای SaaS</b>\n\n"
        "بخش موردنظر خودت را انتخاب کن:",
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
        "یکی از ابزارها را انتخاب کن:",
        reply_markup=text_tools_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "content_tools")
async def content_tools(callback: CallbackQuery):

    await callback.message.edit_text(
        "📅 <b>مرکز برنامه‌ریزی محتوا</b>\n\n"
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
async def vip_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "⭐ <b>VIP SaaS</b>\n\n"
        f"💰 قیمت: <b>{VIP_PRICE}</b> تومان\n"
        "⏳ مدت: <b>۳۰ روز</b>\n\n"
        "مزایا:\n"
        "• استفاده بیشتر از ابزارها\n"
        "• دسترسی گسترده‌تر\n"
        "• امکانات پیشرفته‌تر\n\n"
        "برای خرید VIP با پشتیبانی ارتباط بگیر.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 ارتباط با پشتیبانی",
                        url="https://t.me/"
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


# =========================================================
# ACCOUNT
# =========================================================

@dp.callback_query(F.data == "account")
async def account_callback(callback: CallbackQuery):

    user = get_user(
        callback.from_user.id
    )

    if not user:

        await callback.answer(
            "حساب پیدا نشد.",
            show_alert=True
        )

        return

    plan = user[5] if len(user) > 5 else "FREE"
    expire = user[6] if len(user) > 6 else None
    usage = user[7] if len(user) > 7 else 0

    if plan == "VIP":

        plan_text = "⭐ VIP"

    else:

        plan_text = "🆓 FREE"

    text = (
        "👤 <b>حساب من</b>\n\n"
        f"🆔 شناسه: <code>{callback.from_user.id}</code>\n"
        f"📦 پلن: <b>{plan_text}</b>\n"
        f"📊 استفاده امروز: <b>{usage}</b>\n"
    )

    if expire:

        text += (
            f"⏳ انقضای VIP: <b>{expire}</b>\n"
        )

    await callback.message.edit_text(
        text,
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
# HELP
# =========================================================

@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "📚 <b>راهنمای SaaS</b>\n\n"
        "1️⃣ وارد بخش ابزارها شو.\n"
        "2️⃣ دسته موردنظر را انتخاب کن.\n"
        "3️⃣ ابزار را انتخاب کن.\n"
        "4️⃣ اطلاعات موردنظر را ارسال کن.\n"
        "5️⃣ نتیجه را دریافت کن.\n\n"
        "⭐ برای امکانات بیشتر می‌توانی VIP تهیه کنی.",
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
# TOOL STARTERS
# =========================================================

async def start_tool(
    callback: CallbackQuery,
    state: FSMContext,
    tool_name: str,
    state_obj: State,
    description: str
):

    allowed, result = check_access(
        callback.from_user.id
    )

    if not allowed:

        await callback.answer(
            "⚠️ سهمیه استفاده شما تمام شده.",
            show_alert=True
        )

        return

    await state.set_state(
        state_obj
    )

    await callback.message.edit_text(
        f"🛠 <b>{tool_name}</b>\n\n"
        f"{description}\n\n"
        "📩 اطلاعاتت را در یک پیام بفرست.\n\n"
        "برای لغو: /cancel"
    )

    await callback.answer()


@dp.callback_query(F.data == "tool_caption")
async def tool_caption(callback: CallbackQuery, state: FSMContext):

    await start_tool(
        callback,
        state,
        "✍️ ساخت کپشن",
        ToolState.waiting_caption,
        "موضوع یا متن پستت را بفرست تا چند مدل کپشن مناسب برایت آماده کنم"
