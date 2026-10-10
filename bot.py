import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
DB_PATH = os.environ.get("DB_PATH", "movies.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_name TEXT,
            added_by INTEGER
        )
    """)
    return conn

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔎 Search my movie library", callback_data="search_help")],
        [InlineKeyboardButton("➕ Add a movie/file", callback_data="add_help")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    await update.message.reply_text(
        "🎬 Welcome to Manolo Movie Bot!\\n\\n"
        "Search files uploaded by the bot owner, or add your own videos/files. "
        "Only share files you own or are authorized to distribute.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\\n"
        "/start - open menu\\n"
        "/addmovie Movie title - then send a video/document to save it\\n"
        "/search words - search saved titles\\n"
        "/cancel - cancel adding a file\\n\\n"
        "Owner-only: set OWNER_ID as an environment variable. "
        "Files must be ones you own or have permission to share."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("pending_title", None)
    await update.message.reply_text("Cancelled.")

async def addmovie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = os.environ.get("OWNER_ID")
    if owner_id and str(update.effective_user.id) != owner_id:
        await update.message.reply_text("Only the bot owner can add files.")
        return
    title = " ".join(context.args).strip()
    if not title:
        await update.message.reply_text("Use: /addmovie Movie title")
        return
    context.user_data["pending_title"] = title
    await update.message.reply_text(
        f"Now send the video or document for: {title}\\n"
        "Send /cancel to stop."
    )

async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = context.user_data.get("pending_title")
    if not title:
        return
    msg = update.effective_message
    file_id = None
    file_name = None
    if msg.video:
        file_id = msg.video.file_id
        file_name = msg.video.file_name or f"{title}.mp4"
    elif msg.document:
        file_id = msg.document.file_id
        file_name = msg.document.file_name or title
    elif msg.audio:
        file_id = msg.audio.file_id
        file_name = msg.audio.file_name or title
    if not file_id:
        await msg.reply_text("Please send a video, document, or audio file.")
        return
    conn = db()
    conn.execute(
        "INSERT INTO movies (title, file_id, file_name, added_by) VALUES (?, ?, ?, ?)",
        (title, file_id, file_name, update.effective_user.id),
    )
    conn.commit()
    conn.close()
    context.user_data.pop("pending_title", None)
    await msg.reply_text(f"✅ Saved: {title}\\nSearch it with /search {title}")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        await update.message.reply_text("Use: /search movie title")
        return
    conn = db()
    rows = conn.execute(
        "SELECT id, title, file_id, file_name FROM movies WHERE title LIKE ? ORDER BY title LIMIT 10",
        (f"%{query}%",),
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No matching files found in this bot's library.")
        return
    for movie_id, title, file_id, file_name in rows:
        keyboard = [[InlineKeyboardButton("📥 Send file", callback_data=f"get:{movie_id}")]]
        await update.message.reply_text(
            f"🎬 {title}" + (f"\\n📄 {file_name}" if file_name else ""),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "search_help":
        await query.message.reply_text("Search using: /search movie title")
    elif query.data == "add_help":
        await query.message.reply_text("Use /addmovie Movie title, then send the video/document.")
    elif query.data == "help":
        await query.message.reply_text("Use /help to see commands.")
    elif query.data.startswith("get:"):
        movie_id = int(query.data.split(":", 1)[1])
        conn = db()
        row = conn.execute(
            "SELECT title, file_id, file_name FROM movies WHERE id = ?", (movie_id,)
        ).fetchone()
        conn.close()
        if not row:
            await query.message.reply_text("File not found.")
            return
        title, file_id, file_name = row
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=file_id,
            caption=f"🎬 {title}",
        )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Send /help.")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("addmovie", addmovie))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL | filters.AUDIO, save_file))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.run_polling()

if __name__ == "__main__":
    main()
