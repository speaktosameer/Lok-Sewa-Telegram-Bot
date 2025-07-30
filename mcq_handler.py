import random
from supabase_client import supabase_get

# Fetch and return a random MCQ by subject
def get_random_mcq(subject: str):
    mcqs = supabase_get("mcqs")
    subject_mcqs = [q for q in mcqs if q["subject"].lower() == subject.lower()]
    if not subject_mcqs:
        return None
    return random.choice(subject_mcqs)

# Format the MCQ nicely for Telegram display
def format_mcq(mcq: dict):
    return (
        f"📘 *{mcq['subject']}*\n\n"
        f"❓ *{mcq['question']}*\n\n"
        f"A. {mcq['option_a']}\n"
        f"B. {mcq['option_b']}\n"
        f"C. {mcq['option_c']}\n"
        f"D. {mcq['option_d']}"
    )
