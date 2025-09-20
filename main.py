from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid, PhoneCodeExpired
from pyrogram.enums import ChatType, ChatMemberStatus
import asyncio, time

# ---------------- CONFIG ----------------
BOT_TOKEN = "7544282169:AAHzdcWOVEVfqeS7q7YT0szI9POBu8tONSc"
API_ID = 24945402
API_HASH = "6118e50f5dc4e3a955e50b22cf673ae2"
ADMIN_ID = 8463150711
FORCE_CHANNEL = "@LordAdsPro"
FORCE_GROUP = "@LordAdsGroup"
BOT_USERNAME = "@LordAdsBot"
MIN_INTERVAL = 300  # 5 minutes minimum interval
# ----------------------------------------

bot = Client("ad_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# ---------------- STATE ----------------
listen_states = {}
user_temp_clients = {}
otp_inputs = {}
user_accounts = {}       # user_id: [ { "client": Client, "first_name": str, "username": str } ]
user_ad_message = {}     # user_id: ad text
user_time_interval = {}  # user_id: seconds
premium_users = set()
ad_tasks = {}            # user_id: asyncio task
user_groups = {}         # user_id: {account_index: [group_ids]}
user_warnings = {}       # user_id: warning count
all_bot_users = set()    # Track all users who interact with the bot

# ---------------- MEMBERSHIP ----------------
async def check_membership(user_id):
    try:
        ch = await bot.get_chat_member(FORCE_CHANNEL, user_id)
        gr = await bot.get_chat_member(FORCE_GROUP, user_id)
        if ch.status in ["left","kicked"] or gr.status in ["left","kicked"]:
            return False
        return True
    except:
        return False

# ---------------- DASHBOARD ----------------
def dashboard_buttons():
    buttons = [
        [InlineKeyboardButton("Add Accounts", callback_data="add_accounts"),
         InlineKeyboardButton("My Accounts", callback_data="my_accounts")],
        [InlineKeyboardButton("Set Ad Message", callback_data="set_ad")],
        [InlineKeyboardButton("Set Time Intervals", callback_data="set_time"),
         InlineKeyboardButton("Start/Stop Ad", callback_data="ad_control")],
        [InlineKeyboardButton("Add Groups", callback_data="add_groups")],
        [InlineKeyboardButton("Premium", callback_data="premium"),
         InlineKeyboardButton("Support", url="https://t.me/NeoHarsh")]
    ]
    return InlineKeyboardMarkup(buttons)

# ---------------- OTP KEYPAD ----------------
def otp_keypad(current=""):
    buttons = [
        [InlineKeyboardButton("1", callback_data="otp_1"), InlineKeyboardButton("2", callback_data="otp_2")],
        [InlineKeyboardButton("3", callback_data="otp_3"), InlineKeyboardButton("4", callback_data="otp_4")],
        [InlineKeyboardButton("5", callback_data="otp_5"), InlineKeyboardButton("6", callback_data="otp_6")],
        [InlineKeyboardButton("7", callback_data="otp_7"), InlineKeyboardButton("8", callback_data="otp_8")],
        [InlineKeyboardButton("9", callback_data="otp_9"), InlineKeyboardButton("0", callback_data="otp_0")],
        [InlineKeyboardButton("🔙 Back", callback_data="otp_back"), InlineKeyboardButton("✅ OK", callback_data="otp_ok")]
    ]
    caption = f"📝 Enter the OTP code:\n\n`{current}`\n\nUse the keypad below:"
    return InlineKeyboardMarkup(buttons), caption

# ---------------- /START ----------------
@bot.on_message(filters.command("start"))
async def start(_, message):
    user_id = message.from_user.id
    all_bot_users.add(user_id)  # Track user interaction
    if not await check_membership(user_id):
        await message.reply(f"Please join the channel {FORCE_CHANNEL} and group {FORCE_GROUP} to use the bot.")
        return
    await bot.send_photo(
        chat_id=user_id,
        photo="https://i.postimg.cc/qv7fcQXb/a-logo-design-featuring-the-text-lord-ad-0sfrm-JKJTea-DLQfz82-X-Q-Sd-Clrr-URTS22-Yyz6rn-8-g.jpg",
        caption="✅ Welcome to Ad Bot Dashboard!\nChoose an option below:",
        reply_markup=dashboard_buttons()
    )

# ---------------- (rest of your code remains same) ----------------
# (All functions for add accounts, OTP, ads, groups, approve, allusers etc.)
# ---------------- RUN ----------------
bot.run()
