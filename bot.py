import os
import re
import sys
import logging
import asyncio
import requests
import subprocess

# --- ১. লাইব্রেরি অটো ইনস্টল সিস্টেম ---
def install_dependencies():
    packages = ['aiogram', 'requests']
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- ২. কনফিগারেশন (আপনার দেওয়া তথ্য) ---
API_TOKEN = '8488533482:AAE4JBLU8I1cdboE4_o_qwb3yDe_-PA_ehU'
DOMAIN = "urlbotsot.vercel.app"
API_KEY = "akashdeveloper"
ADMIN_USERNAME = "AkashDeveloperBot"
CHANNEL_USERNAME = "yabotz"

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)

# বট ও ডিসপ্যাচার ইনিশিয়ালাইজেশন
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ইউআরএল শনাক্ত করার জন্য Regex (http এবং https দুইটাই ধরবে)
URL_PATTERN = r'https?://[^\s]+'

# --- ৩. এপিআই শর্টনার ফাংশন (হিবিজিবি মুক্ত) ---
def get_clean_short_url(long_url):
    try:
        api_endpoint = f"https://{DOMAIN}/api?api={API_KEY}&url={long_url}"
        response = requests.get(api_endpoint, timeout=15)
        
        if response.status_code == 200:
            raw_res = response.text.strip()
            # এপিআই-এর রেজাল্ট থেকে শুধু ক্লিন ইউআরএল-টি ছেঁকে নেওয়া
            clean_match = re.search(URL_PATTERN, raw_res)
            if clean_match:
                return clean_match.group(0) # শুধু লিংকটি রিটার্ন করবে
            return raw_res
    except Exception as e:
        print(f"API Error: {e}")
    return None

# --- ৪. স্টার্ট কমান্ড হ্যান্ডলার ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    
    # বাটন সেটআপ
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨‍💻 Admin Contact", url=f"https://t.me/{ADMIN_USERNAME}"),
            InlineKeyboardButton(text="📢 Developer Channel", url=f"https://t.me/{CHANNEL_USERNAME}")
        ]
    ])

    welcome_text = (
        f"👋 আসসালামু আলাইকুম, {user.full_name}!\n\n"
        f"🆔 আপনার আইডি: `{user.id}`\n"
        f"👤 আপনার প্রোফাইল: [এখানে ক্লিক করুন](tg://user?id={user.id})\n\n"
        "🔗 আমাকে যেকোনো **টেক্সট, ফটো, ভিডিও, বা অডিও** পাঠান।\n"
        "আমি সেগুলোর লিংক শর্ট করে ক্লিন ভাবে পুনরায় পাঠিয়ে দেব।"
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

# --- ৫. মেইন প্রসেসিং হ্যান্ডলার (টেক্সট ও মিডিয়া রি-ডাইরেক্ট) ---
@dp.message(F.content_type.in_({'text', 'photo', 'video', 'audio', 'document', 'animation', 'voice'}))
async def handle_everything(message: types.Message):
    # টেক্সট অথবা মিডিয়ার ক্যাপশন সংগ্রহ
    original_text = message.text if message.text else message.caption
    
    if not original_text:
        return # কোনো টেক্সট বা ক্যাপশন না থাকলে কিছু করবে না

    # টেক্সটে কোনো ইউআরএল আছে কি না চেক করা
    urls = re.findall(URL_PATTERN, original_text)
    if not urls:
        return # ইউআরএল না থাকলে রিপ্লাই দিবে না

    status = await message.answer("🔄 প্রসেসিং হচ্ছে, অপেক্ষা করুন...")
    
    new_text = original_text
    is_shortened = False

    for url in urls:
        short_link = get_clean_short_url(url)
        if short_link and "http" in short_link:
            new_text = new_text.replace(url, short_link)
            is_shortened = True

    await status.delete()

    if is_shortened:
        # রি-ডাইরেক্ট ফিচার: মিডিয়া হলে মিডিয়াসহ, টেক্সট হলে শুধু টেক্সট পাঠাবে
        try:
            await message.copy_to(
                chat_id=message.chat.id,
                caption=new_text,
                reply_markup=None # চাইলে এখানেও বাটন দিতে পারেন
            )
        except Exception as e:
            await message.answer(f"✅ **Shortened Post:**\n\n{new_text}", disable_web_page_preview=True)
    else:
        await message.answer("❌ এপিআই থেকে সঠিক লিংক পাওয়া যায়নি।")

# --- ৬. রানার ---
async def main():
    print("বটটি সফলভাবে চালু হয়েছে...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("বট বন্ধ করা হয়েছে।")
