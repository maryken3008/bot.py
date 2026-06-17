import os
import asyncio
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, ContextTypes

# ============================================================
# CONFIG — edit these
# ============================================================
CHANNEL_LINK = "https://t.me/nun0moraised4N76nm"
SUPPORT_HANDLE = "@NUNO_MORAlS"

GITHUB_BASE = "https://raw.githubusercontent.com/<USERNAME>/<REPO>/main/"
IMAGE_FILES = [
    "image1.jpg",
    "image2.jpg",
    "image3.jpg",
    "image4.jpg",
]
IMAGE_URLS = [GITHUB_BASE + name for name in IMAGE_FILES]

REPEAT_SECONDS = 6 * 60 * 60  # 6 hours

# ============================================================
# Logging
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("bot")

# ============================================================
# Dummy HTTP server (Railway/Render need an open port)
# ============================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot esta a correr.")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def log_message(self, format, *args):
        return

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    log.info(f"Health server on port {port}")
    server.serve_forever()

# ============================================================
# Messages
# ============================================================
WELCOME_MSG = (
    "*Bem-vindo ao Nuno Morais Apostas – o seu companheiro de confiança "
    "para dicas de apostas inteligentes e responsáveis.*\n\n"
    "O nosso foco são sugestões desportivas claras e com alta probabilidade "
    "de acerto para o ajudar a jogar com mais confiança.\n\n"
    "🔞 Apenas para maiores de 18 anos.\n\n"
    "O que vai encontrar:\n"
    "· Palpites diários bem pesquisados\n"
    "· Odds sólidas e com bom valor\n"
    "· Atualizações ao vivo à medida que a ação acontece\n"
    "· Dicas simples de gestão de banca e estratégias de apostas\n"
    "· Conteúdo extra exclusivo para os nossos subscritores"
)

LINK_MSG = (
    "👇 Clique aqui para entrar no nosso canal de Telegram:\n"
    f"{CHANNEL_LINK}"
)

HELP_MSG = (
    "Precisa de ajuda?\n\n"
    "Entre em contacto:\n"
    f"📩 {SUPPORT_HANDLE}\n\n"
    "Responderei o mais breve possível."
)

# ============================================================
# The sequence — fires 1 sec after /start and every 6h after
# ============================================================
async def send_sequence(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    bot = context.bot
    log.info(f"Sending sequence to {chat_id}")
    try:
        # 1. Welcome
        await bot.send_message(chat_id, WELCOME_MSG, parse_mode="Markdown")
        await asyncio.sleep(2)

        # 2. Channel link
        await bot.send_message(chat_id, LINK_MSG)
        await asyncio.sleep(2)

        # 3. Four proof images
        try:
            media = [InputMediaPhoto(media=url) for url in IMAGE_URLS]
            await bot.send_media_group(chat_id, media)
        except Exception as e:
            log.error(f"Image send failed: {e}")
            await bot.send_message(
                chat_id,
                "⚠️ *Aviso:* As imagens falharam a carregar. "
                "Verifique os links no GitHub.",
                parse_mode="Markdown",
            )

        # 4. Channel link again
        await bot.send_message(chat_id, LINK_MSG)
        await asyncio.sleep(5)

        # 5. Help message
        await bot.send_message(chat_id, HELP_MSG)
        log.info(f"Sequence complete for {chat_id}")
    except Exception as e:
        log.error(f"send_sequence failed for {chat_id}: {e}")

# ============================================================
# /start handler
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    log.info(f"/start from {chat_id}")

    if context.job_queue is None:
        await context.bot.send_message(
            chat_id,
            "⚠️ JobQueue not installed.",
        )
        return

    # Cancel any previous schedule for this user
    for j in context.job_queue.get_jobs_by_name(str(chat_id)):
        j.schedule_removal()

    # Run sequence in 1 second + repeat every 6h
    # (must be `first=1` not `first=0`; PTB treats 0 as "use interval")
    context.job_queue.run_repeating(
        send_sequence,
        interval=REPEAT_SECONDS,
        first=1,
        chat_id=chat_id,
        name=str(chat_id),
    )

# ============================================================
# Main
# ============================================================
def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        log.critical("BOT_TOKEN env var missing!")
        return

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    log.info("O Bot está a correr...")
    app.run_polling()

if __name__ == "__main__":
    main()
