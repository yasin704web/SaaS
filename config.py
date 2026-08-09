import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CARD_NUMBER = os.getenv("CARD_NUMBER", "").strip()

CHANNEL_1 = os.getenv("CHANNEL_1", "").strip()
CHANNEL_2 = os.getenv("CHANNEL_2", "").strip()

CHANNEL_LINK_1 = os.getenv("CHANNEL_LINK_1", "").strip()
CHANNEL_LINK_2 = os.getenv("CHANNEL_LINK_2", "").strip()

VIP_PRICE = int(os.getenv("VIP_PRICE", "199000"))

FREE_LIMIT = int(os.getenv("FREE_LIMIT", "10"))

VIP_DAYS = 30


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN در Environment Variables تنظیم نشده است.")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID در Environment Variables تنظیم نشده است.")

if not CHANNEL_1 or not CHANNEL_2:
    raise RuntimeError("CHANNEL_1 و CHANNEL_2 باید تنظیم شوند.")
