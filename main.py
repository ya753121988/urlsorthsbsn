import sys
import subprocess
import os
import json
import re
import asyncio
import logging

# ==========================================
# ১. অটো লাইব্রেরি ইন্সটলার (যা যা লাগবে সব অটো হবে)
# ==========================================
def install_dependencies():
    required = {'aiogram', 'aiohttp'}
    for package in required:
        try:
            __import__(package)
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
import aiohttp

# ==========================================
# ২. কনফিগারেশন (এখানে আপনার টোকেন দিন)
# ==========================================
API_TOKEN = '8488533482:AAHfM7dS8CjZ1bL541BvOLOrfIWjSu0VJJs'  # <--- এখানে বট টোকেন বসান
DEFAULT_DOMAIN = 'urlbotsot.vercel.app'     # আপনার শর্টনার ডোমেইন
DB_FILE = 'database.json'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ==========================================
# ৩. ডাটাবেস ম্যানেজমেন্ট (JSON ফাইল)
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# ==========================================
# ৪. এপিআই শর্টনার ফাংশন
# ==========================================
async def get_short_url(api, long_url):
    api_url = f"https://{DEFAULT_DOMAIN}/api?api={api}&url={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as resp:
                data = await resp.json()
                if data.get('status') == 'success':
                    return data.get('shortenedUrl')
                return long_url
    except:
        return long_url

# ==========================================
# ৫. বটের কমান্ডসমূহ
# ==========================================

# /start কমান্ড
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    text = (
        f"👋 **স্বাগতম, {user.full_name}!**\n\n"
        f"🆔 আপনার আইডি: `{user.id}`\n"
        f"👤 ইউজারনেম: @{user.username}\n\n"
        "📜 **বট কমান্ডসমূহ:**\n"
        "🔹 `/setapi API_KEY` - শর্টনার সাইটের এপিআই সেট করুন।\n"
        "🔹 `/setfooter Name | Link` - নতুন ফুটার এড করুন।\n"
        "🔹 `/listfooters` - আপনার সব ফুটার দেখুন।\n"
        "🔹 `/delfooter ID` - নির্দিষ্ট ফুটার ডিলিট করুন।\n\n"
        "📢 **কিভাবে কাজ করে?**\n"
        "যেকোনো পোস্ট (টেক্সট, ফটো, ভিডিও) আমাকে পাঠান, আমি সব লিংক অটো শর্ট করে ফুটারসহ রিপ্লাই দেব।"
    )
    await message.reply(text, parse_mode="Markdown")

# API সেট করা
@dp.message(Command("setapi"))
async def cmd_setapi(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ ভুল ফরম্যাট! লিখুন: `/setapi your_api_key`", parse_mode="Markdown")
    
    uid = str(message.from_user.id)
    db = load_db()
    if uid not in db: db[uid] = {"api": "", "footers": []}
    db[uid]["api"] = args[1]
    save_db(db)
    await message.reply("✅ **API Key সফলভাবে সেট করা হয়েছে!**")

# ফুটার সেট করা
@dp.message(Command("setfooter"))
async def cmd_setfooter(message: Message):
    content = message.text.replace("/setfooter", "").strip()
    if "|" not in content:
        return await message.reply("❌ ভুল ফরম্যাট! লিখুন: `/setfooter নাম | লিংক`", parse_mode="Markdown")
    
    name, link = content.split("|", 1)
    uid = str(message.from_user.id)
    db = load_db()
    if uid not in db: db[uid] = {"api": "", "footers": []}
    
    db[uid]["footers"].append({"name": name.strip(), "link": link.strip()})
    save_db(db)
    await message.reply(f"✅ **নতুন ফুটার যোগ হয়েছে:**\n`{name.strip()}`")

# ফুটার লিস্ট
@dp.message(Command("listfooters"))
async def cmd_listfooters(message: Message):
    uid = str(message.from_user.id)
    db = load_db()
    footers = db.get(uid, {}).get("footers", [])
    
    if not footers:
        return await message.reply("📭 আপনার কোনো ফুটার সেট করা নেই।")
    
    msg = "📋 **আপনার ফুটারসমূহ:**\n\n"
    for i, f in enumerate(footers, 1):
        msg += f"{i}. {f['name']} - {f['link']}\n"
    msg += "\nডিলিট করতে লিখুন: `/delfooter ID`"
    await message.reply(msg, disable_web_page_preview=True)

# ফুটার ডিলিট
@dp.message(Command("delfooter"))
async def cmd_delfooter(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ লিখুন: `/delfooter ID`")
    
    uid = str(message.from_user.id)
    db = load_db()
    footers = db.get(uid, {}).get("footers", [])
    
    try:
        idx = int(args[1]) - 1
        if 0 <= idx < len(footers):
            removed = footers.pop(idx)
            db[uid]["footers"] = footers
            save_db(db)
            await message.reply(f"🗑 **ডিলিট হয়েছে:** {removed['name']}")
        else:
            await message.reply("❌ ভুল আইডি! লিস্ট চেক করুন।")
    except:
        await message.reply("❌ আইডি সংখ্যায় হতে হবে।")

# ==========================================
# ৬. পোস্ট প্রসেসিং (লিংক শর্ট করা ও রিপ্লাই দেওয়া)
# ==========================================

@dp.message(F.text | F.caption)
async def handle_post(message: Message):
    uid = str(message.from_user.id)
    db = load_db()
    
    # চেক ইউজার এপিআই
    user_data = db.get(uid)
    if not user_data or not user_data.get("api"):
        return await message.reply("⚠️ আগে `/setapi` কমান্ড দিয়ে আপনার API Key সেট করুন।")
    
    api_key = user_data["api"]
    footers = user_data.get("footers", [])
    
    original_text = message.text or message.caption or ""
    urls = re.findall(r'(https?://[^\s]+)', original_text)
    
    # লিংক থাকলে শর্ট করবে
    if urls:
        status_msg = await message.reply("⏳ প্রসেসিং হচ্ছে...")
        new_text = original_text
        for url in urls:
            if DEFAULT_DOMAIN in url: continue
            short = await get_short_url(api_key, url)
            new_text = new_text.replace(url, short)
        await status_msg.delete()
    else:
        new_text = original_text

    # ফুটার যোগ করা (সুন্দর স্টাইলে)
    if footers:
        new_text += "\n\n" + "━" * 15 + "\n"
        for f in footers:
            new_text += f"📢 [{f['name']}]({f['link']})\n"

    # আউটপুট (ফটো/ভিডিও/টেক্সট)
    try:
        if message.photo:
            await message.answer_photo(message.photo[-1].file_id, caption=new_text, parse_mode="Markdown")
        elif message.video:
            await message.answer_video(message.video.file_id, caption=new_text, parse_mode="Markdown")
        else:
            await message.answer(new_text, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await message.answer(f"❌ এরর: {str(e)}")

# ==========================================
# ৭. বট রান করা
# ==========================================
async def main():
    print("🚀 বট সফলভাবে চালু হয়েছে!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 বট বন্ধ করা হয়েছে।")
