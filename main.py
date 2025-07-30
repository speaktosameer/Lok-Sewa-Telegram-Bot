import os
from dotenv import load_dotenv
from datetime import datetime, date
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
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
        "Use:\n/quiz – Practice MCQs\n/syllabus – Track syllabus\n/leaderboard – View top scorers\n"
        "/badges – View achievements\n/exams – Upcoming exams\n/remindme – Daily countdown alerts",
        parse_mode="Markdown"
    )

# --- /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start – Start bot\n"
        "/quiz – Practice questions\n"
        "/syllabus – View & track topics\n"
        "/leaderboard – Top users\n"
        "/badges – View earned achievements\n"
        "/exams – Upcoming exam countdown\n"
        "/remindme – Set daily reminder"
    )

# --- /quiz
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["GK", "Computer"], ["English", "Math"]]
    await update.message.reply_text(
        "📚 Choose a subject to start your quiz:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return "CHOOSE_SUBJECT"

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
    last_answered = user_data.get("last_answered")
    streak = user_data.get("streak", 0)
    last_date = datetime.strptime(last_answered, "%Y-%m-%d").date() if last_answered else None
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

        # Badge unlock
        existing = supabase.table("user_badges").select("badge_id").eq("telegram_id", user_id).execute().data
        existing_ids = {b['badge_id'] for b in existing}
        badges = supabase.table("badges").select("*").lte("streak_day", streak).execute().data
        new_badges = []
        for badge in badges:
            if badge["id"] not in existing_ids:
                supabase.table("user_badges").insert({
                    "telegram_id": user_id,
                    "badge_id": badge["id"]
                }).execute()
                new_badges.append(f"{badge['emoji']} *{badge['name']}* – {badge['description']}")
        if new_badges:
            await query.message.reply_markdown("🎉 *New Badge Unlocked!*\n\n" + "\n".join(new_badges))

        await query.edit_message_text(f"✅ Correct! (+{total_points} pts)\n🔥 Streak: {streak} days\n\n🧠 {explanation}")
    else:
        await query.edit_message_text(f"❌ Wrong! Correct: {correct}\n\n🧠 {explanation}")

# --- /leaderboard
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = supabase.table("users").select("full_name", "score").order("score", desc=True).limit(10).execute().data
    if not data:
        await update.message.reply_text("🏆 No leaderboard data yet.")
        return
    msg = "🏆 *Top 10 Learners:*\n\n"
    for i, user in enumerate(data, 1):
        msg += f"{i}. {user['full_name']} — {user['score']} pts\n"
    await update.message.reply_markdown(msg)

# --- /badges
async def my_badges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_badges = supabase.table("user_badges").select("badge_id").eq("telegram_id", user_id).execute().data
    badge_ids = [b['badge_id'] for b in user_badges]
    if not badge_ids:
        await update.message.reply_text("😢 You haven’t earned any badges yet.")
        return
    badges = supabase.table("badges").select("*").in_("id", badge_ids).execute().data
    msg = "🏅 *Your Achievements:*\n\n"
    for badge in badges:
        msg += f"{badge['emoji']} *{badge['name']}* – {badge['description']}\n"
    await update.message.reply_markdown(msg)

# --- /exams
async def exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    data = supabase.table("exams").select("*").gte("exam_date", str(today)).order("exam_date").execute().data
    if not data:
        await update.message.reply_text("🎯 No upcoming exams found.")
        return
    msg = "📅 *Upcoming Lok Sewa Exams:*\n\n"
    for exam in data:
        exam_day = datetime.strptime(exam['exam_date'], "%Y-%m-%d").date()
        days_left = (exam_day - today).days
        msg += f"📌 *{exam['name']}*\n🗓 {exam_day.strftime('%B %d, %Y')} – In {days_left} days\n📝 {exam['description']}\n\n"
    await update.message.reply_markdown(msg)

# --- /remindme
async def remindme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Morning (8AM)", "Evening (6PM)"]]
    await update.message.reply_text(
        "⏰ When would you like to receive daily exam reminders?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return "SET_REMINDER_TIME"

async def save_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    user_id = update.effective_user.id
    if "Morning" in choice:
        pref = "morning"
    elif "Evening" in choice:
        pref = "evening"
    else:
        await update.message.reply_text("❌ Invalid selection.")
        return ConversationHandler.END
    supabase.table("reminders").upsert({
        "telegram_id": user_id,
        "time_pref": pref,
        "enabled": True
    }).execute()
    await update.message.reply_text(f"✅ Daily reminders set for *{pref.capitalize()}*!", parse_mode="Markdown")
    return ConversationHandler.END

# --- main()
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("badges", my_badges))
    app.add_handler(CommandHandler("exams", exams))

    # Quiz flow
    quiz_conv = ConversationHandler(
        entry_points=[CommandHandler("quiz", quiz)],
        states={"CHOOSE_SUBJECT": [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_subject)]},
        fallbacks=[]
    )
    app.add_handler(quiz_conv)

    # Reminder setup
    remind_conv = ConversationHandler(
        entry_points=[CommandHandler("remindme", remindme)],
        states={"SET_REMINDER_TIME": [MessageHandler(filters.TEXT & ~filters.COMMAND, save_reminder)]},
        fallbacks=[]
    )
    app.add_handler(remind_conv)

    # Answer handler
    app.add_handler(CallbackQueryHandler(handle_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
