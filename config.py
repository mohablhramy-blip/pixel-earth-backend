import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PIXEL_PRICE = 1
WELCOME_BONUS = 100
SESSION_TIMEOUT = 30
FRONTEND_URL = os.getenv("FRONTEND_URL")
