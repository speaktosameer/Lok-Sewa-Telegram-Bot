import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
import os

from supabase_client import supabase_upsert
from mcq_handler import get_random_mcq, format_mcq

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    supabase_upsert("users", {
        "telegram_id": user.id,
        "full_name": user.full_name,
        "username": user.username
    })
    await update.message.reply_text(
        f"👋 Hello {user.first_name}, welcome to the Lok Sewa Preparation Bot!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /quiz to get a random MCQ.")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mcq = get_random_mcq()
    if mcq:
        question_text, reply_markup = format_mcq(mcq)
        await update.message.reply_text(question_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text("No MCQs found in the database.")

# --- Main entry ---

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("quiz", quiz))

    print("🤖 Bot is running...")
    await app.run_polling()

# Entry point
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
