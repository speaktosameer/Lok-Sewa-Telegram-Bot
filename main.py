import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from supabase_client import supabase_upsert
from mcq_handler import get_random_mcq, format_mcq

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        supabase_upsert("users", {
            "telegram_id": user.id,
            "full_name": user.full_name,
            "username": user.username
        })
        await update.message.reply_text(f"Welcome, {user.full_name or 'User'}! 🎉")
    except Exception as e:
        logging.error("Failed to upsert user: %s", e)
        await update.message.reply_text("There was an error registering you.")

# /help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /quiz to get a random MCQ!")

# /quiz command handler
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        mcq = get_random_mcq()
        formatted = format_mcq(mcq)
        await update.message.reply_text(formatted)
    except Exception as e:
        logging.error("Error fetching quiz: %s", e)
        await update.message.reply_text("Sorry, failed to fetch a quiz.")

# Main application function
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("quiz", quiz))

    logging.info("🤖 Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
