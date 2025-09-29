import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

# ====================
# Environment Variables
# ====================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
ADMINS = [int(x.strip()) for x in os.getenv("ADMINS", "").replace(',', ' ').split()] if os.getenv("ADMINS") else []
MONGO_URI = os.getenv("MONGO_URI")
LOG_CHANNEL = os.getenv("LOGS_CHANNEL")
FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL")
FORCE_JOIN_GROUP = os.getenv("FORCE_JOIN_GROUP")
PRIVACY_LINK = os.getenv("PRIVACY_LINK")

# ====================
# MongoDB Connection
# ====================
client_db = MongoClient(MONGO_URI)
db_name = "cosmic_ads"  # default database
db = client_db.get_database(db_name)
try:
    client_db.admin.command("ping")
    print(f"✅ Connected to MongoDB! Using database: {db_name}")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# ====================
# Pyrogram Client
# ====================
bot = Client(
    "auto_ads_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ====================
# Helper Functions
# ====================
def is_admin(user_id):
    return user_id in ADMINS or user_id == OWNER_ID

def dashboard_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Add Accounts", callback_data="add_acc")],
        [InlineKeyboardButton("🗂 My Accounts", callback_data="my_acc"),
         InlineKeyboardButton("✉️ Set Ad Message", callback_data="set_msg")],
        [InlineKeyboardButton("⏱ Set Time Intervals", callback_data="set_time"),
         InlineKeyboardButton("▶️ Start/Stop Ad", callback_data="start_stop")],
        [InlineKeyboardButton("👥 Add Groups", callback_data="add_groups")],
        [InlineKeyboardButton("⭐ Premium", callback_data="premium"),
         InlineKeyboardButton("🛠 Support", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ====================
# Start Command
# ====================
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = f"👋 Hello {message.from_user.first_name}!\n\n" \
           f"Please join our channel and group to use the bot.\n" \
           f"[Channel]({FORCE_JOIN_CHANNEL}) | [Group]({FORCE_JOIN_GROUP})\n\n" \
           f"📜 [Privacy Policy]({PRIVACY_LINK})"
    await message.reply_text(text, reply_markup=dashboard_keyboard(), disable_web_page_preview=True)

# ====================
# Callback Queries
# ====================
@bot.on_callback_query()
async def callbacks(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "add_acc":
        await callback_query.answer("⚠️ Note: We are not storing your data.", show_alert=True)
        await callback_query.message.reply_text("📱 Send your account number in international format.")

    elif data == "set_msg":
        await callback_query.answer("⚠️ Note: Do not abuse this feature.", show_alert=True)
        await callback_query.message.reply_text("✉️ Send the message you want to auto-send as ads.")

    elif data == "start_stop":
        await callback_query.answer("▶️ Ads process toggled.", show_alert=True)

    elif data == "premium":
        await callback_query.message.reply_text(
            "⭐ To get Premium, please DM the owner or admins."
        )

    elif data == "support":
        await callback_query.message.reply_text(
            "🛠 Contact Admins:\n" + "\n".join([f"@{x}" for x in ["King_bst34","Sherrbst"]])
        )

# ====================
# Run Bot
# ====================
print("✅ Bot is starting...")
bot.run()
