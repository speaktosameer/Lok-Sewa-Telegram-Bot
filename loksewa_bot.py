from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import datetime

TOKEN = "8380057958:AAG6pnd2r89pljuu6t6nE2FRuCdwrNhXWlQ"

# Sample MCQ
MCQS = [
    {
        "question": "What is the capital of Nepal?",
        "options": ["Pokhara", "Kathmandu", "Lalitpur", "Biratnagar"],
        "answer": "Kathmandu"
    }
]

def get_exam_countdown():
    exam_date = datetime.datetime(2025, 12, 1)
    today = datetime.datetime.now()
    remaining = exam_date - today
    return f"📆 Days until exam: {remaining.days} days"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 Daily MCQ", callback_data="daily_mcq")],
        [InlineKeyboardButton("📖 Syllabus", callback_data="syllabus")],
        [InlineKeyboardButton("🧠 Random Quiz", callback_data="random_quiz")],
        [InlineKeyboardButton("📆 Exam Countdown", callback_data="countdown")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Welcome to Lok Sewa Bot!\nChoose an option:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "daily_mcq" or query.data == "random_quiz":
        mcq = MCQS[0]  # In future: random.choice(MCQS)
        options = [InlineKeyboardButton(opt, callback_data=f"ans_{opt}") for opt in mcq["options"]]
        await query.edit_message_text(mcq["question"], reply_markup=InlineKeyboardMarkup.from_column(options))
        context.user_data["correct_answer"] = mcq["answer"]

    elif query.data == "countdown":
        countdown = get_exam_countdown()
        await query.edit_message_text(countdown)

    elif query.data == "syllabus":
        await query.edit_message_text("📖 Lok Sewa syllabus:\n- GK\n- IQ\n- Office Tech\n- English\n- Math")

    elif query.data.startswith("ans_"):
        selected = query.data.replace("ans_", "")
        correct = context.user_data.get("correct_answer")
        if selected == correct:
            await query.edit_message_text(f"✅ Correct! Answer: {correct}")
        else:
            await query.edit_message_text(f"❌ Wrong. Correct answer is: {correct}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()
