# Manolo Movie Bot

A Telegram bot for searching and sharing video/document files that you own or are authorized to distribute.

## Deploy on Render

1. Upload these files to your GitHub repository.
2. In Render, create a **Background Worker** from that repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Add environment variables:
   - `BOT_TOKEN`: your token from the official @BotFather (keep it secret)
   - `OWNER_ID`: your Telegram numeric user ID (optional, but recommended)
6. Deploy.

**Important:** Free hosting may sleep or be unavailable; uninterrupted 24/7 service may require a paid plan. The included SQLite database may not persist on all hosting plans/redeploys, so for a durable library use a persistent disk or managed database.

## Commands

- `/start` — menu
- `/help` — help
- `/addmovie Movie title` — then send a video/document/audio file
- `/search words` — search saved files
- `/cancel` — cancel pending upload

Only upload/share content you own or have permission to distribute. This bot does not scrape or provide unauthorized copyrighted movies.
