import os
import subprocess
import sys
import re
import logging
import requests

# --- ১. লাইব্রেরি অটো ইনস্টল সিস্টেম ---
def install_requirements():
    required_packages = ['aiogram==2.25.1', 'requests']
    for package in required_packages:
        try:
            __import__(package.split('==')[0])
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- ২. কনফিগারেশন (সঠিকভাবে চেক করুন) ---
API_TOKEN = '8488533482:AAE4JBLU8I1cdboE4_o_qwb3yDe_-PA_ehU'  # @BotFather থেকে পাওয়া টোকেন দিন
DOMAIN = "urlbotsot.vercel.app"
API_KEY = "akashdeveloper"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# লিংক শনাক্ত করার Regex
URL_PATTERN = r'https?://[^\s]+'

# --- ৩. এপিআই থেকে লিংক শর্ট করার ফাংশন ---
def get_short_url(long_url):
    try:
        # আপনার এপিআই এন্ডপয়েন্ট অনুযায়ী ইউআরএল তৈরি
        api_endpoint = f"https://{DOMAIN}/api?api={API_KEY}&url={long_url}"
        response = requests.get(api_endpoint, timeout=15)
        
        if response.status_code == 200:
            # যদি এপিআই JSON ডাটা পাঠায়
            try:
                res_json = response.json()
                # সম্ভাব্য কি (Key) গুলো চেক করছে
                return res_json.get('shorted') or res_json.get('short_url') or res_json.get('url')
            except:
                # যদি এপিআই সরাসরি শুধু টেক্সট পাঠায়
                return response.text.strip()
        else:
            return f"Error: Status Code {response.status_code}"
    except Exception as e:
        return None

# --- ৪. স্টার্ট কমান্ড ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user = message.from_user
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    admin_btn = InlineKeyboardButton("👨‍💻 Admin", url="https://t.me/YourUsername")
    dev_btn = InlineKeyboardButton("📢 Channel", url="https://t.me/YourChannel")
    keyboard.add(admin_btn, dev_btn)

    text = (
        f"👋 আসসালামু আলাইকুম, {user.full_name}!\n\n"
        f"🆔 আইডি: `{user.id}`\n"
        f"👤 প্রোফাইল: [Click Here](tg://user?id={user.id})\n\n"
        "🔗 যেকোনো পোস্ট বা লিংক পাঠান, আমি শর্ট করে দিচ্ছি।"
    )

    try:
        photos = await message.from_user.get_profile_photos()
        if photos.total_count > 0:
            await message.reply_photo(photos.photos[0][-1].file_id, caption=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")

# --- ৫. মেইন লিংক শর্টনার লজিক ---
@dp.message_handler(content_types=['text'])
async def process_post(message: types.Message):
    input_text = message.text
    urls = re.findall(URL_PATTERN, input_text)

    if not urls:
        return # কোনো লিংক না থাকলে রিপ্লাই দিবে না

    wait_msg = await message.answer("⚡ শর্ট করা হচ্ছে...")
    
    new_text = input_text
    success = False

    for url in urls:
        short_link = get_short_url(url)
        if short_link and "http" in short_link:
            new_text = new_text.replace(url, short_link)
            success = True

    await wait_msg.delete()

    if success:
        await message.answer(f"✅ **Shortened Post:**\n\n{new_text}", disable_web_page_preview=True)
    else:
        await message.answer("❌ দুঃখিত! এপিআই থেকে লিংক পাওয়া যাচ্ছে না। আপনার API Key বা Domain চেক করুন।")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
