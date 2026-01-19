import os
import sys
import subprocess

# ==========================================
# ১. অটোমেটিক লাইব্রেরি ইন্সটলার
# ==========================================
def auto_install():
    packages = ["aiogram", "aiohttp"]
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

auto_install()

import logging
import json
import re
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message

# ==========================================
# ২. কনফিগারেশন
# ==========================================
API_TOKEN = '8488533482:AAHfM7dS8CjZ1bL541BvOLOrfIWjSu0VJJs'  # <--- আপনার টোকেন দিন
DEFAULT_DOMAIN = 'urlbotsot.vercel.app'     # আপনার ডোমেইন
DATABASE_FILE = 'bot_db.json'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ডাটাবেস হ্যান্ডলিং ---
def get_db():
    if not os.path.exists(DATABASE_FILE):
        return {}
    with open(DATABASE_FILE, 'r') as f:
        try:
            return json.load(f)
        except: return {}

def save_db(data):
    with open(DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- শর্টনার ফাংশন ---
async def shorten_url(api_key, long_url):
    api_url = f"https://{DEFAULT_DOMAIN}/api?api={api_key}&url={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as response:
                res = await response.json()
                if res.get('status') == 'success':
                    return res.get('shortenedUrl')
                return long_url
    except: return long_url

# ==========================================
# ৩. কমান্ড হ্যান্ডলারস (এগুলো সবার আগে থাকবে)
# ==========================================

@dp.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    text = (
        f"👋 **স্বাগতম, {user.full_name}!**\n\n"
        f"🆔 আপনার আইডি: `{user.id}`\n\n"
        "📜 **বট কমান্ডসমূহ:**\n"
        "🔹 `/setapi API_KEY` - এপিআই সেট করুন\n"
        "🔹 `/setfooter Name | Link` - ফুটার যোগ করুন\n"
        "🔹 `/listfooters` - ফুটার লিস্ট দেখুন\n"
        "🔹 `/delfooter ID` - ফুটার ডিলিট করুন\n\n"
        "📢 যে কোনো পোস্ট আমাকে পাঠান, আমি লিংক শর্ট করে সাজিয়ে দেব।"
    )
    await message.reply(text, parse_mode="Markdown")

@dp.message(Command("setapi"))
async def set_api(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ ফরম্যাট: `/setapi আপনার_কি`")
    
    uid = str(message.from_user.id)
    db = get_db()
    if uid not in db: db[uid] = {"api": "", "footers": []}
    db[uid]["api"] = args[1]
    save_db(db)
    await message.reply("✅ API Key সফলভাবে সেভ হয়েছে!")

@dp.message(Command("setfooter"))
async def add_footer(message: Message):
    if "|" not in message.text:
        return await message.reply("❌ ফরম্যাট: `/setfooter নাম | লিংক`")
    
    content = message.text.replace("/setfooter", "").strip()
    name, link = content.split("|", 1)
    
    uid = str(message.from_user.id)
    db = get_db()
    if uid not in db: db[uid] = {"api": "", "footers": []}
    if "footers" not in db[uid]: db[uid]["footers"] = []
    
    db[uid]["footers"].append({"name": name.strip(), "link": link.strip()})
    save_db(db)
    await message.reply(f"✅ ফুটার যোগ হয়েছে: **{name.strip()}**")

@dp.message(Command("listfooters"))
async def list_footers(message: Message):
    uid = str(message.from_user.id)
    db = get_db()
    footers = db.get(uid, {}).get("footers", [])
    
    if not footers:
        return await message.reply("📭 কোনো ফুটার সেট করা নেই।")
    
    msg = "📋 **আপনার ফুটারসমূহ:**\n\n"
    for i, f in enumerate(footers, 1):
        msg += f"{i}. {f['name']} - {f['link']}\n"
    msg += "\nডিলিট করতে লিখুন: `/delfooter ID`"
    await message.reply(msg, disable_web_page_preview=True)

@dp.message(Command("delfooter"))
async def del_footer(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ ফরম্যাট: `/delfooter ID`")
    
    uid = str(message.from_user.id)
    db = get_db()
    footers = db.get(uid, {}).get("footers", [])
    
    try:
        idx = int(args[1]) - 1
        if 0 <= idx < len(footers):
            removed = footers.pop(idx)
            db[uid]["footers"] = footers
            save_db(db)
            await message.reply(f"🗑 ডিলিট হয়েছে: **{removed['name']}**")
        else:
            await message.reply("❌ ভুল আইডি!")
    except:
        await message.reply("❌ আইডি সংখ্যায় দিন (যেমন: /delfooter 1)")

# ==========================================
# ৪. মেসেজ প্রসেসিং হ্যান্ডলার (এটি সবার নিচে থাকবে)
# ==========================================

@dp.message(F.text | F.caption)
async def process_message(message: Message):
    # যদি মেসেজটি কমান্ড হয় (যেমন /start), তবে এটি প্রসেস করবে না
    if message.text and message.text.startswith('/'):
        return

    uid = str(message.from_user.id)
    db = get_db()
    user_data = db.get(uid)

    if not user_data or not user_data.get("api"):
        return await message.reply("⚠️ আগে `/setapi` কমান্ড দিয়ে API কি সেট করুন।")

    api_key = user_data["api"]
    footers = user_data.get("footers", [])
    original_text = message.text or message.caption or ""
    
    urls = re.findall(r'(https?://[^\s]+)', original_text)
    
    if urls:
        waiting = await message.reply("⏳ লিংক শর্ট করা হচ্ছে...")
        new_text = original_text
        for url in urls:
            if DEFAULT_DOMAIN in url: continue
            shorted = await shorten_url(api_key, url)
            new_text = new_text.replace(url, shorted)
        await waiting.delete()
    else:
        new_text = original_text

    # ফুটার যোগ করা
    if footers:
        new_text += "\n\n" + "━━━━━━━━━━━━━━\n"
        for f in footers:
            new_text += f"📢 [{f['name']}]({f['link']})\n"

    try:
        if message.photo:
            await message.answer_photo(message.photo[-1].file_id, caption=new_text, parse_mode="Markdown")
        elif message.video:
            await message.answer_video(message.video.file_id, caption=new_text, parse_mode="Markdown")
        else:
            await message.answer(new_text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await message.answer(f"এরর: {str(e)}")

# বট চালু করা
async def main():
    print("🤖 বট সফলভাবে চালু হয়েছে...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
