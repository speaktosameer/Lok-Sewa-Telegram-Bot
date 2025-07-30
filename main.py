import os
from dotenv import load_dotenv
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from supabase_client import supabase
from mcq_handler import get_random_mcq, format_mcq

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    supabase.table("users").upsert({
        "telegram_id": user.id,
        "full_name": user.full_name,
        "username": user.username
    }).execute()
    
    await update.message.reply_text(
        f"👋 Hello {user.first_name}, welcome to *Lok Sewa Preparation Bot 🇳🇵*!\n\n"
        "Use:\n/quiz – Practice MCQs\n/syllabus – Track syllabus\n/leaderboard – View top scorers",
        parse_mode="Markdown"
    )

# --- /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start – Start bot\n"
        "/quiz – Practice questions\n"
        "/syllabus – View & track topics\n"
        "/leaderboard – Top users"
    )

# --- /quiz: subject selector
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["GK", "Computer"], ["English", "Math"]]
    await update.message.reply_text(
        "📚 Choose a subject to start your quiz:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return "CHOOSE_SUBJECT"

# --- handle subject → send MCQ
async def handle_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text
    mcq = get_random_mcq(subject)
    if not mcq:
        await update.message.reply_text("❌ No MCQs found.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("A", callback_data=f"A|{mcq['id']}"),
         InlineKeyboardButton("B", callback_data=f"B|{mcq['id']}")],
        [InlineKeyboardButton("C", callback_data=f"C|{mcq['id']}"),
         InlineKeyboardButton("D", callback_data=f"D|{mcq['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_markdown(format_mcq(mcq), reply_markup=reply_markup)
    return ConversationHandler.END

# --- handle answer logic + streak + score
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    answer, mcq_id = query.data.split("|")
    mcq = supabase.table("mcqs").select("*").eq("id", mcq_id).single().execute().data
    correct = mcq["correct_option"]
    explanation = mcq.get("explanation", "No explanation provided.")

    user_id = query.from_user.id
    today = date.today()
    user_data = supabase.table("users").select("*").eq("telegram_id", user_id).single().execute().data

    # streak logic
    last_answered = user_data.get("last_answered")
    streak = user_data.get("streak", 0)
    if last_answered:
        last_date = datetime.strptime(last_answered, "%Y-%m-%d").date()
    else:
        last_date = None

    if last_date == today:
        pass
    elif last_date == today.fromordinal(today.toordinal() - 1):
        streak += 1
    else:
        streak = 1

    bonus = 1 if streak >= 5 else 0
    total_points = 1 + bonus

    if answer == correct:
        supabase.table("users").update({
            "score": user_data["score"] + total_points,
            "streak": streak,
            "last_answered": str(today)
        }).eq("telegram_id", user_id).execute()
        await query.edit_message_text(f"✅ Correct! (+{total_points} pts)\n🔥 Streak: {streak} days\n\n🧠 {explanation}")
    else:
        await query.edit_message_text(f"❌ Wrong! Correct: {correct}\n\n🧠 {explanation}")

# --- /leaderboard
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = supabase.table("users").select("full_name", "score").order("score", desc=True).limit(10).execute().data
    if not data:
        await update.message.reply_text("🏆 No leaderboard data yet.")
        return
    
    msg = "🏆 *Top 10 Learners This Week:*\n\n"
    for i, user in enumerate(data, 1):
        msg += f"{i}. {user['full_name']} — {user['score']} pts\n"
    await update.message.reply_markdown(msg)

# --- /syllabus
async def syllabus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["GK", "Computer"], ["English", "Math"]]
    await update.message.reply_text(
        "📘 Choose subject to view syllabus:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return "CHOOSE_SYLLABUS_SUBJECT"

# --- show topics
async def show_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text
    user_id = update.effective_user.id
    topic_data = supabase.table("topics").select("*").eq("subject", subject).execute().data
    user_completed = supabase.table("user_topics").select("topic_id").eq("telegram_id", user_id).execute().data
    completed_ids = {row['topic_id'] for row in user_completed}

    buttons = []
    for topic in topic_data:
        check = "✅" if topic["id"] in completed_ids else "⬜️"
        buttons.append([KeyboardButton(f"{check} {topic['topic_name']}")])

    context.user_data["syllabus_subject"] = subject
    context.user_data["topic_data"] = {t['topic_name']: t['id'] for t in topic_data}

    await update.message.reply_text(
        f"📖 *{subject} Syllabus:*\nTap a topic to mark as complete ✅",
        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return "MARK_TOPIC"

# --- mark topic complete
async def mark_topic_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    full_text = update.message.text
    topic_name = full_text.replace("✅ ", "").replace("⬜️ ", "")
    topic_id = context.user_data["topic_data"].get(topic_name)

    if not topic_id:
        await update.message.reply_text("❌ Topic not recognized.")
        return ConversationHandler.END

    supabase.table("user_topics").upsert({
        "telegram_id": user_id,
        "topic_id": topic_id,
        "completed": True
    }).execute()

    await update.message.reply_text(f"✅ Marked '{topic_name}' as complete!")
    return await show_topics(update, context)

# --- MAIN
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Quiz Conversation
    quiz_conv = ConversationHandler(
        entry_points=[CommandHandler("quiz", quiz)],
        states={"CHOOSE_SUBJECT": [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subject)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("❌ Cancelled."))],
    )

    # Syllabus Conversation
    syllabus_conv = ConversationHandler(
        entry_points=[CommandHandler("syllabus", syllabus)],
        states={
            "CHOOSE_SYLLABUS_SUBJECT": [MessageHandler(filters.TEXT & ~filters.COMMAND, show_topics)],
            "MARK_TOPIC": [MessageHandler(filters.TEXT & ~filters.COMMAND, mark_topic_done)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("❌ Cancelled."))],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(quiz_conv)
    app.add_handler(syllabus_conv)
    app.add_handler(CallbackQueryHandler(handle_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
