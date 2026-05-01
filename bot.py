import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = "8745935271:AAHDkRcH3Z59UoBpKENZaf_V32OHRGPMgjo"
MANAGER = "Havenrealtymanager"

bot = telebot.TeleBot(TOKEN)

DISTRICTS = [
    "Yunusobod", "Chilonzor", "Mirzo Ulugbek", "Yakkasaroy",
    "Shayxontohur", "Olmazar", "Sergeli", "Uchtepa",
    "Bektemir", "Mirobod", "Yashnobod"
]

ROOMS = ["1", "2", "3", "4+"]
PRICES = ["300-500$", "500-700$", "700-1000$", "1000$+", "Farqi yo'q"]

user_data = {}

def district_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(d, callback_data=f"d|{d}") for d in DISTRICTS]
    markup.add(*buttons)
    return markup

def rooms_keyboard():
    markup = InlineKeyboardMarkup(row_width=4)
    buttons = [InlineKeyboardButton(f"{r} xona", callback_data=f"r|{r}") for r in ROOMS]
    markup.add(*buttons)
    return markup

def price_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(p, callback_data=f"p|{p}") for p in PRICES]
    markup.add(*buttons)
    return markup

def contact_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔄 Qaytadan", callback_data="restart"),
        InlineKeyboardButton("📞 Menejer", url=f"https://t.me/{MANAGER}")
    )
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    bot.send_message(
        message.chat.id,
        "🏙 Assalomu alaykum! Qaysi tumandan uy qidiryapsiz?",
        reply_markup=district_keyboard()
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("d|"))
def handle_district(call):
    user_id = call.from_user.id
    district = call.data.split("|")[1]
    user_data[user_id] = {"district": district}
    bot.edit_message_text(
        f"✅ Tuman: {district}\n\n🚪 Xona sonini tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=rooms_keyboard()
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("r|"))
def handle_rooms(call):
    user_id = call.from_user.id
    rooms = call.data.split("|")[1]
    user_data[user_id]["rooms"] = rooms
    district = user_data[user_id].get("district", "")
    bot.edit_message_text(
        f"✅ Tuman: {district}\n✅ Xona: {rooms}\n\n💰 Narx oralig'ini tanlang:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=price_keyboard()
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("p|"))
def handle_price(call):
    user_id = call.from_user.id
    price = call.data.split("|")[1]
    user_data[user_id]["price"] = price
    filters = user_data[user_id]

    bot.edit_message_text(
        "🔍 Qidirilmoqda...",
        call.message.chat.id,
        call.message.message_id
    )

    bot.send_message(
        call.message.chat.id,
        f"📋 Qidiruv natijalari:\n\n"
        f"🏙 Tuman: {filters.get('district')}\n"
        f"🚪 Xona: {filters.get('rooms')}\n"
        f"💰 Narx: {filters.get('price')}\n\n"
        f"Menejer siz uchun mos variantlarni topib beradi!",
        reply_markup=contact_keyboard()
    )

@bot.callback_query_handler(func=lambda c: c.data == "restart")
def handle_restart(call):
    user_id = call.from_user.id
    user_data[user_id] = {}
    bot.edit_message_text(
        "🏙 Qaysi tumandan uy qidiryapsiz?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=district_keyboard()
    )

if __name__ == "__main__":
    logging.info("Bot ishga tushdi!")
    bot.infinity_polling()
