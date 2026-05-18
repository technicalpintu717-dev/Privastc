import telebot
from telebot import types
import smtplib
import time
import threading
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============ CONFIG ============
API_TOKEN = '8325851971:AAHQnEfumrJwcz_Ncet34PIBI0XQFP2iFnw'
OWNER_ID = 8542876714
bot = telebot.TeleBot(API_TOKEN)

# Use environment variable for port (Railway requirement)
PORT = int(os.environ.get('PORT', 8080))

user_db = {}

# ============ CORE ENGINE ============
def test_account_credentials(email, password):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.set_debuglevel(0)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(email, password)
        server.quit()
        return True
    except Exception as e:
        print(f"Test failed for {email}: {e}")
        return False

def mass_mailer_engine(chat_id, target, subject, body, total_limit):
    data = user_db[chat_id]
    accounts = data['accounts']
    sent, failed, acc_index = 0, 0, 0
    
    working_accounts = []
    for acc in accounts:
        if test_account_credentials(acc['email'], acc['pass']):
            working_accounts.append(acc)
        else:
            print(f"Skipping {acc['email']}")
    
    if not working_accounts:
        bot.send_message(chat_id, "❌ **No working accounts!**\n\nUse App Passwords for Gmail", parse_mode="Markdown")
        data['running'] = False
        return
    
    bot.send_message(chat_id, f"🚀 **MAIL START**\n🎯 Target: `{target}`\n🔢 Limit: `{total_limit}`\n📧 Accounts: `{len(working_accounts)}`", parse_mode="Markdown")

    while sent < total_limit and data['running']:
        current_acc = working_accounts[acc_index]
        server = None
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.set_debuglevel(0)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(current_acc['email'], current_acc['pass'])
            
            for _ in range(5):
                if sent >= total_limit or not data['running']:
                    break
                try:
                    msg = MIMEMultipart()
                    msg['From'] = current_acc['email']
                    msg['To'] = target
                    msg['Subject'] = subject
                    msg.attach(MIMEText(body, 'plain'))
                    server.send_message(msg)
                    sent += 1
                    time.sleep(1.5)
                except:
                    failed += 1
            
            server.quit()
            server = None
            
        except Exception as e:
            failed += 1
            print(f"Login error: {e}")
            if server:
                try:
                    server.quit()
                except:
                    pass
        
        acc_index = (acc_index + 1) % len(working_accounts)
        
        if sent % 50 == 0 and sent > 0:
            bot.send_message(chat_id, f"📊 Progress: `{sent}/{total_limit}` sent", parse_mode="Markdown")
    
    data['running'] = False
    bot.send_message(chat_id, f"🏁 **FINISH**\n✅ Sent: `{sent}`\n❌ Failed: `{failed}`")

# ============ BROADCAST FUNCTIONS ============
def broadcast_to_all(message_text):
    count = 0
    failed = 0
    for user_id in user_db.keys():
        try:
            bot.send_message(user_id, message_text)
            count += 1
            time.sleep(0.1)
        except:
            failed += 1
    return count, failed

def broadcast_with_photo(message_text, photo_id):
    count = 0
    failed = 0
    for user_id in user_db.keys():
        try:
            bot.send_photo(user_id, photo_id, caption=message_text)
            count += 1
            time.sleep(0.1)
        except:
            failed += 1
    return count, failed

# ============ INLINE INTERFACE ============
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Account", callback_data="add_acc"),
        types.InlineKeyboardButton("📋 My Accounts", callback_data="list_acc"),
        types.InlineKeyboardButton("🎯 Set Target", callback_data="set_target"),
        types.InlineKeyboardButton("📝 Craft Msg", callback_data="set_msg"),
        types.InlineKeyboardButton("🔥 START MAIL 💀", callback_data="pre_start"),
        types.InlineKeyboardButton("⏹ Stop", callback_data="stop_bomb"),
        types.InlineKeyboardButton("📊 Status", callback_data="status"),
        types.InlineKeyboardButton("🧹 Clear All", callback_data="clear")
    )
    return markup

def get_owner_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Account", callback_data="add_acc"),
        types.InlineKeyboardButton("📋 My Accounts", callback_data="list_acc"),
        types.InlineKeyboardButton("🎯 Set Target", callback_data="set_target"),
        types.InlineKeyboardButton("📝 Craft Msg", callback_data="set_msg"),
        types.InlineKeyboardButton("🔥 START MAIL 💀", callback_data="pre_start"),
        types.InlineKeyboardButton("⏹ Stop", callback_data="stop_bomb"),
        types.InlineKeyboardButton("📊 Status", callback_data="status"),
        types.InlineKeyboardButton("🧹 Clear All", callback_data="clear"),
        types.InlineKeyboardButton("📢 BROADCAST", callback_data="broadcast_menu"),
        types.InlineKeyboardButton("📈 Total Users", callback_data="total_users")
    )
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    cid = message.chat.id
    if cid not in user_db:
        user_db[cid] = {'accounts': [], 'target': None, 'running': False, 'subj': 'Alert', 'body': 'Sample'}
    
    if cid == OWNER_ID:
        bot.send_message(cid, "**ALPHA MASS MAILER**\nStatus: Online 🟢", parse_mode="Markdown", reply_markup=get_owner_menu())
    else:
        bot.send_message(cid, "ALPHA MASS MAILER\nStatus: Online 🟢", reply_markup=get_main_menu())

# ============ BROADCAST HANDLERS ============
@bot.callback_query_handler(func=lambda call: call.data == "broadcast_menu")
def broadcast_menu(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ Owner only!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📝 Send Text", callback_data="broadcast_text"),
        types.InlineKeyboardButton("🖼 Send Text + Photo", callback_data="broadcast_photo"),
        types.InlineKeyboardButton("📊 Stats Only", callback_data="broadcast_stats"),
        types.InlineKeyboardButton("🔙 Back", callback_data="back_main")
    )
    bot.edit_message_text("📢 **BROADCAST MENU**\nChoose:", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "total_users")
def total_users(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ Owner only!")
        return
    total = len(user_db.keys())
    bot.answer_callback_query(call.id, f"Total Users: {total}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "broadcast_stats")
def broadcast_stats(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ Owner only!")
        return
    users_list = "\n".join([f"• `{uid}`" for uid in list(user_db.keys())[:20]])
    bot.send_message(call.message.chat.id, f"📊 **USERS:**\n{users_list}", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "broadcast_text")
def broadcast_text_prompt(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ Owner only!")
        return
    msg = bot.send_message(call.message.chat.id, "📝 **Send your message:**\n(/cancel to cancel)")
    bot.register_next_step_handler(msg, execute_broadcast_text)

def execute_broadcast_text(message):
    if message.text == "/cancel":
        bot.send_message(message.chat.id, "❌ Cancelled.")
        return
    bot.send_message(message.chat.id, "📢 Broadcasting...")
    count, failed = broadcast_to_all(message.text)
    bot.send_message(message.chat.id, f"✅ **Done!**\n📨 Sent: `{count}`\n❌ Failed: `{failed}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "broadcast_photo")
def broadcast_photo_prompt(call):
    if call.message.chat.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ Owner only!")
        return
    msg = bot.send_message(call.message.chat.id, "🖼 **Send the PHOTO first**")
    bot.register_next_step_handler(msg, wait_for_photo)

def wait_for_photo(message):
    if message.text == "/cancel":
        bot.send_message(message.chat.id, "❌ Cancelled.")
        return
    if message.photo:
        photo_id = message.photo[-1].file_id
        msg2 = bot.send_message(message.chat.id, "📝 **Now send caption:**")
        bot.register_next_step_handler(msg2, lambda m: execute_broadcast_photo(m, photo_id))
    else:
        bot.send_message(message.chat.id, "❌ Send PHOTO, not text.")
        bot.register_next_step_handler(message, wait_for_photo)

def execute_broadcast_photo(message, photo_id):
    if message.text == "/cancel":
        bot.send_message(message.chat.id, "❌ Cancelled.")
        return
    bot.send_message(message.chat.id, "📢 Broadcasting with photo...")
    count, failed = broadcast_with_photo(message.text, photo_id)
    bot.send_message(message.chat.id, f"✅ **Done!**\n📨 Sent: `{count}`\n❌ Failed: `{failed}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_to_main(call):
    if call.message.chat.id == OWNER_ID:
        bot.edit_message_text("**ALPHA MOD**\nOnline 🟢", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=get_owner_menu())
    else:
        bot.edit_message_text("ALPHA DASHBOARD\nOnline 🟢", call.message.chat.id, call.message.message_id, reply_markup=get_main_menu())

# ============ MAIN HANDLERS ============
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid = call.message.chat.id
    if call.data == "add_acc":
        msg = bot.send_message(cid, "📧 Send: `email:password` or `email:app_password`")
        bot.register_next_step_handler(msg, save_acc)
    elif call.data == "list_acc":
        accs = user_db[cid]['accounts']
        text = "📂 **ACCOUNTS:**\n" + "\n".join([f"• {a['email']}" for a in accs]) if accs else "No accounts."
        bot.send_message(cid, text, parse_mode="Markdown")
    elif call.data == "set_target":
        msg = bot.send_message(cid, "🎯 **Target Email:**")
        bot.register_next_step_handler(msg, save_target)
    elif call.data == "set_msg":
        msg = bot.send_message(cid, "📝 **Subject:**")
        bot.register_next_step_handler(msg, save_subj)
    elif call.data == "pre_start":
        msg = bot.send_message(cid, "🔢 **How many emails?**")
        bot.register_next_step_handler(msg, final_launch)
    elif call.data == "stop_bomb":
        user_db[cid]['running'] = False
        bot.answer_callback_query(call.id, "Stopping...")
    elif call.data == "status":
        d = user_db[cid]
        bot.send_message(cid, f"👤 Accounts: {len(d['accounts'])}\n🎯 Target: {d['target']}")
    elif call.data == "clear":
        user_db[cid]['accounts'] = []
        bot.answer_callback_query(call.id, "Cleared!")

def save_acc(m):
    try:
        e, p = m.text.split(':', 1)
        user_db[m.chat.id]['accounts'].append({'email': e.strip(), 'pass': p.strip()})
        if test_account_credentials(e.strip(), p.strip()):
            bot.send_message(m.chat.id, "✅ Added + Working!")
        else:
            bot.send_message(m.chat.id, "⚠️ Added but NOT working! Use App Password.\n\nHow to get App Password:\n1. Google Account → Security\n2. 2-Step Verification ON\n3. App Passwords → Generate\n4. Use 16-digit code as password")
    except:
        bot.send_message(m.chat.id, "❌ Format: `email:password`")

def save_target(m):
    user_db[m.chat.id]['target'] = m.text.strip()
    bot.send_message(m.chat.id, "✅ Target saved!")

def save_subj(m):
    user_db[m.chat.id]['subj'] = m.text.strip()
    msg = bot.send_message(m.chat.id, "📝 **Body/Content:**")
    bot.register_next_step_handler(msg, save_body)

def save_body(m):
    user_db[m.chat.id]['body'] = m.text.strip()
    bot.send_message(m.chat.id, "✅ Message saved!")

def final_launch(m):
    try:
        cid = m.chat.id
        limit = int(m.text)
        d = user_db[cid]
        if not d['accounts'] or not d['target']:
            return bot.send_message(cid, "❌ Add accounts and target first!")
        d['running'] = True
        threading.Thread(target=mass_mailer_engine, args=(cid, d['target'], d['subj'], d['body'], limit)).start()
    except:
        bot.send_message(m.chat.id, "❌ Enter number only!")

# ============ WEBHOOK / POLLING ============
if __name__ == "__main__":
    print("🤖 Bot Started!")
    print(f"👑 Owner ID: {OWNER_ID}")
    # Railway requires webhook or polling on a port
    # Remove webhook and use polling
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)