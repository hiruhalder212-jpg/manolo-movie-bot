import os, sqlite3, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
DB_PATH = os.environ.get("DB_PATH", "files.db")
logging.basicConfig(level=logging.INFO)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        file_id TEXT NOT NULL, file_type TEXT NOT NULL, added_by INTEGER NOT NULL)""")
    return conn

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎬 Movie Library", callback_data="movie_info")],
                [InlineKeyboardButton("🔎 Search Files", callback_data="search_info")],
                [InlineKeyboardButton("ℹ️ Help", callback_data="help")]]
    await update.effective_message.reply_text(
        "🎬 Welcome to Manolo Movie Bot!\nUse /search words to find files.\n"
        "Owner: /add Title, then send the file. Only share files you have permission to distribute.",
        reply_markup=InlineKeyboardMarkup(keyboard))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Commands:\n/start - menu\n/search words - search catalogue\n"
        "/add Title - owner adds a file, then sends it\n/cancel - cancel upload")

async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if OWNER_ID and update.effective_user.id != OWNER_ID:
        await update.effective_message.reply_text("Only the bot owner can add files."); return
    title = " ".join(context.args).strip()
    if not title:
        await update.effective_message.reply_text("Use: /add Movie title"); return
    context.user_data["pending_title"] = title
    await update.effective_message.reply_text(f"Now send the file for: {title}\n/cancel to stop.")

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("pending_title", None)
    await update.effective_message.reply_text("Cancelled.")

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    title = context.user_data.get("pending_title")
    if not title: return
    if OWNER_ID and update.effective_user.id != OWNER_ID:
        await msg.reply_text("Only the bot owner can add files."); return
    file_id, kind, fallback = None, "document", "file"
    if msg.document:
        file_id, kind, fallback = msg.document.file_id, "document", msg.document.file_name or "document"
    elif msg.video:
        file_id, kind, fallback = msg.video.file_id, "video", msg.video.file_name or "video"
    elif msg.photo:
        file_id, kind, fallback = msg.photo[-1].file_id, "photo", "photo"
    elif msg.audio:
        file_id, kind, fallback = msg.audio.file_id, "audio", msg.audio.file_name or "audio"
    elif msg.voice:
        file_id, kind, fallback = msg.voice.file_id, "voice", "voice"
    if not file_id: return
    conn = db()
    conn.execute("INSERT INTO files(name,file_id,file_type,added_by) VALUES(?,?,?,?)",
                 (title or fallback, file_id, kind, update.effective_user.id))
    conn.commit(); conn.close()
    context.user_data.pop("pending_title", None)
    await msg.reply_text(f"✅ Saved: {title}\nSearch with /search {title}")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        await update.effective_message.reply_text("Use: /search movie name"); return
    conn = db()
    rows = conn.execute("SELECT id,name,file_type FROM files WHERE name LIKE ? ORDER BY name LIMIT 10",
                        (f"%{query}%",)).fetchall()
    conn.close()
    if not rows:
        await update.effective_message.reply_text("No matches found in the catalogue."); return
    for item_id, name, kind in rows:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get file", callback_data=f"get:{item_id}")]])
        await update.effective_message.reply_text(f"📁 {name} ({kind})", reply_markup=markup)

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if q.data == "movie_info": await q.message.reply_text("Search titles with /search movie name.")
    elif q.data == "search_info": await q.message.reply_text("Use /search followed by a title or filename.")
    elif q.data == "help": await help_cmd(update, context)
    elif q.data.startswith("get:"):
        conn = db()
        row = conn.execute("SELECT name,file_id,file_type FROM files WHERE id=?",
                           (int(q.data.split(":")[1]),)).fetchone()
        conn.close()
        if not row: await q.message.reply_text("File not found."); return
        name, fid, kind = row
        if kind == "photo": await context.bot.send_photo(q.message.chat_id, fid, caption=name)
        elif kind == "video": await context.bot.send_video(q.message.chat_id, fid, caption=name)
        elif kind == "audio": await context.bot.send_audio(q.message.chat_id, fid, caption=name)
        elif kind == "voice": await context.bot.send_voice(q.message.chat_id, fid, caption=name)
        else: await context.bot.send_document(q.message.chat_id, fid, caption=name)

def main():
    if not TOKEN: raise RuntimeError("BOT_TOKEN environment variable is missing")
    db().close()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO | filters.PHOTO | filters.AUDIO | filters.VOICE, receive_file))
    app.run_polling()

if __name__ == "__main__": main()
