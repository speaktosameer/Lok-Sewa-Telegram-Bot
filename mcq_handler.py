# mcq_handler.py

from supabase_client import supabase
import random

def get_random_mcq(subject):
    response = supabase.table("mcqs").select("*").eq("subject", subject).execute()
    data = response.data
    if not data:
        return None
    return random.choice(data)

def format_mcq(mcq):
    return (
        f"📘 *{mcq['subject']}*\n\n"
        f"❓ *{mcq['question']}*\n\n"
        f"A. {mcq['option_a']}\n"
        f"B. {mcq['option_b']}\n"
        f"C. {mcq['option_c']}\n"
        f"D. {mcq['option_d']}"
    )
