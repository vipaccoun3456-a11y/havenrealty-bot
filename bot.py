import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import re

# Bot token
TOKEN = "8745935271:AAHDkRcH3Z59UoBpKENZaf_V32OHRGPMgjo"

# Kanal username
CHANNEL = "@havenrealty_uz"

# Manager username
MANAGER = "@Havenrealtymanager"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Toshkent tumanlari
DISTRICTS = [
    "Yunusobod", "Chilonzor", "Mirzo Ulugbek", "Yakkasaroy",
    "Shayxontohur", "Olmazar", "Sergeli", "Uchtepa",
    "Bektemir", "Mirobod", "Yashnobod"
]

ROOMS = ["1", "2", "3", "4+"]
FLOORS = ["1-3", "4-6", "7-9", "10+", "Farqi yo'q"]
AREAS = ["30-50 m²", "50-70 m²", "70-100 m²", "100+ m²", "Farqi yo'q"]
PRICES = ["300-500$", "500-700$", "700-1000$", "1000$+", "Farqi yo'q"]

user_filters = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_filters[user_id] = {}
    
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Tilni tanlang / Выберите язык:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if user_id not in user_filters:
        user_filters[user_id] = {}

    # Til tanlash
    if data.startswith("lang_"):
        user_filters[user_id]["lang"] = data.split("_")[1]
        await show_districts(query)

    # Tuman tanlash
    elif data.startswith("district_"):
        district = data.replace("district_", "")
        user_filters[user_id]["district"] = district
        await show_rooms(query)

    # Xona tanlash
    elif data.startswith("rooms_"):
        rooms = data.replace("rooms_", "")
        user_filters[user_id]["rooms"] = rooms
        await show_floors(query)

    # Qavat tanlash
    elif data.startswith("floor_"):
        floor = data.replace("floor_", "")
        user_filters[user_id]["floor"] = floor
        await show_areas(query)

    # Maydon tanlash
    elif data.startswith("area_"):
        area = data.replace("area_", "")
        user_filters[user_id]["area"] = area
        await show_prices(query)

    # Narx tanlash
    elif data.startswith("price_"):
        price = data.replace("price_", "")
        user_filters[user_id]["price"] = price
        await search_listings(query, context, user_id)

async def show_districts(query):
    keyboard = []
    row = []
    for i, district in enumerate(DISTRICTS):
        row.append(InlineKeyboardButton(district, callback_data=f"district_{district}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    await query.edit_message_text(
        "🏙 Tumanni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_rooms(query):
    keyboard = [[InlineKeyboardButton(r + " xona", callback_data=f"rooms_{r}") for r in ROOMS]]
    await query.edit_message_text(
        "🚪 Xona sonini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_floors(query):
    keyboard = [[InlineKeyboardButton(f, callback_data=f"floor_{f}") for f in FLOORS[:3]],
                [InlineKeyboardButton(f, callback_data=f"floor_{f}") for f in FLOORS[3:]]]
    await query.edit_message_text(
        "🏢 Qavatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_areas(query):
    keyboard = [[InlineKeyboardButton(a, callback_data=f"area_{a}") for a in AREAS[:2]],
                [InlineKeyboardButton(a, callback_data=f"area_{a}") for a in AREAS[2:]]]
    await query.edit_message_text(
        "📐 Maydonni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_prices(query):
    keyboard = [[InlineKeyboardButton(p, callback_data=f"price_{p}") for p in PRICES[:2]],
                [InlineKeyboardButton(p, callback_data=f"price_{p}") for p in PRICES[2:]]]
    await query.edit_message_text(
        "💰 Narx oralig'ini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def parse_price(price_str):
    """Narxni dollardan raqamga o'girish"""
    price_str = price_str.replace(" ", "").replace("$", "").replace("/месяц", "")
    match = re.search(r'\d+', price_str)
    if match:
        return int(match.group())
    return 0

def matches_filters(text, filters):
    """E'lon filterlarga mos kelishini tekshirish"""
    text_lower = text.lower()
    
    # Tuman tekshirish
    district = filters.get("district", "")
    district_map = {
        "Yunusobod": ["юнусабад", "yunusobod"],
        "Chilonzor": ["чиланзар", "chilonzor"],
        "Mirzo Ulugbek": ["мирзо улугбек", "mirzo ulugbek"],
        "Yakkasaroy": ["яккасарай", "yakkasaroy"],
        "Shayxontohur": ["шайхантахур", "shayxontohur"],
        "Olmazar": ["алмазар", "olmazar"],
        "Sergeli": ["сергели", "sergeli"],
        "Uchtepa": ["учтепа", "uchtepa"],
        "Bektemir": ["бектемир", "bektemir"],
        "Mirobod": ["мирабад", "mirobod"],
        "Yashnobod": ["яшнабад", "yashnobod"],
    }
    
    district_keywords = district_map.get(district, [district.lower()])
    if not any(kw in text_lower for kw in district_keywords):
        return False

    # Xona soni tekshirish
    rooms = filters.get("rooms", "")
    if rooms and rooms != "4+":
        if f"количество комнат: {rooms}" not in text_lower:
            return False
    elif rooms == "4+":
        match = re.search(r'количество комнат:\s*(\d+)', text_lower)
        if match and int(match.group(1)) < 4:
            return False

    return True

async def search_listings(query, context, user_id):
    filters = user_filters.get(user_id, {})
    
    await query.edit_message_text("🔍 Qidirilmoqda... Bir oz kuting...")

    try:
        found = []
        async for message in context.bot.get_chat(CHANNEL):
            if message.text and matches_filters(message.text, filters):
                found.append(message.text[:300] + "...")
                if len(found) >= 5:
                    break
    except Exception as e:
        logger.error(f"Kanal o'qishda xato: {e}")
        found = []

    if found:
        result_text = f"✅ {len(found)} ta e'lon topildi:\n\n"
        for i, listing in enumerate(found, 1):
            result_text += f"**{i}.** {listing}\n\n---\n\n"
        
        keyboard = [[InlineKeyboardButton("🔄 Qaytadan qidirish", callback_data="restart"),
                     InlineKeyboardButton("📞 Bog'lanish", url=f"https://t.me/{MANAGER.replace('@', '')}")]]
        
        await query.edit_message_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        keyboard = [[InlineKeyboardButton("🔄 Qaytadan qidirish", callback_data="restart"),
                     InlineKeyboardButton("📞 Menejer bilan bog'lanish", url=f"https://t.me/{MANAGER.replace('@', '')}")]]
        
        await query.edit_message_text(
            f"😔 Afsuski, so'rovingizga mos e'lon topilmadi.\n\n"
            f"Menejer bilan bog'laning — u sizga yordam beradi! 👇",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_filters[user_id] = {}
    await show_districts(query)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(restart, pattern="^restart$"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
