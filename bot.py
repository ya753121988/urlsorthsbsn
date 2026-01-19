import os
import re
import logging
import asyncio
import requests
import subprocess
import sys

# --- লাইব্রেরি অটো ইনস্টল সিস্টেম ---
def install_requirements():
    try:
        import aiogram
        import requests
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram", "requests"])

install_requirements()

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- কনফিগারেশন ---
API_TOKEN = '8488533482:AAE4JBLU8I1cdboE4_o_qwb3yDe_-PA_ehU'
DOMAIN = "urlbotsot.vercel.app"
API_KEY = "akashdeveloper"
ADMIN_USERNAME = "AkashDeveloperBot"
CHANNEL_USERNAME = "yabotz"

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)

# বট ও ডিসপ্যাচার (aiogram 3.x)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

URL_PATTERN = r'https?://[^\s]+'

# --- এপিআই শর্টনার ফাংশন ---
def get_short_url(long_url):
    try:
        api_endpoint = f"https://{DOMAIN}/api?api={API_KEY}&url={long_url}"
        response = requests.get(api_endpoint, timeout=15)
        if response.status_code == 200:
            res_text = response.text.strip()
            # এপিআই থেকে শুধু লিংকটি বের করার চেষ্টা
            match = re.search(URL_PATTERN, res_text)
            return match.group(0) if match else res_text
    except:
        return None
    return None

# --- স্টার্ট কমান্ড হ্যান্ডলার ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    
    # বাটন তৈরি
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍💻 Admin", url=f"https://t.me/{ADMIN_USERNAME}"),
            InlineKeyboardButton(text="📢 Channel", url=f"https://t.me/{CHANNEL_USERNAME}")
        ]
    ])

    welcome_text = (
        f"👋 আসসালামু আলাইকুম, {user.full_name}!\n\n"
        f"🆔 আপনার আইডি: `{user.id}`\n"
        f"👤 প্রোফাইল: [Click Here](tg://user?id={user.id})\n\n"
        "🔗 যেকোনো লিংক বা পোস্ট পাঠান, আমি সব শর্ট করে দেব।"
    )

    try:
        # ইউজারের প্রোফাইল ফটো নেওয়া
        photos = await bot.get_user_profile_photos(user_id=user.id, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]
            await message.answer_photo(photo.file_id, caption=welcome_text, reply_markup=builder, parse_mode="Markdown")
        else:
            await message.answer(welcome_text, reply_markup=builder, parse_mode="Markdown")
    except:
        await message.answer(welcome_text, reply_markup=builder, parse_mode="Markdown")

# --- পোস্ট হ্যান্ডলার (লিংক শর্ট করার জন্য) ---
@dp.message(F.text)
async def handle_links(message: types.Message):
    input_text = message.text
    urls = re.findall(URL_PATTERN, input_text)

    if not urls:
        return

    status = await message.answer("🔄 প্রসেসিং হচ্ছে...")
    
    new_text = input_text
    is_changed = False

    for url in urls:
        # শর্ট লিংক তৈরি
        short = get_short_url(url)
        if short and "http" in short:
            new_text = new_text.replace(url, short)
            is_changed = True

    await status.delete()

    if is_changed:
        await message.answer(f"✅ **Shortened Post:**\n\n{new_text}", disable_web_page_preview=True)
    else:
        await message.answer("❌ আপনার এপিআই থেকে কোনো লিংক পাওয়া যায়নি। দয়া করে ডোমেন বা এপিআই কি চেক করুন।")

# মেইন ফাংশন
async def main():
    print("বট সফলভাবে চালু হয়েছে (Aiogram 3.x)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
