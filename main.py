import os
import subprocess
import sys
import re
import logging

# --- ১. লাইব্রেরি অটো ইনস্টল সিস্টেম ---
def install_requirements():
    required_packages = ['aiogram==2.25.1', 'requests']
    for package in required_packages:
        try:
            __import__(package.split('==')[0])
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_requirements()

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# --- কনফিগারেশন ---
API_TOKEN = '8488533482:AAE4JBLU8I1cdboE4_o_qwb3yDe_-PA_ehU'  # @BotFather থেকে পাওয়া টোকেন দিন
DOMAIN = "urlbotsot.vercel.app"
API_KEY = "akashdeveloper"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# লিংক খুঁজে বের করার জন্য Regex
URL_PATTERN = r'(https?://[^\s]+)'

# লিংক শর্ট করার ফাংশন
def get_short_url(long_url):
    try:
        api_url = f"https://{DOMAIN}/api?api={API_KEY}&url={long_url}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    return long_url

# /start কমান্ড হ্যান্ডলার
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user = message.from_user
    
    # বাটন সেটআপ
    keyboard = InlineKeyboardMarkup(row_width=2)
    admin_btn = InlineKeyboardButton("👨‍💻 Admin Contact", url="https://t.me/AkashDeveloperBot") # পরিবর্তন করুন
    dev_btn = InlineKeyboardButton("📢 Developer Channel", url="https://t.me/yabotz") # পরিবর্তন করুন
    keyboard.add(admin_btn, dev_btn)

    text = (
        f"👋 আসসালামু আলাইকুম, {user.full_name}!\n\n"
        f"🆔 আইডি: `{user.id}`\n"
        f"👤 প্রোফাইল: [ক্লিক করুন](tg://user?id={user.id})\n\n"
        "🔗 আমাকে যেকোনো পোস্ট বা লিংক পাঠান, আমি সব লিংক ছোট করে দেব।"
    )

    try:
        # ইউজারের প্রোফাইল ফটো নেওয়া
        photos = await message.from_user.get_profile_photos()
        if photos.total_count > 0:
            # প্রথম ফটোর সবচেয়ে বড় সাইজ পাঠানো
            await message.reply_photo(photos.photos[0][-1].file_id, caption=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")

# যেকোনো টেক্সট বা পোস্ট হ্যান্ডলার
@dp.message_handler(content_types=['text'])
async def process_links(message: types.Message):
    input_text = message.text
    urls = re.findall(URL_PATTERN, input_text)

    if not urls:
        return # কোনো লিংক না থাকলে কিছু করবে না

    wait_msg = await message.answer("⏳ আপনার পোস্টের লিংকগুলো শর্ট করা হচ্ছে...")
    
    final_text = input_text
    for url in urls:
        short = get_short_url(url)
        final_text = final_text.replace(url, short)

    await wait_msg.delete()
    await message.answer(f"✅ **শর্ট করা পোস্ট:**\n\n{final_text}", disable_web_page_preview=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
