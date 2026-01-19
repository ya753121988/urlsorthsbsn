import os
import re
import logging
import requests
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

def get_short_url(long_url):
    try:
        # এপিআই রিকোয়েস্ট
        api_endpoint = f"https://{DOMAIN}/api?api={API_KEY}&url={long_url}"
        response = requests.get(api_endpoint, timeout=15)
        
        if response.status_code == 200:
            res_text = response.text.strip()
            # যদি এপিআই শুধু একটা লিংক দেয়, তবে সেটা নেবে
            # যদি ভুল করে পুরো টেক্সট পাঠায় তবে প্রথম লিংকটা ফিল্টার করবে
            short_match = re.search(URL_PATTERN, res_text)
            if short_match:
                return short_match.group(0)
            return res_text
    except:
        return None
    return None

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user = message.from_user
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👨‍💻 Admin", url=f"https://t.me/{ADMIN_USERNAME}"),
        InlineKeyboardButton("📢 Channel", url=f"https://t.me/{CHANNEL_USERNAME}")
    )

    text = f"👋 হাই {user.full_name}!\nআইডি: `{user.id}`\nযেকোনো লিংক পাঠান আমি শর্ট করে দেব।"

    try:
        photos = await message.from_user.get_profile_photos()
        if photos.total_count > 0:
            await message.reply_photo(photos.photos[0][-1].file_id, caption=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message_handler(content_types=['text'])
async def handle_msg(message: types.Message):
    urls = re.findall(URL_PATTERN, message.text)
    if not urls: return

    wait = await message.answer("🔄 শর্ট করা হচ্ছে...")
    new_text = message.text

    for url in urls:
        short = get_short_url(url)
        if short and "http" in short:
            new_text = new_text.replace(url, short)

    await wait.delete()
    await message.answer(f"✅ **Shortened Post:**\n\n{new_text}", disable_web_page_preview=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
