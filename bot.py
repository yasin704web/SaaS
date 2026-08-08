from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from config import TOKEN, CARD_NUMBER, ADMIN_ID
from vip import activate_vip


# ================= START =================
def start(update: Update, context: CallbackContext):
    keyboard = [
        ["🛠 ابزارها"],
        ["👑 خرید VIP"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "به Vista AI Tools خوش اومدی 👋",
        reply_markup=reply_markup
    )


# ================= BUY VIP =================
def buy_vip(update: Update, context: CallbackContext):
    text = f"""
👑 اشتراک VIP یک ماهه

💰 قیمت: (اینجا قیمت رو بنویس)

💳 شماره کارت:
{CARD_NUMBER}

📸 بعد از پرداخت، عکس رسید رو ارسال کن.
"""
    update.message.reply_text(text)


# ================= HANDLE TEXT =================
def handle_text(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "👑 خرید VIP":
        buy_vip(update, context)
    else:
        update.message.reply_text("دستور نامعتبر")


# ================= HANDLE RECEIPT =================
def handle_receipt(update: Update, context: CallbackContext):
    if update.message.photo:
        user = update.message.from_user
        photo = update.message.photo[-1].file_id

        caption = f"""
💳 درخواست VIP جدید

👤 یوزرنیم:
@{user.username}

🆔:
{user.id}
"""

        # ارسال به ادمین
        context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo,
            caption=caption
        )

        update.message.reply_text(
            "✅ رسید ارسال شد. بعد از بررسی VIP فعال می‌شود."
        )


# ================= ADMIN VIP COMMAND =================
def vip_command(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])

        success, expire = activate_vip(user_id)

        if success:
            update.message.reply_text("✅ VIP فعال شد")

            context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 VIP شما فعال شد تا:\n{expire}"
            )
        else:
            update.message.reply_text("❌ کاربر پیدا نشد")

    except:
        update.message.reply_text("❌ فرمت اشتباه. مثال:\n/vip 123456789")


# ================= MAIN =================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("vip", vip_command))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.photo, handle_receipt))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
