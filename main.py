import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo.mongo_client import MongoClient

# -----------------------------
# 🔹 Environment Variables
# -----------------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL")
FORCE_GROUP = os.getenv("FORCE_GROUP")
ADMINS = [int(x) for x in os.getenv("ADMINS").split(",")]
LOGS_CHAT_ID = os.getenv("LOGS_CHAT_ID")
PREMIUM_LINK = os.getenv("PREMIUM_LINK")
MONGO_URI = os.getenv("MONGO_URI")

# Auto-premium users (owner + admins)
PREMIUM_USERS = [OWNER_ID] + ADMINS

# -----------------------------
# 🔹 MongoDB Setup
# -----------------------------
client = MongoClient(MONGO_URI)
db = client.get_database()  # defaults to URI database (cosmic_ads)

def ping_db():
    try:
        client.admin.command('ping')
        print("✅ Connected to MongoDB!")
    except Exception as e:
        print("❌ MongoDB connection failed:", e)

ping_db()

# -----------------------------
# 🔹 Bot Setup
# -----------------------------
bot = Client("cosmic_bot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

# -----------------------------
# 🔹 Helper Functions
# -----------------------------
def is_premium(user_id):
    return user_id in PREMIUM_USERS or db.premium.find_one({"user_id": user_id, "approved": True})

async def send_logs(text):
    try:
        await bot.send_message(LOGS_CHAT_ID, text)
    except:
        pass

# -----------------------------
# 🔹 /start Command
# -----------------------------
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    # Force join check
    try:
        await bot.get_chat_member(FORCE_CHANNEL, message.from_user.id)
        await bot.get_chat_member(FORCE_GROUP, message.from_user.id)
    except:
        await message.reply(
            f"❌ Please join {FORCE_CHANNEL} and {FORCE_GROUP} first to use the bot!"
        )
        return

    # Privacy Policy
    privacy_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("I have read", callback_data="privacy_accept")]]
    )
    await message.reply(
        "📄 Please read our privacy policy: https://gist.github.com/harshpvt1029-svg/504fba01171ef14c81f9f7143f5349c5#file-privacy-policy",
        reply_markup=privacy_button
    )

# -----------------------------
# 🔹 Privacy Accept Callback
# -----------------------------
@bot.on_callback_query(filters.regex("privacy_accept"))
async def privacy_accept(_, callback_query):
    dashboard_buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Add Accounts", callback_data="add_accounts")],
            [InlineKeyboardButton("My Accounts", callback_data="my_accounts"),
             InlineKeyboardButton("Set Ad Message", callback_data="set_ad")],
            [InlineKeyboardButton("Set Time Intervals", callback_data="set_time"),
             InlineKeyboardButton("Start/Stop Ad", callback_data="start_stop")],
            [InlineKeyboardButton("Add Groups", callback_data="add_groups")],
            [InlineKeyboardButton("Premium", url=PREMIUM_LINK),
             InlineKeyboardButton("Support", callback_data="support")]
        ]
    )
    await callback_query.message.edit_text(
        "✅ Dashboard ready! Select an option below:",
        reply_markup=dashboard_buttons
    )

# -----------------------------
# 🔹 Dashboard Button Callbacks
# -----------------------------
@bot.on_callback_query()
async def dashboard_callbacks(_, query):
    data = query.data
    user_id = query.from_user.id

    if data == "add_accounts":
        await query.answer("🟢 Feature: Add Accounts (coming soon)", show_alert=True)
    elif data == "my_accounts":
        await query.answer("🟢 Feature: My Accounts (coming soon)", show_alert=True)
    elif data == "set_ad":
        await query.answer("🟢 Feature: Set Ad Message (coming soon)", show_alert=True)
    elif data == "set_time":
        await query.answer("🟢 Feature: Set Time Intervals (coming soon)", show_alert=True)
    elif data == "start_stop":
        await query.answer("🟢 Feature: Start/Stop Ad (coming soon)", show_alert=True)
    elif data == "add_groups":
        await query.answer("🟢 Feature: Add Groups (coming soon)", show_alert=True)
    elif data == "support":
        support_text = f"Admins: @LordHarsh, @King_bst34, @Sherrbst"
        await query.answer(support_text, show_alert=True)
    else:
        await query.answer("❌ Unknown action", show_alert=True)

# -----------------------------
# 🔹 Premium Approval Command
# -----------------------------
@bot.on_message(filters.command("approve") & filters.user(OWNER_ID))
async def approve(_, message):
    try:
        username = message.text.split()[1].replace("@", "")
        db.premium.update_one({"username": username}, {"$set": {"approved": True}}, upsert=True)
        await message.reply(f"✅ @{username} has been approved for Premium!")
        await send_logs(f"✅ @{username} approved by owner/admin {message.from_user.first_name}")
    except IndexError:
        await message.reply("❌ Usage: /approve <username>")

# -----------------------------
# 🔹 Run Bot
# -----------------------------
print("🚀 Bot is starting...")
bot.run()
