import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()
PROFILE_NAME = os.getenv("PROFILE_NAME", "Lina").strip()
DATABASE_PATH = os.getenv("DATABASE_PATH", "ash.db").strip()

if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
    raise RuntimeError(
        "BOT_TOKEN is missing. Set it in your .env file."
    )

try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except (TypeError, ValueError):
    raise RuntimeError(
        "ADMIN_ID must be your numeric Telegram user ID."
    )

ABOUT_FA = (
    "من Ash هستم؛ درگاه شخصی لینا برای دسترسی به شبکه‌های اجتماعی، "
    "پروژه‌ها و مسیرهای ارتباطی او.\n\n"
    "یک رابط ساده، منظم و همیشه آماده."
)

ABOUT_EN = (
    "I'm Ash, Lina's personal hub for social links, projects, "
    "and contact points.\n\n"
    "A clean interface. No unnecessary noise."
)

SOCIALS = {
    "channel": {
        "label_fa": "کانال تلگرام",
        "label_en": "Telegram Channel",
        "url": "https://t.me/NeutrinoNetwork",
    },
    "instagram": {
        "label_fa": "اینستاگرام",
        "label_en": "Instagram",
        "url": "https://www.instagram.com/linaalbonaser/",
    },
    "x": {
        "label_fa": "ایکس",
        "label_en": "X",
        "url": "https://x.com/linaalbonaser",
    },
    "lichess": {
        "label_fa": "لیچس",
        "label_en": "Lichess",
        "url": "https://lichess.org/@/linaalbonaser",
    },
    "github": {
        "label_fa": "گیت‌هاب",
        "label_en": "GitHub",
        "url": "https://github.com/Linaalbonaser",
    },
    "pinterest": {
        "label_fa": "پینترست",
        "label_en": "Pinterest",
        "url": "https://www.pinterest.com/",
    },
}

# Alert when a user interacts with enough distinct social platforms.
TRACKING_WINDOW_SECONDS = 5 * 60
TRACKING_MIN_CLICKS = 4
TRACKING_MIN_PLATFORMS = 3
