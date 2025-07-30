import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from supabase_client import supabase_upsert
from mcq_handler import get_random_mcq, format_mcq

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# States for ConversationHandler
CHOOSE_SUBJECT = "CHOOSE_SUBJECT"

# Start command - register user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    supabase_upsert("users", {
        "telegram_id": user.id,
        "full_name": user.full_name,
        "username": user.username
    })
    await update.message.reply_text(
        f"👋 Hello {user.first_name}, welcome to *Lok Sewa Preparation Bot 🇳🇵*!\n\n"
        "Use:\n"
        "/quiz – Practice MCQs\n"
        "/help – View commands",
        parse_mode="Markdown"
    )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 *Available Commands:*\n\n"
        "/start – Register yourself\n"
        "/quiz – Start subject-wise quiz\n"
        "/help – Show this help message",
        parse_mode="Markdown"
    )

# Quiz command – ask subject
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["GK", "Computer"], ["English", "Math"]]
    await update.message.reply_text(
        "📚 Choose a subject to start your quiz:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSE_SUBJECT

# Handle subject response
async def handle_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text
    mcq = get_random_mcq(subject)
    if not mcq:
        await update.message.reply_text("❌ No MCQs found for this subject.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("A", callback_data=f"A|{mcq['id']}"),
         InlineKeyboardButton("B", callback_data=f"B|{mcq['id']}")],
        [InlineKeyboardButton("C", callback_data=f"C|{mcq['id']}"),
         InlineKeyboardButton("D", callback_data=f"D|{mcq['id']}")]
    ]
    await update.message.reply_markdown(
        format_mcq(mcq),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

# Handle MCQ answer (for now just acknowledge)
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected, _ = query.data.split("|")
    await query.edit_message_text(f"✅ You selected option: {selected}")

# Main bot entry
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Quiz conversation handler
    quiz_handler = ConversationHandler(
        entry_points=[CommandHandler("quiz", quiz)],
        states={
            CHOOSE_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subject)]
        },
        fallbacks=[]
    )
    app.add_handler(quiz_handler)

    # Inline answer handler
    app.add_handler(CallbackQueryHandler(handle_answer))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
