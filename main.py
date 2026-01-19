import os
import sys
import subprocess
import logging
import json
import re
import asyncio

# ১. অটোমেটিক লাইব্রেরি ইন্সটলার (আপনার কিছু করা লাগবে না)
def install_libs():
    libs = ["aiogram", "aiohttp"]
    for lib in libs:
        try:
            __import__(lib)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_libs()

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
import aiohttp

# ২. আপনার তথ্য এখানে দিন
API_TOKEN = '8488533482:AAHfM7dS8CjZ1bL541BvOLOrfIWjSu0VJJs'  # <--- টোকেন এখানে দিন
DEFAULT_DOMAIN = 'urlbotsot.vercel.app'     # আপনার শর্টনার ডোমেইন
DB_FILE = 'database.json'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ৩. ডাটাবেস ফাংশন (JSON)
def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r') as f:
        try: return json.load(f)
        except: return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# ৪. লিংক শর্টনার ফাংশন
async def shorten(api, url):
    api_url = f"https://{DEFAULT_DOMAIN}/api?api={api}&url={url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as resp:
                data = await resp.json()
                if data.get('status') == 'success':
                    return data.get('shortenedUrl')
                return url
    except: return url

# ==========================================
# ৫. কমান্ড হ্যান্ডলার (এগুলো ফিক্স করা হয়েছে)
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        f"👋 **হ্যালো {message.from_user.full_name}!**\n\n"
        "বটটি ব্যবহার করতে নিচের কমান্ডগুলো দেখুন:\n\n"
        "🔹 `/setapi API_KEY` - শর্টনার সাইটের API সেট করুন\n"
        "🔹 `/setfooter নাম | লিংক` - নতুন ফুটার এড করুন\n"
        "🔹 `/listfooters` - সব ফুটার এবং তাদের **ID** দেখুন\n"
        "🔹 `/delfooter ID` - আইডি দিয়ে ফুটার ডিলিট করুন\n\n"
        "📢 লিংকসহ কোনো পোস্ট পাঠালে আমি তা শর্ট করে দেব।"
    )
    await message.reply(text, parse_mode="Markdown")

@dp.message(Command("setapi"))
async def cmd_setapi(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ এভাবে লিখুন: `/setapi আপনার_কি`")
    
    uid = str(message.from_user.id)
    db = load_db()
    if uid not in db: db[uid] = {"api": "", "footers": []}
    db[uid]["api"] = args[1]
    save_db(db)
    await message.reply("✅ API Key সফলভাবে সেভ করা হয়েছে!")

@dp.message(Command("setfooter"))
async def cmd_setfooter(message: Message):
    if "|" not in message.text:
        return await message.reply("❌ এভাবে লিখুন: `/setfooter নাম | লিংক`")
    
    parts = message.text.replace("/setfooter", "").split("|")
    name = parts[0].strip()
    link = parts[1].strip()
    
    uid = str(message.from_user.id)
    db = load_db()
    if uid not in db: db[uid] = {"api": "", "footers": []}
    if "footers" not in db[uid]: db[uid]["footers"] = []
    
    db[uid]["footers"].append({"name": name, "link": link})
    save_db(db)
    await message.reply(f"✅ ফুটার যোগ হয়েছে:\n**{name}**")

@dp.message(Command("listfooters"))
async def cmd_list(message: Message):
    uid = str(message.from_user.id)
    db = load_db()
    footers = db.get(uid, {}).get("footers", [])
    
    if not footers:
        return await message.reply("📭 আপনার কোনো ফুটার সেট করা নেই।")
    
    msg = "📋 **আপনার ফুটার লিস্ট:**\n\n"
    for i, f in enumerate(footers, 1):
        # এখানে i হলো আইডি (1, 2, 3...)
        msg += f"🆔 **ID: {i}**\n🔹 নাম: {f['name']}\n🔗 লিংক: {f['link']}\n\n"
    
    msg += "🗑 ডিলিট করতে লিখুন: `/delfooter আইডি_নম্বর`"
    await message.reply(msg, disable_web_page_preview=True, parse_mode="Markdown")

@dp.message(Command("delfooter"))
async def cmd_del(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ ডিলিট করতে আইডি দিন। উদাহরণ: `/delfooter 1`")
    
    uid = str(message.from_user.id)
    db = load_db()
    footers = db.get(uid, {}).get("footers", [])
    
    try:
        idx = int(args[1]) - 1 # ইউজার দেয় ১, পাইথনে সেটা ০
        if 0 <= idx < len(footers):
            removed = footers.pop(idx)
            db[uid]["footers"] = footers
            save_db(db)
            await message.reply(f"🗑 ডিলিট হয়েছে: **{removed['name']}**")
        else:
            await message.reply("❌ এই আইডিতে কোনো ফুটার নেই!")
    except:
        await message.reply("❌ আইডিটি সংখ্যায় হতে হবে।")

# ==========================================
# ৬. মেইন প্রসেসিং (লিংক শর্ট করা)
# ==========================================

@dp.message(F.text | F.caption)
async def handle_all(message: Message):
    # যদি মেসেজটি কমান্ড হয় তবে এখানে প্রসেস করবে না
    if message.text and message.text.startswith("/"): return

    uid = str(message.from_user.id)
    db = load_db()
    user_data = db.get(uid)

    if not user_data or not user_data.get("api"):
        return await message.reply("⚠️ আগে `/setapi` দিয়ে আপনার API কি সেট করুন।")

    api = user_data["api"]
    footers = user_data.get("footers", [])
    text = message.text or message.caption or ""
    
    urls = re.findall(r'(https?://[^\s]+)', text)
    
    if urls:
        wait = await message.reply("⏳ লিংকগুলো শর্ট করছি...")
        new_text = text
        for url in urls:
            if DEFAULT_DOMAIN in url: continue
            short_url = await shorten(api, url)
            new_text = new_text.replace(url, short_url)
        await wait.delete()
    else:
        new_text = text

    # ফুটার অ্যাড করা
    if footers:
        new_text += "\n\n" + "━━━━━━━━━━━━━━\n"
        for f in footers:
            new_text += f"📢 [{f['name']}]({f['link']})\n"

    # ফাইনাল আউটপুট পাঠানো
    try:
        if message.photo:
            await message.answer_photo(message.photo[-1].file_id, caption=new_text, parse_mode="Markdown")
        elif message.video:
            await message.answer_video(message.video.file_id, caption=new_text, parse_mode="Markdown")
        else:
            await message.answer(new_text, parse_mode="Markdown", disable_web_page_preview=True)
    except:
        # যদি মার্কডাউন এরর দেয় তবে সাধারণ টেক্সট পাঠাবে
        if message.photo: await message.answer_photo(message.photo[-1].file_id, caption=new_text)
        elif message.video: await message.answer_video(message.video.file_id, caption=new_text)
        else: await message.answer(new_text, disable_web_page_preview=True)

# বট রান করা
async def main():
    print("🚀 Bot is Running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
