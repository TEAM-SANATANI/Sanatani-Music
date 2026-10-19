import asyncio
import logging
import os
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("music-bot")

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("Set the BOT_TOKEN environment variable (get it from @BotFather).")

MAX_SECONDS = 15 * 60          # skip tracks longer than 15 min
MAX_BYTES = 49 * 1024 * 1024   # Telegram bot upload limit is 50 MB


def download_audio(query: str):
    """Search YouTube (or use a URL) and download audio. Returns (folder, filepath, info)."""
    folder = tempfile.mkdtemp(prefix="musicbot_")
    target = query if query.startswith("http") else f"ytsearch1:{query}"
    opts = {
        # m4a needs no ffmpeg and Telegram plays it fine
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": f"{folder}/%(id)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_BYTES,
        "match_filter": yt_dlp.utils.match_filter_func(f"duration < {MAX_SECONDS}"),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(target, download=True)
        if info and "entries" in info:
            entries = [e for e in info["entries"] if e]
            info = entries[0] if entries else None
        if not info:
            raise ValueError("No result (maybe too long or too large).")
        path = ydl.prepare_filename(info)
    if not os.path.exists(path):
        raise ValueError("Download failed or file too large.")
    return folder, path, info


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Send me a song name or a YouTube link, or use /play <song name>."
    )


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else (update.message.text or "").strip()
    if not query:
        await update.message.reply_text("Usage: /play <song name or link>")
        return

    status = await update.message.reply_text("Searching and downloading...")
    folder = None
    try:
        folder, path, info = await asyncio.to_thread(download_audio, query)
        await update.message.reply_chat_action("upload_voice")
        with open(path, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=info.get("title"),
                performer=info.get("uploader"),
                duration=int(info.get("duration") or 0),
                read_timeout=120,
                write_timeout=120,
            )
        await status.delete()
    except Exception as e:
        log.exception("play failed")
        await status.edit_text(f"Could not get that song: {str(e)[:200]}")
    finally:
        if folder:
            shutil.rmtree(folder, ignore_errors=True)


# --- tiny HTTP server so Render's free "web service" sees an open port ---
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def run_health_server():
    port = int(os.environ["PORT"])
    HTTPServer(("0.0.0.0", port), Health).serve_forever()


def main():
    if os.environ.get("PORT"):  # set automatically on Render, not on Termux
        threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, play))
    log.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
