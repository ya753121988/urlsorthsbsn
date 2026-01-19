import os
import subprocess
import sys
import re
import logging
import requests

# --- ১. লাইব্রেরি অটো ইনস্টল সিস্টেম ---
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

# --- ২. কনফিগারেশন (আপনার দেওয়া তথ্য অনুযায়ী) ---
API_TOKEN = '8488533482:AAE4JBLU8I1cdboE4_o_qwb3yDe_-PA_ehU'
DOMAIN = "urlbotsot.vercel.app"
API_KEY = "akashdeveloper"
ADMIN_USERNAME = "AkashDeveloperBot"
CHANNEL_USERNAME = "yabotz"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# লিংক শনাক্ত করার Regex
URL_PATTERN = r'https?://[^\s]+'

# --- ৩. এপিআই শর্টনার ফাংশন ---
def get_short_url(long_url):
    try:
        # আপনার এপিআই ফরম্যাট অনুযায়ী
        api_endpoint = f"https://{DOMAIN}/api?api={API_KEY}&url={long_url}"
        response = requests.get(api_endpoint, timeout=15)
        
        if response.status_code == 200:
            # যদি এপিআই শুধু টেক্সট পাঠায়
            short_link = response.text.strip()
            # যদি ভুলবশত JSON আসে তবে তা হ্যান্ডেল করা
            if "{" in short_link:
                try:
                    res_json = response.json()
                    return res_json.get('shorted') or res_json.get('url') or long_url
                except:
                    return long_url
            return short_link
    except:
        return None
    return None

# --- ৪. স্টার্ট কমান্ড হ্যান্ডলার ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user = message.from_user
    
    # বাটন তৈরি
    keyboard = InlineKeyboardMarkup(row_width=2)
    admin_btn = InlineKeyboardButton("👨‍💻 Admin Contact", url=f"https://t.me/{ADMIN_USERNAME}")
    dev_btn = InlineKeyboardButton("📢 Developer Channel", url=f"https://t.me/{CHANNEL_USERNAME}")
    keyboard.add(admin_btn, dev_btn)

    welcome_text = (
        f"👋 আসসালামু আলাইকুম, {user.full_name}!\n\n"
        f"🆔 আপনার আইডি: `{user.id}`\n"
        f"👤 প্রোফাইল লিংক: [Click Here](tg://user?id={user.id})\n\n"
        "🔗 যেকোনো পোস্ট পাঠান যাতে লিংক আছে, আমি সব শর্ট করে রিপ্লাই দেব।"
    )

    try:
        # ইউজারের প্রোফাইল পিকচার সংগ্রহ
        user_photos = await bot.get_user_profile_photos(user.id)
        if user_photos.total_count > 0:
            photo_id = user_photos.photos[0][-1].file_id
            await message.reply_photo(photo_id, caption=welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await message.reply(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

# --- ৫. পোস্ট হ্যান্ডলার (লিংক শর্ট করার জন্য) ---
@dp.message_handler(content_types=['text'])
async def process_post(message: types.Message):
    input_text = message.text
    urls = re.findall(URL_PATTERN, input_text)

    if not urls:
        # যদি কোনো লিংক না থাকে তবে কোনো রিপ্লাই দিবে না
        return

    wait_msg = await message.answer("⚡ আপনার পোস্টের লিংকগুলো শর্ট করা হচ্ছে, দয়া করে অপেক্ষা করুন...")
    
    new_text = input_text
    success_count = 0

    for url in urls:
        # শর্ট লিংক তৈরি
        short_link = get_short_url(url)
        if short_link and "http" in short_link:
            new_text = new_text.replace(url, short_link)
            success_count += 1

    await wait_msg.delete()

    if success_count > 0:
        await message.answer(f"✅ **Shortened Post:**\n\n{new_text}", disable_web_page_preview=True)
    else:
        await message.answer("❌ এপিআই থেকে লিংক পাওয়া যায়নি। দয়া করে আপনার এপিআই বা ডোমেন চেক করুন।")

if __name__ == '__main__':
    print("বটটি সফলভাবে চালু হয়েছে...")
    executor.start_polling(dp, skip_updates=True)
