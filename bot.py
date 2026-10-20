
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import (
    ADMIN_ID,
    ABOUT_EN,
    ABOUT_FA,
    BOT_TOKEN,
    PROFILE_NAME,
    SOCIALS,
    DATABASE_PATH,
)
from database import Database
from tracking import router as tracking_router
from soundtrack import router as soundtrack_router
from admin import router as admin_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ash")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database(DATABASE_PATH)

menu_messages: dict[int, int] = {}


def main_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if language == "fa":
        builder.button(text="👤 دربارهٔ من", callback_data="page:about:fa")
        builder.button(text="🌐 شبکه‌های اجتماعی", callback_data="page:socials:fa")
        builder.button(text="💻 پروژه‌ها", callback_data="page:projects:fa")
        builder.button(text="🇬🇧 English", callback_data="page:home:en")
    else:
        builder.button(text="👤 About", callback_data="page:about:en")
        builder.button(text="🌐 Social links", callback_data="page:socials:en")
        builder.button(text="💻 Projects", callback_data="page:projects:en")
        builder.button(text="🇮🇷 فارسی", callback_data="page:home:fa")

    builder.adjust(2, 1, 1)
    return builder.as_markup()


def socials_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for key, social in SOCIALS.items():
        if not social.get("url"):
            continue

        label = (
            social["label_fa"]
            if language == "fa"
            else social["label_en"]
        )
        builder.button(
            text=label,
            callback_data=f"track:{key}",
        )

    back_label = "⬅️ بازگشت" if language == "fa" else "⬅️ Back"
    builder.button(
        text=back_label,
        callback_data=f"page:home:{language}",
    )
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def back_keyboard(language: str) -> InlineKeyboardMarkup:
    label = "⬅️ بازگشت" if language == "fa" else "⬅️ Back"
    builder = InlineKeyboardBuilder()
    builder.button(text=label, callback_data=f"page:home:{language}")
    return builder.as_markup()


def page_content(
    page: str,
    language: str,
) -> tuple[str, InlineKeyboardMarkup]:
    if page == "home":
        if language == "fa":
            text = (
                "ASH // PERSONAL SOCIAL HUB\n\n"
                f"سلام، من Ash هستم.\n"
                f"درگاه شخصی {PROFILE_NAME}.\n\n"
                "یک نقطهٔ دسترسی برای شبکه‌ها، پروژه‌ها و ارتباطات."
            )
        else:
            text = (
                "ASH // PERSONAL SOCIAL HUB\n\n"
                "Hello. I'm Ash.\n"
                f"{PROFILE_NAME}'s personal access point.\n\n"
                "Social links, projects, and contact points."
            )
        return text, main_keyboard(language)

    if page == "about":
        return (
            ABOUT_FA if language == "fa" else ABOUT_EN,
            back_keyboard(language),
        )

    if page == "socials":
        text = (
            "شبکهٔ موردنظر را انتخاب کن."
            if language == "fa"
            else "Select a social destination."
        )
        return text, socials_keyboard(language)

    if page == "projects":
        text = (
            "پروژه‌ها به‌زودی اضافه می‌شوند."
            if language == "fa"
            else "Projects will be listed here soon."
        )
        return text, back_keyboard(language)

    return page_content("home", language)


async def register_and_notify(user):
    is_new = await db.register_user(user)

    if not is_new or user.id == ADMIN_ID:
        return

    name = " ".join(
        part for part in [user.first_name, user.last_name] if part
    ) or "Unknown"
    username = f"@{user.username}" if user.username else "No username"

    try:
        await bot.send_message(
            ADMIN_ID,
            "ASH // NEW USER\n\n"
            f"Name: {name}\n"
            f"Username: {username}\n"
            f"Telegram ID: {user.id}\n"
            "First interaction: recorded.",
        )
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        logger.info("Could not notify admin: %s", exc)


@dp.message(CommandStart())
async def start_handler(message: Message):
    await register_and_notify(message.from_user)

    language = (
        "fa"
        if message.from_user.language_code == "fa"
        else "en"
    )

    text, keyboard = page_content("home", language)
    sent = await message.answer(text, reply_markup=keyboard)
    menu_messages[message.chat.id] = sent.message_id

    try:
        await message.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


@dp.message(Command("help"))
async def help_handler(message: Message):
    await register_and_notify(message.from_user)

    await message.answer(
        "ASH // HELP\n\n"
        "/start — open the menu\n"
        "/help — show this help\n"
        "/admin — admin console (authorized account only)"
    )


@dp.callback_query(F.data.startswith("page:"))
async def page_handler(callback: CallbackQuery):
    await callback.answer()

    try:
        _, page, language = callback.data.split(":", 2)
    except ValueError:
        return

    text, keyboard = page_content(page, language)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
        )
        menu_messages[callback.message.chat.id] = (
            callback.message.message_id
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            logger.warning("Page update failed: %s", exc)


async def main():
    await db.initialize()

    dp.include_router(tracking_router)
    dp.include_router(soundtrack_router)
    dp.include_router(admin_router)

    logger.info("Tracking router loaded.")
    logger.info("Soundtrack router loaded.")
    logger.info("Admin router loaded.")
    logger.info("Ash is starting.")

    await dp.start_polling(bot, db=db)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Ash stopped.")
    except Exception:
        logger.exception("Ash stopped due to an unexpected error.")
        raise
