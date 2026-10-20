# Personal Social Hub

A bilingual Persian/English Telegram profile hub built with Python and aiogram 3. The Telegram channel is featured first.

## Features

- Main Telegram channel featured at the top
- Instagram, X, Lichess, GitHub, and Pinterest profile links
- `/start`, `/socials`, `/channel`, `/about`, and `/help`
- Environment-based settings and token protection
- Missing/blank social URLs are not shown as buttons

## Windows setup

1. Install Python 3.11 or newer from https://www.python.org/downloads/
2. During installation, enable **Add Python to PATH**.
3. Create a bot with Telegram's official `@BotFather`:
   - Open Telegram and search for `@BotFather`.
   - Send `/newbot` and follow the prompts.
   - Copy the token privately. Never share it or commit it to GitHub.
4. Open PowerShell in this project folder.
5. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run this in the same terminal:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

6. Install dependencies:

   ```powershell
   py -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. Copy the example environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

8. Open `.env` in Notepad and replace `PASTE_YOUR_BOT_TOKEN_HERE` with the token from BotFather. Confirm your social links and profile text.
9. Start the bot:

   ```powershell
   py bot.py
   ```

10. Open your bot in Telegram and send `/start`. Keep the terminal running while testing.

## Commands

- `/start` — home screen
- `/socials` — social profiles
- `/channel` — featured Telegram channel
- `/about` — profile description
- `/help` — command guide

## Publish safely to GitHub

Never upload `.env`. The `.gitignore` file excludes it. You may upload `.env.example`, which contains a placeholder token only.

## Notes

- This version uses Telegram long polling. Your computer must be on and connected to the internet while the bot is running.
- The bot cannot force people to join a channel. The channel button opens the channel link.
- The Pinterest URL is the supplied short link; verify it opens the intended profile or destination.
- The bot's UI is limited to Telegram messages and buttons; it is not a custom web page.
