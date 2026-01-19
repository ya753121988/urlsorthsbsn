import os
import sys
import subprocess

# ==========================================
# ১. অটোমেটিক লাইব্রেরি ইন্সটলার (Zero Setup)
# ==========================================
def auto_install():
    # যা যা লাইব্রেরি লাগবে তার লিস্ট
    packages = ["aiogram", "aiohttp"]
    
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"📦 {package} পাওয়া যায়নি। অটোমেটিক ইন্সটল করা হচ্ছে... দয়া করে অপেক্ষা করুন।")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} ইন্সটল সফল হয়েছে।")

# কোড চলার শুরুতেই এই ফাংশনটি কাজ করবে
auto_install()

# লাইব্রেরিগুলো ইমপোর্ট করা
import logging
import json
import re
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message

# ==========================================
# ২. কনফিগারেশন (এখানে আপনার টোকেন দিন)
# ==========================================
API_TOKEN = '8488533482:AAHfM7dS8CjZ1bL541BvOLOrfIWjSu0VJJs'  # <--- এখানে আপনার বট টোকেন দিন
DEFAULT_DOMAIN = 'urlbotsot.vercel.app'     # আপনার শর্টনার ডোমেইন (যেমন: gplinks.in)
DATABASE_FILE = 'bot_database.json'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ডাটাবেস হ্যান্ডলিং (JSON) ---
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

# --- ইউআরএল শর্ট করার ফাংশন ---
async def shorten_url(api_key, long_url):
    api_url = f"https://{DEFAULT_DOMAIN}/api?api={api_key}&url={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=15) as response:
                res_data = await response.json()
                if res_data.get('status') == 'success':
                    return res_data.get('shortenedUrl')
                return long_url
    except:
        return long_url

# ==========================================
# ৩. বটের কমান্ডসমূহ
# ==========================================

@dp.message(Command("start"))
async def start_handler(message: Message):
    user = message.from_user
    text = (
        f"👋 হ্যালো {user.full_name}!\n\n"
        f"🆔 আইডি: `{user.id}`\n"
        f"👤 ইউজারনেম: @{user.username}\n\n"
        "📜 **বট কমান্ডসমূহ:**\n"
        "🔹 `/setapi API_KEY` - আপনার শর্টনার এপিআই কি সেট করুন\n"
        "🔹 `/setfooter নাম | লিংক` - ফুটার যোগ করুন (আনলিমিটেড)\n"
        "🔹 `/listfooters` - ফুটার লিস্ট দেখুন\n"
        "🔹 `/delfooter ID` - নির্দিষ্ট ফুটার ডিলিট করুন\n\n"
        "যেকোনো পোস্ট পাঠান বা ফরওয়ার্ড করুন, আমি সব লিংক শর্ট করে সাজিয়ে দেব।"
    )
    await message.reply(text, parse_mode="Markdown")

@dp.message(Command("setapi"))
async def set_api(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ ফরম্যাট: `/setapi আপনার_এপিআই_কি`")
    
    uid = str(message.from_user.id)
    db = get_db()
    if uid not in db: db[uid] = {"api": "", "footers": []}
    db[uid]["api"] = args[1]
    save_db(db)
    await message.reply("✅ আপনার API Key সফলভাবে সেভ হয়েছে।")

@dp.message(Command("setfooter"))
async def add_footer(message: Message):
    content = message.text.replace("/setfooter", "").strip()
    if "|" not in content:
        return await message.reply("❌ ফরম্যাট: `/setfooter চ্যানেলের নাম | লিংক`")
    
    name, link = content.split("|", 1)
    uid = str(message.from_user.id)
    db = get_db()
    
    if uid not in db: db[uid] = {"api": "", "footers": []}
    db[uid]["footers"].append({"name": name.strip(), "link": link.strip()})
    save_db(db)
    await message.reply(f"✅ ফুটার যোগ হয়েছে: **{name.strip()}**")

@dp.message(Command("listfooters"))
async def list_footers(message: Message):
    uid = str(message.from_user.id)
    db = get_db()
    footers = db.get(uid, {}).get("footers", [])
    
    if not footers:
        return await message.reply("আপনার কোনো ফুটার সেট করা নেই।")
    
    msg = "📋 **আপনার ফুটারসমূহ:**\n\n"
    for i, f in enumerate(footers, 1):
        msg += f"{i}. {f['name']} - {f['link']}\n"
    msg += "\nডিলিট করতে লিখুন: `/delfooter ID` (যেমন: /delfooter 1)"
    await message.reply(msg, disable_web_page_preview=True)

@dp.message(Command("delfooter"))
async def del_footer(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ ফরম্যাট: `/delfooter ID` (আইডি পেতে /listfooters দেখুন)")
    
    uid = str(message.from_user.id)
    db = get_db()
    footers = db.get(uid, {}).get("footers", [])
    
    try:
        idx = int(args[1]) - 1
        if 0 <= idx < len(footers):
            removed = footers.pop(idx)
            db[uid]["footers"] = footers
            save_db(db)
            await message.reply(f"🗑 **ডিলিট করা হয়েছে:** {removed['name']}")
        else:
            await message.reply("❌ ভুল আইডি!")
    except:
        await message.reply("❌ আইডি সংখ্যায় দিন।")

# ==========================================
# ৪. মেইন প্রসেসিং (লিংক শর্ট ও পোস্ট রিপ্লাই)
# ==========================================

@dp.message(F.text | F.caption)
async def process_message(message: Message):
    uid = str(message.from_user.id)
    db = get_db()
    user_data = db.get(uid)

    if not user_data or not user_data.get("api"):
        return await message.reply("⚠️ আপনি এখনো API সেট করেননি! আগে `/setapi` কমান্ড ব্যবহার করুন।")

    api_key = user_data["api"]
    footers = user_data.get("footers", [])
    
    original_content = message.text or message.caption or ""
    # লিংক খুঁজে বের করার Regex
    urls = re.findall(r'(https?://[^\s]+)', original_content)
    
    if urls:
        waiting = await message.reply("⏳ লিংকগুলো শর্ট করা হচ্ছে... দয়া করে অপেক্ষা করুন।")
        new_content = original_content
        for url in urls:
            # যদি লিংকটি আগে থেকেই আপনার ডোমেইনের হয় তবে শর্ট করার দরকার নেই
            if DEFAULT_DOMAIN in url:
                continue
            shorted = await shorten_url(api_key, url)
            new_content = new_content.replace(url, shorted)
        await waiting.delete()
    else:
        new_content = original_content

    # ফুটার সাজানো
    if footers:
        new_content += "\n\n" + "━" * 15 + "\n"
        for f in footers:
            new_content += f"📢 [{f['name']}]({f['link']})\n"

    # রিপ্লাই পাঠানো (ফটো, ভিডিও বা টেক্সট অনুযায়ী)
    try:
        if message.photo:
            await message.answer_photo(message.photo[-1].file_id, caption=new_content, parse_mode="Markdown")
        elif message.video:
            await message.answer_video(message.video.file_id, caption=new_content, parse_mode="Markdown")
        else:
            await message.answer(new_content, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await message.answer(f"❌ এরর: {str(e)}")

# বট রান করা
async def main():
    print("🤖 বট সফলভাবে চালু হয়েছে এবং এটি অনলাইনে আছে।")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 বট বন্ধ করা হয়েছে।")
