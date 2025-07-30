import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from mcq_handler import get_random_mcq, format_mcq
from supabase_client import supabase

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    supabase.table("users").upsert({
        "telegram_id": user.id,
        "full_name": user.full_name,
        "username": user.username
    }).execute()
    
    await update.message.reply_text(
        f"👋 Hello {user.first_name}, welcome to Lok Sewa Preparation Bot 🇳🇵!\n\n"
        "Type /quiz to start practicing MCQs.\nUse /help for commands."
    )

# --- Quiz command
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = "GK"  # default for now
    mcq = get_random_mcq(subject)
    if not mcq:
        await update.message.reply_text("❌ No MCQ found.")
        return
    
    keyboard = [
        [InlineKeyboardButton("A", callback_data=f"A|{mcq['id']}"),
         InlineKeyboardButton("B", callback_data=f"B|{mcq['id']}")],
        [InlineKeyboardButton("C", callback_data=f"C|{mcq['id']}"),
         InlineKeyboardButton("D", callback_data=f"D|{mcq['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_markdown(format_mcq(mcq), reply_markup=reply_markup)

# --- Callback for MCQ Answer
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    answer, mcq_id = query.data.split("|")
    mcq = supabase.table("mcqs").select("*").eq("id", mcq_id).single().execute().data

    correct = mcq["correct_option"]
    explanation = mcq.get("explanation", "No explanation provided.")
    
    if answer == correct:
        supabase.table("users").update({"score": supabase.rpc("increment_score", {"id": query.from_user.id, "points": 1})}).eq("telegram_id", query.from_user.id).execute()
        await query.edit_message_text(f"✅ Correct!\n\n🧠 {explanation}")
    else:
        await query.edit_message_text(f"❌ Wrong! Correct Answer: {correct}\n\n🧠 {explanation}")

# --- Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Start bot\n"
        "/quiz - Get a random MCQ\n"
        "/help - List of commands"
    )

# --- Main App
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_answer))
    app.run_polling()

if __name__ == "__main__":
    main()
