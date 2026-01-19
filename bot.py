import os
import subprocess
import sys
import re
import logging
import requests

# লাইব্রেরি অটো ইনস্টল
def install_dependencies():
    packages = ['aiogram==2.25.1', 'requests']
    for package in packages:
        try:
            __import__(package.split('==')[0])
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- কনফিগারেশন ---
API_TOKEN = '8488533482:AAE4JBLU8I1cdboE4_o_qwb3yDe_-PA_ehU'
DOMAIN = "urlbotsot.vercel.app"
API_KEY = "akashdeveloper"
ADMIN_USERNAME = "AkashDeveloperBot"
CHANNEL_USERNAME = "yabotz"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

URL_PATTERN = r'https?://[^\s]+'

# --- এপিআই কল করার উন্নত ফাংশন ---
def get_short_url(long_url):
    try:
        # অনেক সময় এপিআই এন্ডপয়েন্ট /api এর বদলে শুধু / হতে পারে। 
        # আপাতত আপনার দেওয়া ফরম্যাটই ব্যবহার করছি।
        api_endpoint = f"https://{DOMAIN}/api?api={API_KEY}&url={long_url}"
        
        response = requests.get(api_endpoint, timeout=20)
        
        if response.status_code == 200:
            res_text = response.text.strip()
            
            # চেক করা হচ্ছে এটি JSON কি না
            try:
                data = response.json()
                # সম্ভাব্য সব ধরণের Key চেক করা হচ্ছে (developer ভেদে আলাদা হয়)
                return data.get('shorted') or data.get('short') or data.get('url') or data.get('shortenedUrl') or res_text
            except:
                # যদি সরাসরি টেক্সট লিংক পাঠায়
                return res_text
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

# --- স্টার্ট কমান্ড ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user = message.from_user
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👨‍💻 Admin", url=f"https://t.me/{ADMIN_USERNAME}"),
        InlineKeyboardButton("📢 Channel", url=f"https://t.me/{CHANNEL_USERNAME}")
    )

    text = (f"👋 হাই {user.full_name}!\n"
            f"🆔 আইডি: `{user.id}`\n\n"
            "আমাকে যেকোনো লিংক বা পোস্ট পাঠান, আমি সব শর্ট করে দেব।")

    try:
        photos = await message.from_user.get_profile_photos()
        if photos.total_count > 0:
            await message.reply_photo(photos.photos[0][-1].file_id, caption=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")

# --- মেসেজ হ্যান্ডলার ---
@dp.message_handler(content_types=['text'])
async def handle_all_messages(message: types.Message):
    input_text = message.text
    urls = re.findall(URL_PATTERN, input_text)

    if not urls:
        return

    status_msg = await message.answer("🔄 প্রসেসিং হচ্ছে...")
    
    final_text = input_text
    found_any = False

    for url in urls:
        short_link = get_short_url(url)
        
        # যদি লিংকটি সঠিক হয় (http আছে এমন)
        if short_link and "http" in short_link:
            final_text = final_text.replace(url, short_link)
            found_any = True
        else:
            # যদি এপিআই কাজ না করে তবে এরর দেখাবে (Debug)
            await message.answer(f"❌ লিংক শর্ট করতে সমস্যা হয়েছে!\nএপিআই থেকে আসা উত্তর: `{short_link}`")
            await status_msg.delete()
            return

    await status_msg.delete()
    if found_any:
        await message.answer(f"✅ **Shortened Post:**\n\n{final_text}", disable_web_page_preview=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
