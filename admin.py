
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID
from database import Database

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def format_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).astimezone().strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "ASH // ADMIN CONSOLE\n\n"
        "/users — registered users\n"
        "/stats — bot statistics\n"
        "/music — saved soundtrack status\n"
        "/cancel — cancel soundtrack input"
    )


@router.message(Command("users"))
async def list_users(message: Message, db: Database):
    if not is_admin(message.from_user.id):
        return

    users = await db.get_users()

    if not users:
        await message.answer("No registered users yet.")
        return

    # Telegram messages have a length limit, so send the list in chunks.
    lines = [f"Registered users: {len(users)}\n"]

    for user in users:
        name = " ".join(
            part for part in [user["first_name"], user["last_name"]] if part
        ) or "Unknown"

        username = (
            f"@{user['username']}"
            if user["username"]
            else "No username"
        )

        lines.append(
            f"Name: {name}\n"
            f"Username: {username}\n"
            f"ID: {user['user_id']}\n"
            f"First seen: {format_timestamp(user['first_seen'])}\n"
            f"Last seen: {format_timestamp(user['last_seen'])}\n"
            "--------------------"
        )

    chunk = ""

    for line in lines:
        if len(chunk) + len(line) + 2 > 3500:
            await message.answer(chunk)
            chunk = ""

        chunk += line + "\n\n"

    if chunk:
        await message.answer(chunk)


@router.message(Command("stats"))
async def show_stats(message: Message, db: Database):
    if not is_admin(message.from_user.id):
        return

    stats = await db.get_stats()

    await message.answer(
        "ASH // SYSTEM STATISTICS\n\n"
        f"Registered users: {stats['users']}\n"
        f"Recorded interactions: {stats['interactions']}\n"
        f"Activity alerts sent: {stats['alerts']}"
    )


@router.message(Command("music"))
async def music_status(message: Message, db: Database):
    if not is_admin(message.from_user.id):
        return

    soundtrack = await db.get_soundtrack()

    if not soundtrack:
        await message.answer(
            "No soundtrack saved.\n"
            "Use /admin, then send a music file or link when prompted "
            "by an activity alert's Add soundtrack button."
        )
        return

    await message.answer(
        "ASH // SOUNDTRACK STATUS\n\n"
        f"Type: {soundtrack['kind']}\n"
        f"Title: {soundtrack['title'] or 'Untitled'}\n"
        f"Updated: {format_timestamp(soundtrack['updated_at'])}"
    )
