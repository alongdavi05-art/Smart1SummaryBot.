"""
Smart1SummaryBot
A Telegram bot that summarizes text using a free, local, offline summarizer.

Commands:
    /start           - welcome message
    /help            - usage instructions
    /setlength <n>   - set how many sentences the summary should contain (default 3)
    /algorithm <name> - choose summarization algorithm: lexrank | textrank | lsa

Usage:
    - Send or forward any block of text -> bot replies with a summary
    - Send a .txt file -> bot summarizes the file contents
"""

import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from summarizer import summarize_text, word_count, ensure_nltk_data, ALGORITHMS

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("Smart1SummaryBot")

MIN_WORDS = 25
DEFAULT_SENTENCE_COUNT = 3
DEFAULT_ALGORITHM = "lexrank"


def get_settings(context: ContextTypes.DEFAULT_TYPE) -> dict:
    context.user_data.setdefault("sentence_count", DEFAULT_SENTENCE_COUNT)
    context.user_data.setdefault("algorithm", DEFAULT_ALGORITHM)
    return context.user_data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Hi! I'm *Smart1SummaryBot*.\n\n"
        "Send me any long text, forward me a message, or upload a `.txt` file "
        "and I'll summarize it for you — free, offline, no API key needed.\n\n"
        "Use /help to see all commands.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = get_settings(context)
    await update.message.reply_text(
        "*How to use me:*\n"
        "• Just send text (min ~25 words) and I'll summarize it\n"
        "• Upload a `.txt` file and I'll summarize its contents\n\n"
        "*Commands:*\n"
        "/setlength `<n>` — number of sentences in summary (current: "
        f"{settings['sentence_count']})\n"
        "/algorithm `<name>` — lexrank | textrank | lsa (current: "
        f"{settings['algorithm']})\n"
        "/help — show this message",
        parse_mode=ParseMode.MARKDOWN,
    )


async def set_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = get_settings(context)
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /setlength <number>  e.g. /setlength 5")
        return
    n = max(1, min(int(context.args[0]), 20))
    settings["sentence_count"] = n
    await update.message.reply_text(f"✅ Summary length set to {n} sentence(s).")


async def set_algorithm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = get_settings(context)
    if not context.args or context.args[0].lower() not in ALGORITHMS:
        await update.message.reply_text(
            "Usage: /algorithm <lexrank|textrank|lsa>\n"
            "e.g. /algorithm textrank"
        )
        return
    algo = context.args[0].lower()
    settings["algorithm"] = algo
    await update.message.reply_text(f"✅ Algorithm set to *{algo}*.", parse_mode=ParseMode.MARKDOWN)


async def _reply_with_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    settings = get_settings(context)
    wc_before = word_count(text)

    if wc_before < MIN_WORDS:
        await update.message.reply_text(
            f"That's only {wc_before} words — send at least {MIN_WORDS} words so I have "
            "enough content to summarize."
        )
        return

    await update.message.chat.send_action("typing")

    summary = summarize_text(
        text,
        sentence_count=settings["sentence_count"],
        algorithm=settings["algorithm"],
    )
    wc_after = word_count(summary)
    reduction = round(100 * (1 - wc_after / wc_before)) if wc_before else 0

    await update.message.reply_text(
        f"📝 *Summary* ({wc_before} → {wc_after} words, -{reduction}%):\n\n{summary}",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_with_summary(update, context, update.message.text)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc = update.message.document
    if not doc.file_name.lower().endswith(".txt"):
        await update.message.reply_text("I can only read plain `.txt` files right now.")
        return

    file = await doc.get_file()
    file_bytes = await file.download_as_bytearray()
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1", errors="ignore")

    await _reply_with_summary(update, context, text)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update %s caused error %s", update, context.error)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Add it to your .env file (local) "
            "or Railway environment variables (production)."
        )

    ensure_nltk_data()

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setlength", set_length))
    application.add_handler(CommandHandler("algorithm", set_algorithm))
    application.add_handler(MessageHandler(filters.Document.TXT, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    logger.info("Smart1SummaryBot is starting (polling mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
