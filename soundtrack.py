
import logging
from urllib.parse import urlparse

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramAPIError

from config import ADMIN_ID
from database import Database

router = Router()
logger = logging.getLogger(__name__)

INTRO = "Interesting..."
OUTRO = "ازم خوشت میاد یا فضولی؟ فرقی نداره.\n\nLet's dance."


class SoundtrackState(StatesGroup):
    waiting_for_soundtrack = State()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def is_valid_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        return (
            parsed.scheme in ("https", "http")
            and bool(parsed.netloc)
        )
    except ValueError:
        return False


@router.callback_query(F.data.startswith("music:add:"))
async def request_soundtrack(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    await state.set_state(SoundtrackState.waiting_for_soundtrack)
    await callback.answer()
    await callback.message.answer(
        "Send an audio file, an audio document, or an HTTP(S) link.\n"
        "Use /cancel to abort."
    )


@router.message(Command("cancel"), SoundtrackState.waiting_for_soundtrack)
async def cancel_soundtrack(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    await message.answer("Cancelled.")


@router.message(SoundtrackState.waiting_for_soundtrack)
async def receive_soundtrack(
    message: Message,
    state: FSMContext,
    db: Database,
):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    if message.audio:
        await db.save_soundtrack(
            kind="audio",
            file_id=message.audio.file_id,
            title=(
                message.audio.title
                or message.audio.file_name
                or "Ash soundtrack"
            ),
        )

    elif message.document:
        document = message.document
        filename = (document.file_name or "").lower()
        mime = (document.mime_type or "").lower()

        if not (
            mime.startswith("audio/")
            or filename.endswith(
                (".mp3", ".m4a", ".ogg", ".wav", ".flac")
            )
        ):
            await message.answer("Send a valid audio file.")
            return

        await db.save_soundtrack(
            kind="document",
            file_id=document.file_id,
            title=document.file_name or "Ash soundtrack",
        )

    elif message.text and is_valid_url(message.text):
        await db.save_soundtrack(
            kind="url",
            title="Ash soundtrack link",
            url=message.text.strip(),
        )

    else:
        await message.answer(
            "Send an audio file, audio document, or valid HTTP(S) link."
        )
        return

    await state.clear()
    await message.answer("ASH // SOUNDTRACK SAVED")


async def send_soundtrack_to_user(
    bot,
    db: Database,
    user_id: int,
) -> bool:
    try:
        soundtrack = await db.get_soundtrack()

        if not soundtrack:
            logger.error("No soundtrack is saved.")
            return False

        kind = soundtrack["kind"]
        file_id = soundtrack["file_id"]
        url = soundtrack["url"]

        if kind in ("audio", "document") and not file_id:
            logger.error("Soundtrack file_id is missing.")
            return False

        if kind == "url" and not url:
            logger.error("Soundtrack URL is missing.")
            return False

        if kind not in ("audio", "document", "url"):
            logger.error("Invalid soundtrack kind: %s", kind)
            return False

        await bot.send_message(user_id, INTRO)

        if kind == "audio":
            await bot.send_audio(user_id, audio=file_id)
        elif kind == "document":
            await bot.send_document(user_id, document=file_id)
        else:
            await bot.send_message(user_id, url)

        await bot.send_message(user_id, OUTRO)
        return True

    except TelegramAPIError:
        logger.exception(
            "Telegram rejected soundtrack delivery to user_id=%s",
            user_id,
        )
        return False
    except Exception:
        logger.exception(
            "Unexpected soundtrack error for user_id=%s",
            user_id,
        )
        return False


@router.callback_query(F.data.startswith("music:resend:"))
async def resend_soundtrack(
    callback: CallbackQuery,
    db: Database,
):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied.", show_alert=True)
        return

    await callback.answer("Broadcast started.")

    users = await db.get_users()
    sent = 0
    failed = 0

    for user in users:
        user_id = user["user_id"]
        success = await send_soundtrack_to_user(
            callback.bot, db, user_id
        )

        if success:
            sent += 1
            try:
                await db.mark_soundtrack_sent(user_id)
            except Exception:
                logger.exception(
                    "Could not save delivery status for user_id=%s",
                    user_id,
                )
        else:
            failed += 1

    await callback.message.answer(
        "ASH // BROADCAST COMPLETE\n\n"
        f"Successful: {sent}\n"
        f"Failed: {failed}"
    )
