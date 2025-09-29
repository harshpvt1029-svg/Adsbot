import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import logging
from flask import Flask
from threading import Thread

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= ENVIRONMENT VARS =================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split()] if os.getenv("ADMINS") else []
MONGO_URI = os.getenv("MONGO_URI")

# ================= MONGO DB =================
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["bot_db"]
users_col = db["users"]

# ================= FLASK KEEP-ALIVE =================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running safely ✅"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

Thread(target=run).start()

# ================= BOT CLIENT =================
bot = Client(
    "cosmic_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= START =================
@bot.on_message(filters.command("start"))
async def start(client, message):
    user = {"id": message.from_user.id, "name": message.from_user.first_name}
    users_col.update_one({"id": user["id"]}, {"$set": user}, upsert=True)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Add Account", callback_data="add_account")],
            [InlineKeyboardButton("💬 Add Message", callback_data="add_message")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("📜 Privacy Policy", callback_data="privacy")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")]
        ]
    )
    await message.reply_text(
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "Welcome to **Cosmic Bot** 🚀\n\n"
        "Choose an option below 👇",
        reply_markup=keyboard
    )

# ================= CALLBACK HANDLERS =================
@bot.on_callback_query()
async def callbacks(client, callback_query):
    data = callback_query.data

    if data == "add_account":
        await callback_query.message.edit_text(
            "➕ **Add Account Tutorial**:\n\n"
            "1️⃣ Enter your account details.\n"
            "2️⃣ Confirm safely.\n\n"
            "⚠️ *Note*: We are **not storing your data** 🔒"
        )

    elif data == "add_message":
        await callback_query.message.edit_text(
            "💬 **Add Message Tutorial**:\n\n"
            "1️⃣ Type your message.\n"
            "2️⃣ Set when it should be sent.\n\n"
            "⚠️ *Note*: Please **do not abuse** ❌"
        )

    elif data == "settings":
        await callback_query.message.edit_text(
            "⚙️ **Settings Tutorial**:\n\n"
            "1️⃣ Manage your keywords.\n"
            "2️⃣ Customize replies.\n\n"
            "✨ You’re in full control!"
        )

    elif data == "privacy":
        await callback_query.message.edit_text(
            "📜 **Privacy Policy**:\n\n"
            "We respect your privacy 🛡️\n"
            "✅ We do **not store personal data**.\n"
            "✅ Only necessary details are saved securely.\n"
            "✅ Abuse or spam will not be tolerated."
        )

    elif data == "dashboard":
        await callback_query.message.edit_text(
            "📊 **Dashboard Tutorial**:\n\n"
            "1️⃣ Track your accounts.\n"
            "2️⃣ See your message stats.\n"
            "3️⃣ Manage everything in one place.\n\n"
            "🚀 Coming with more features soon!"
        )

    else:
        await callback_query.message.edit_text("❌ Unknown action.")

# ================= RUN =================
if __name__ == "__main__":
    logger.info("🤖 Cosmic Bot is starting...")
    bot.run()
