from supabase_client import supabase
import random

def get_random_mcq(subject):
    response = supabase.table("mcqs").select("*").eq("subject", subject).execute()
    data = response.data
    if not data:
        return None
    return random.choice(data)

def format_mcq(mcq):
    return f"📘 *{mcq['subject']}*\n\n❓ {mcq['question']}\n\nA. {mcq['option_a']}\nB. {mcq['option_b']}\nC. {mcq['option_c']}\nD. {mcq['option_d']}"
