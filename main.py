import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import db, ping_db

# -----------------------------
# 🔹 Bot Configuration
# -----------------------------
API_ID = 24945402  # your API_ID
API_HASH = "6118e50f5dc4e3a955e50b22cf673ae2"  # your API_HASH
BOT_TOKEN = "8388938837:AAFLBd4BHMUnbwelsqcXbsjtuz6t7-nTZoc"  # your BotFather token
OWNER_ID = 123456789  # replace with your numeric Telegram ID
FORCE_CHANNEL = "@CosmicAdsPro"
FORCE_GROUP = "@Cosmicadsgroup"
PREMIUM_LINK = "https://your-premium-link.com"
ADMINS = ["King_bst34", "Sherrbst", "LordHarsh"]
LOGS_CHAT_ID = "@your_logs_channel"  # optional logs bot/channel

# -----------------------------
# 🔹 Create Bot Client
# -----------------------------
bot = Client("cosmic_bot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

# Ping MongoDB on start
ping_db()

# -----------------------------
# 🔹 Start Command
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

    # Privacy Policy (simple text)
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
    # Show Dashboard
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
# 🔹 Dashboard Button Callbacks (Skeleton)
# -----------------------------
@bot.on_callback_query()
async def dashboard_callbacks(_, query):
    data = query.data

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
        await query.answer("🟢 Contact Admins: " + ", ".join(ADMINS), show_alert=True)
    else:
        await query.answer("❌ Unknown action", show_alert=True)

# -----------------------------
# 🔹 Run Bot
# -----------------------------
print("🚀 Bot is starting...")
bot.run()
