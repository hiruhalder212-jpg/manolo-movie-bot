# Manolo Movie Bot
Upload these files to the root of your GitHub repository.

Render Background Worker:
- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Environment variables: `BOT_TOKEN` (keep secret), `OWNER_ID` (your numeric Telegram user ID; recommended).

Commands:
- `/start`
- `/help`
- `/add Movie title` then send an authorized file
- `/search words`
- `/cancel`

Only share files you own or are authorized to distribute. Free hosting is not guaranteed to run 24/7. SQLite data can be lost on ephemeral hosting/redeploys; use persistent storage for a durable catalogue.
