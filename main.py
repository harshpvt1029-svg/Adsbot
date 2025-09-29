from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid, PhoneCodeExpired
from pyrogram.enums import ChatType, ChatMemberStatus
import asyncio, os, time
from pymongo import MongoClient

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OWNER_ID = int(os.getenv("OWNER_ID"))
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",")]
FORCE_CHANNEL = os.getenv("FORCE_CHANNEL")
FORCE_GROUP = os.getenv("FORCE_GROUP")
BOT_USERNAME = os.getenv("BOT_USERNAME")
MONGO_URI = os.getenv("MONGO_URI")
MIN_INTERVAL = int(os.getenv("MIN_INTERVAL", "300"))

# ---------------- DATABASE ----------------
client_db = MongoClient(MONGO_URI)
db = client_db.get_database()  # Default DB from URI

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
auto_replies = {}        # user_id: {keyword: reply_text}

# ---------------- BOT ----------------
bot = Client("ad_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# ---------------- MEMBERSHIP CHECK ----------------
async def check_membership(user_id):
    try:
        ch = await bot.get_chat_member(FORCE_CHANNEL, user_id)
        gr = await bot.get_chat_member(FORCE_GROUP, user_id)
        if ch.status in ["left","kicked"] or gr.status in ["left","kicked"]:
            return False
        return True
    except:
        return False

# ---------------- DASHBOARD BUTTONS ----------------
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
    caption = f"📩 Enter the OTP code:\n\n`{current}`\n\nUse the keypad below:"
    return InlineKeyboardMarkup(buttons), caption

# ---------------- /START COMMAND ----------------
@bot.on_message(filters.command("start"))
async def start(_, message):
    user_id = message.from_user.id
    if not await check_membership(user_id):
        await message.reply(f"Please join the channel {FORCE_CHANNEL} and group {FORCE_GROUP} to use the bot.")
        return
    await bot.send_photo(
        chat_id=user_id,
        photo="https://i.postimg.cc/qv7fcQXb/a-logo-design-featuring-the-text-lord-ad-0sfrm-JKJTea-DLQfz82-X-Q-Sd-Clrr-URTS22-Yyz6rn-8-g.jpg",
        caption="✅ Welcome to Ad Bot Dashboard!\nChoose an option below:",
        reply_markup=dashboard_buttons()
    )

# ---------------- ADD ACCOUNT ----------------
@bot.on_callback_query(filters.regex("add_accounts"))
async def add_account(_, query: CallbackQuery):
    user_id = query.from_user.id
    await query.message.reply("📱 Enter your phone number with country code (e.g., +1234567890):")
    listen_states[user_id] = "waiting_phone"

# ---------------- HANDLE OTP ----------------
@bot.on_callback_query(filters.regex(r"^otp_"))
async def handle_otp(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    if user_id not in otp_inputs:
        otp_inputs[user_id] = ""

    if data.startswith("otp_") and data not in ["otp_back", "otp_ok"]:
        otp_inputs[user_id] += data[4:]
    elif data=="otp_back":
        otp_inputs[user_id] = otp_inputs[user_id][:-1]
    elif data=="otp_ok":
        otp_code = otp_inputs.get(user_id,"")
        if not otp_code:
            await query.answer("❌ Enter OTP first", show_alert=True)
            return
        if user_id not in user_temp_clients:
            await query.answer("❌ Session not found. Start again.", show_alert=True)
            return
        temp_client = user_temp_clients[user_id]["client"]
        phone = user_temp_clients[user_id]["phone"]
        phone_code_hash = user_temp_clients[user_id]["phone_code_hash"]
        try:
            await temp_client.sign_in(phone_number=phone, phone_code_hash=phone_code_hash, phone_code=otp_code)
            me = await temp_client.get_me()
            user_accounts.setdefault(user_id,[]).append({
                "client": temp_client,
                "first_name": me.first_name,
                "username": me.username or "N/A"
            })
            await query.message.edit_text("✅ Account logged in successfully!")
            if user_id not in premium_users:
                await temp_client.update_profile(first_name=f"{me.first_name} {BOT_USERNAME}")
                await temp_client.update_profile(bio=f"AdBot Managed: {BOT_USERNAME}")
            del user_temp_clients[user_id]
            del otp_inputs[user_id]
            listen_states.pop(user_id,None)
        except SessionPasswordNeeded:
            await query.message.edit_text("🔒 2FA enabled. Send your password now:")
            listen_states[user_id]="waiting_2fa"
            del otp_inputs[user_id]
        except PhoneCodeInvalid:
            await query.answer("❌ Invalid OTP", show_alert=True)
            otp_inputs[user_id] = ""
        except PhoneCodeExpired:
            await query.answer("❌ OTP expired. Start login again.", show_alert=True)
            user_temp_clients.pop(user_id,None)
            otp_inputs.pop(user_id,None)
            listen_states.pop(user_id,None)
        except Exception as e:
            await query.answer(f"❌ Login failed: {e}", show_alert=True)
            otp_inputs[user_id]=""
        return

    keyboard, caption = otp_keypad(otp_inputs[user_id])
    try:
        await query.message.edit_text(caption, reply_markup=keyboard)
    except Exception as e:
        print(f"Keypad update error: {e}")

# ---------------- TEXT INPUT ----------------
@bot.on_message(filters.text)
async def handle_text(_, message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Phone input
    if listen_states.get(user_id)=="waiting_phone":
        try:
            session_name = f"session_{user_id}_{int(time.time())}"
            temp_client = Client(session_name, api_id=API_ID, api_hash=API_HASH)
            await temp_client.connect()
            sent_code = await temp_client.send_code(text)
            user_temp_clients[user_id]={"client":temp_client,"phone":text,"phone_code_hash":sent_code.phone_code_hash}
            otp_inputs[user_id] = ""
            keyboard, caption = otp_keypad()
            await message.reply(caption, reply_markup=keyboard)
            listen_states[user_id] = "waiting_otp"
        except PhoneNumberInvalid:
            await message.reply("❌ Invalid phone number format.")
        except Exception as e:
            await message.reply(f"❌ Error sending OTP: {e}")
        return

    # 2FA password
    if listen_states.get(user_id)=="waiting_2fa":
        if user_id not in user_temp_clients:
            await message.reply("❌ Session not found. Start again.")
            return
        temp_client = user_temp_clients[user_id]["client"]
        try:
            await temp_client.check_password(password=text)
            me = await temp_client.get_me()
            user_accounts.setdefault(user_id,[]).append({
                "client": temp_client,
                "first_name": me.first_name,
                "username": me.username or "N/A"
            })
            await message.reply("✅ Account logged in successfully with 2FA!")
            if user_id not in premium_users:
                await temp_client.update_profile(first_name=f"{me.first_name} {BOT_USERNAME}")
                await temp_client.update_profile(bio=f"AdBot Managed: {BOT_USERNAME}")
            del user_temp_clients[user_id]
            listen_states.pop(user_id,None)
        except Exception as e:
            await message.reply(f"❌ 2FA failed: {e}")
            user_temp_clients.pop(user_id,None)
            listen_states.pop(user_id,None)

    # Ad message
    if listen_states.get(user_id)=="waiting_ad":
        user_ad_message[user_id] = text
        await message.reply("✅ Ad message set successfully!")
        listen_states.pop(user_id,None)

    # Time interval
    if listen_states.get(user_id)=="waiting_time":
        try:
            interval = int(text)
            if interval<MIN_INTERVAL:
                await message.reply(f"❌ Minimum interval is {MIN_INTERVAL} seconds.")
                return
            user_time_interval[user_id]=interval
            await message.reply(f"✅ Interval set to {interval} seconds!")
            listen_states.pop(user_id,None)
        except ValueError:
            await message.reply("❌ Please enter a valid number.")
            # ---------------- DASHBOARD CALLBACKS ----------------
@bot.on_callback_query()
async def dashboard_cb(_, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    # My accounts
    if data=="my_accounts":
        accounts=user_accounts.get(user_id,[])
        if accounts:
            msg_text = f"📋 You have {len(accounts)} account(s):\n"
            for idx, acc in enumerate(accounts, start=1):
                msg_text += f"{idx}. {acc.get('first_name')} (@{acc.get('username')})\n"
            await query.message.reply(msg_text)
        else:
            await query.message.reply("❌ No accounts added yet.")

    # Set ad
    elif data=="set_ad":
        await query.message.reply("✏️ Send me the ad message:")
        listen_states[user_id]="waiting_ad"

    # Set interval
    elif data=="set_time":
        await query.message.reply(f"⏱ Send interval in seconds (minimum {MIN_INTERVAL}):")
        listen_states[user_id]="waiting_time"

    # Add groups
    elif data=="add_groups":
        accounts=user_accounts.get(user_id,[])
        if not accounts:
            await query.message.reply("❌ Add accounts first.")
            return
        msg=await query.message.reply("🔄 Reloading your groups...")
        account_groups_map={}
        total_groups=0
        for idx, acc_info in enumerate(accounts):
            acc = acc_info["client"]
            groups=[]
            try:
                async for dialog in acc.get_dialogs(limit=100):
                    chat = dialog.chat
                    if chat.type in [ChatType.SUPERGROUP, ChatType.CHANNEL]:
                        try:
                            member = await acc.get_chat_member(chat.id,"me")
                            if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                                groups.append(chat.id)
                        except:
                            groups.append(chat.id)
            except Exception as e:
                print(f"Error fetching dialogs for account {idx+1}: {e}")
            account_groups_map[idx]=groups
            total_groups+=len(groups)
            await asyncio.sleep(3)
        user_groups[user_id]=account_groups_map
        if total_groups>0:
            await msg.edit_text(f"✅ {total_groups} groups reloaded across {len(accounts)} account(s)!")
        else:
            await msg.edit_text("❌ No groups found in any account.")

    # Start/Stop ad
    elif data=="ad_control":
        if user_id in ad_tasks:
            ad_tasks[user_id].cancel()
            del ad_tasks[user_id]
            await query.message.reply("⏹ Ad sending stopped.")
        else:
            accounts=user_accounts.get(user_id,[])
            groups_map=user_groups.get(user_id,{})
            ad_msg=user_ad_message.get(user_id)
            if not accounts or not groups_map or not ad_msg:
                await query.message.reply("❌ Add accounts, groups, and ad message first.")
                return
            interval=user_time_interval.get(user_id,MIN_INTERVAL)
            task=asyncio.create_task(send_ads(user_id, interval, ad_msg))
            ad_tasks[user_id]=task
            await query.message.reply(f"▶️ Ad sending started every {interval} seconds.")

    # Premium
    elif data=="premium":
        if user_id in premium_users:
            await query.message.reply("⭐ You are already premium!")
        else:
            for admin_id in ADMINS:
                await bot.send_message(admin_id,f"💎 Premium request from user: {user_id}")
            await query.message.reply("✅ Your request has been sent to admin.")

# ---------------- SEND ADS ----------------
async def send_ads(user_id, interval, message_text):
    while True:
        try:
            accounts=user_accounts.get(user_id,[])
            groups_map=user_groups.get(user_id,{})
            for idx, acc_info in enumerate(accounts):
                acc = acc_info["client"]
                groups=groups_map.get(idx,[])
                for grp_id in groups:
                    try:
                        await acc.send_message(grp_id,message_text)
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"❌ Failed to send ad from account {idx+1} to group {grp_id}: {e}")
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break

# ---------------- AUTO REPLY ----------------
@bot.on_message(filters.group)
async def auto_reply(_, message):
    user_id = message.chat.id
    for uid, keywords in auto_replies.items():
        for keyword, reply_text in keywords.items():
            if keyword.lower() in message.text.lower():
                try:
                    await message.reply(reply_text)
                except Exception as e:
                    print(f"❌ Auto-reply error: {e}")

# ---------------- ADMIN COMMANDS ----------------
@bot.on_message(filters.command("approve") & filters.user(OWNER_ID))
async def approve(_, message):
    try:
        parts=message.text.split()
        if len(parts)!=2:
            await message.reply("❌ Usage: /approve <user_id>")
            return
        uid=int(parts[1])
        premium_users.add(uid)
        await message.reply(f"✅ User {uid} approved as premium!")
        try:
            await bot.send_message(uid,"🎉 Congratulations! You are now PREMIUM.\n✨ No bot branding applied.")
        except:
            pass
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@bot.on_message(filters.command("allusers") & filters.user(OWNER_ID))
async def all_users(_, message):
    if not user_accounts:
        await message.reply("❌ No users have added accounts yet.")
        return
    msg_text = "📋 All Users and their accounts:\n\n"
    for uid, accounts in user_accounts.items():
        msg_text += f"User ID: {uid}\n"
        for idx, acc_info in enumerate(accounts, start=1):
            first_name = acc_info.get("first_name", "[Unknown]")
            username = acc_info.get("username", "[No username]")
            msg_text += f"   {idx}. {first_name} (@{username})\n"
        msg_text += "\n"
    await message.reply(msg_text)

# ---------------- RUN BOT ----------------
bot.run()
