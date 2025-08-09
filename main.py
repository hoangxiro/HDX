from keep_alive import keep_alive
import traceback  # Để lấy lỗi
import telebot
import requests
import hashlib
import random
import string
from datetime import datetime, timezone, timedelta
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN_BOT = "7399394702:AAFUh3oB6P1MYqoXmySJY2OqjiAVUYUsAWA"
TOKEN_YEUMONEY = "b926b7fc397affdd8de5be08b14ba3a3cf00dc6c7df19202c1e1d096a6d4264b"
API_KEY_PREFIX = "https://hoangdaixu.x10.bz/laykey.php?key="
API_KEY_VERIFY = "https://yeumoney.com/QL_api.php"
API_CREATE_USER = "https://hoangdaixu.x10.bz/app.php?thaotac=taotaikhoan"
SECRET = "Hoangdaixuuu_98"
DB_PATH = 'botdata.db'
VN_TZ = timezone(timedelta(hours=7))

bot = telebot.TeleBot(TOKEN_BOT)

# Stores active keys. Key expires daily.
active_keys = {}

def db_connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = db_connect()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        uid_golike TEXT NOT NULL,
        golike INTEGER NOT NULL,
        balance REAL DEFAULT 200000,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def user_created_today(telegram_id):
    conn = db_connect()
    c = conn.cursor()
    today_str = datetime.now(VN_TZ).strftime("%Y-%m-%d")
    c.execute('''
    SELECT 1 FROM users WHERE telegram_id = ? AND DATE(created_at, 'localtime') = ?
    ''', (telegram_id, today_str))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def save_user_to_db(telegram_id, username, password, uid_golike, golike, balance=200000):
    conn = db_connect()
    c = conn.cursor()
    c.execute('''
    INSERT INTO users (telegram_id, username, password, uid_golike, golike, balance, created_at)
    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (telegram_id, username, password, uid_golike, golike, balance))
    conn.commit()
    conn.close()

def generate_key(uid: str) -> str:
    date_str = datetime.now(VN_TZ).strftime("%Y%m%d")
    raw_str = f"{uid}{date_str}{SECRET}"
    md5 = hashlib.md5(raw_str.encode('utf-8')).hexdigest()
    return md5

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_random_uid(length=19):
    uid = str(random.randint(1,9))
    for _ in range(length-1):
        uid += str(random.randint(0,9))
    return uid

def get_user_icon(username: str):
    icon = f"❤️ [{username[:2].upper()}]"
    return icon

TARGET_CHAT_ID = -1002893907510

def private_chat_only(func):
    def wrapper(message):
        if message.chat.id == TARGET_CHAT_ID:
            return func(message)
        else:
            bot.reply_to(message, "❌ Lệnh này chỉ hoạt động trong một nhóm chat cụ thể.")
    return wrapper

@bot.message_handler(commands=['thamgiaapp'])
@private_chat_only
def start_handler(message):
    icon = get_user_icon(message.from_user.username or "User")
    bot.reply_to(message, f"{icon} *Chào bạn!*\n\n"
                            "/laykey — Lấy key mới (dùng để xác thực)\n"
                            "/key <key> — Nhập key để kích hoạt\n"
                            "/laytk — Tạo tài khoản mới\n\n"
                            "Mỗi ngày chỉ được tạo 1 tài khoản.\n"
                            "Key sẽ đổi vào lúc 00:00 mỗi ngày.", parse_mode="Markdown")

@bot.message_handler(commands=['laykey'])
@private_chat_only
def laykey_handler(message):
    user_id = message.from_user.id
    uid_str = str(user_id)
    key = generate_key(uid_str)

    # Invalidate the old key
    active_keys.pop(user_id, None)

    url_api = f"{API_KEY_VERIFY}?token={TOKEN_YEUMONEY}&format=json&url={API_KEY_PREFIX}{key}"

    try:
        r = requests.get(url_api, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success" and "shortenedUrl" in data:
                short_url = data["shortenedUrl"].replace("\\/", "/")

                now = datetime.now(VN_TZ)
                tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                time_left = tomorrow - now
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)

                keyboard = InlineKeyboardMarkup(row_width=2)
                keyboard.add(
                    InlineKeyboardButton("🚀 Vượt link", url=short_url),
                    InlineKeyboardButton("👑 Mua key VIP", url="https://hoangdaixu.x10.bz")
                )

                bot.reply_to(message,
                    f"🔑 App Free Mong Bạn Ủng Hộ 1 Link\n"
                    f"🔗 *Link rút gọn dành riêng cho bạn:*\n{short_url}\n\n"
                    f"⏳ *Key còn hiệu lực:* {hours} giờ {minutes} phút\n\n"
                    "Dùng lệnh:\n`/key <key>`\nđể nhập key và xác thực.",
                    parse_mode="Markdown",
                    reply_markup=keyboard)
            else:
                bot.reply_to(message, "❌ Lấy link rút gọn thất bại, vui lòng thử lại sau.")
        else:
            bot.reply_to(message, f"❌ Lỗi kết nối API lấy link: HTTP {r.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi gọi API lấy link: {str(e)}")



@bot.message_handler(commands=['key'])
@private_chat_only
def key_handler(message):
    user_id = message.from_user.id
    text = message.text.strip()
    parts = text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Vui lòng nhập key theo cú pháp: /key <key>")
        return
    user_key = parts[1]
    uid_str = str(user_id)
    key_correct = generate_key(uid_str)

    if user_key != key_correct:
        # Invalidate the key if the user attempts to use a wrong key
        active_keys.pop(user_id, None)
        bot.reply_to(message, "❌ Key bạn nhập không hợp lệ hoặc không khớp với key hiện tại.")
        return

    # Store the user's active key
    active_keys[user_id] = True
    bot.reply_to(message, "✅ Key hợp lệ và đã được kích hoạt.\nBạn có thể sử dụng /laytk để tạo tài khoản.")

@bot.message_handler(commands=['laytk'])
@private_chat_only
def laytk_handler(message):
    user_id = message.from_user.id

    # Check if the user has a valid key first
    if not active_keys.get(user_id):
        bot.reply_to(message, "❌ Bạn chưa có key hợp lệ hoặc key đã hết hạn. Vui lòng dùng `/laykey` để lấy key mới và xác thực lại.")
        return

    if user_created_today(user_id):
        bot.reply_to(message, "⚠️ Bạn chỉ được tạo 1 tài khoản mỗi ngày thôi nha!")
        return

    msg = bot.reply_to(message, "❓ Vui lòng *reply* tin nhắn này với số golike bạn muốn (1 hoặc 2):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_golike)

def process_golike(message):
    user_id = message.from_user.id
    # Double check key validity just in case
    if not active_keys.get(user_id):
        bot.reply_to(message, "❌ Key của bạn đã hết hạn. Vui lòng lấy key mới.")
        return

    golike = message.text.strip()
    if golike not in ["1", "2"]:
        msg = bot.reply_to(message, "❌ Vui lòng nhập số 1 hoặc 2.")
        bot.register_next_step_handler(msg, process_golike)
        return

    bot.reply_to(message, "⏳ Đang tạo tài khoản, vui lòng đợi...")

    username = generate_random_uid(8)
    password_raw = generate_random_string(5)
    uid_golike = generate_random_uid(19)
    balance = 100000

    payload = {
        "username": username,
        "password": password_raw,
        "balance": balance,
        "type": "pending",
        "ver": "7.5.7",
        "tiktok_lite_follow_video_node": "com.zhiliaoapp.musically.go:id/ds6",
        "golike": int(golike),
        "uid_golike": uid_golike
    }

    try:
        r = requests.post(API_CREATE_USER, json=payload, timeout=15)
        if r.status_code == 200:
            res = r.json()
            if res.get("status") == "success":
                api_username = res.get("username")
                api_password = res.get("password")

                save_user_to_db(message.from_user.id, api_username, api_password, uid_golike, int(golike), balance)
                icon = get_user_icon(api_username)
                bot.reply_to(message,
                    f"{icon} *Tạo tài khoản thành công!*\n\n"
                    f"Username: {api_username}\nPassword: {api_password}\nUID Golike: {uid_golike}\n"
                    f"Balance: {balance}\nGolike: {golike}",
                    parse_mode="Markdown")
            else:
                bot.reply_to(message, f"❌ Lỗi tạo tài khoản: {res.get('message', 'Không rõ lỗi')}")
        else:
            bot.reply_to(message, f"❌ Lỗi kết nối API tạo tài khoản: HTTP {r.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ Lỗi gọi API: {str(e)}")

# Gọi keep_alive
keep_alive()

# Vòng lặp giữ bot luôn chạy
while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        error_msg = traceback.format_exc()
        print("Bot bị lỗi nè:\n", error_msg)

        # Gửi log về Telegram
        try:
            bot.send_message(ADMIN_ID,
                             f"⚠️ Bot bị lỗi:\n\n<pre>{error_msg}</pre>",
                             parse_mode="HTML")
        except:
            pass

        time.sleep(0.1)  # Đợi 0s rồi thử chạy lại
