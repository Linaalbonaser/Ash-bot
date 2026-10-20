
import logging

from aiogram import Router, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery

from config import (
    SOCIALS,
    TRACKING_WINDOW_SECONDS,
    TRACKING_MIN_CLICKS,
    TRACKING_MIN_PLATFORMS,
)
from database import Database
from soundtrack import send_soundtrack_to_user

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("track:"))
async def track_social_click(callback: CallbackQuery, db: Database):
    platform = callback.data.split(":", 1)[1]
    social = SOCIALS.get(platform)

    if not social or not social.get("url"):
        await callback.answer(
            "Link is not configured.",
            show_alert=True,
        )
        return

    await callback.answer("Link ready")

    user_id = callback.from_user.id

    try:
        await db.register_user(callback.from_user)

        clicks, platforms = await db.record_interaction(
            user_id,
            platform,
            window_seconds=TRACKING_WINDOW_SECONDS,
        )

        builder = InlineKeyboardBuilder()
        builder.button(
            text=f"Open {social['label_en']}",
            url=social["url"],
        )

        await callback.message.answer(
            f"🔗 {social['label_en']}",
            reply_markup=builder.as_markup(),
        )

        if (
            clicks < TRACKING_MIN_CLICKS
            or platforms < TRACKING_MIN_PLATFORMS
        ):
            return

        # Existing admin alerts do not block automatic delivery.
        if await db.has_received_soundtrack(user_id):
            return

        success = await send_soundtrack_to_user(
            callback.bot,
            db,
            user_id,
        )

        if not success:
            logger.warning(
                "Soundtrack was not delivered to user_id=%s; "
                "another qualifying click can retry.",
                user_id,
            )
            return

        await db.mark_soundtrack_sent(user_id)
        logger.info(
            "Automatic soundtrack delivered to user_id=%s",
            user_id,
        )

    except Exception:
        logger.exception(
            "Tracking handler failed for user_id=%s",
            user_id,
        )
