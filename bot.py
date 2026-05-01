import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import re

TOKEN = "8745935271:AAHDkRcH3Z59UoBpKENZaf_V32OHRGPMgjo"
CHANNEL = "@havenrealty_uz"
MANAGER = "Havenrealtymanager"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

DISTRICTS = [
    "Yunusobod", "Chilonzor", "Mirzo Ulugbek", "Yakkasaroy",
    "Shayxontohur", "Olmazar", "Sergeli", "Uchtepa",
    "Bektemir", "Mirobod", "Yashnobod"
]

DISTRICT_MAP = {
    "Yunusobod": ["юнусабад"],
    "Chilonzor": ["чиланзар"],
    "Mirzo Ulugbek": ["мирзо улугбек"],
    "Yakkasaroy": ["яккасарай"],
    "Shayxontohur": ["шайхантахур"],
    "Olmazar": ["алмазар"],
    "Sergeli": ["сергели"],
    "Uchtepa": ["учтепа"],
    "Bektemir": ["бектемир"],
    "Mirobod": ["мирабад"],
    "Yashnobod": ["яшнабад"],
}

ROOMS = ["1", "2", "3", "4+"]
PRICES = ["300-500$", "500-700$", "700-1000$", "1000$+", "Farqi yo'q"]

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {}
    keyboard = []
    row = []
    for i, d in enumerate(DISTRICTS):
        row.append(InlineKeyboardButton(d, callback_data=f"d_{d}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    await update.message.reply_text(
        "🏙 Assalomu alaykum! Tumanni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if user_id not in user_data:
        user_data[user_id] = {}

    if data.startswith("d_"):
        user_data[user_id]["district"] = data[2:]
        keyboard = [[InlineKeyboardButton(f"{r} xona", callback_data=f"r_{r}") for r in ROOMS]]
        await query.edit_message_text("🚪 Xona sonini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("r_"):
        user_data[user_id]["rooms"] = data[2:]
        keyboard = [
            [InlineKeyboardButton(p, callback_data=f"p_{p}") for p in PRICES[:2]],
            [InlineKeyboardButton(p, callback_data=f"p_{p}") for p in PRICES[2:]]
        ]
        await query.edit_message_text("💰 Narx oralig'ini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("p_"):
        user_data[user_id]["price"] = data[2:]
        filters = user_data[user_id]
        district = filters.get("district", "")
        rooms = filters.get("rooms", "")

        await query.edit_message_text("🔍 Qidirilmoqda...")

        keywords = DISTRICT_MAP.get(district, [district.lower()])

        try:
            found = []
            async for msg in context.bot.get_chat_history(CHANNEL, limit=200):
                if not msg.text:
                    continue
                text = msg.text.lower()
                if not any(kw in text for kw in keywords):
                    continue
                if rooms and rooms != "4+":
                    if f"количество комнат: {rooms}" not in text:
                        continue
                found.append(msg.text[:500])
                if len(found) >= 3:
                    break
        except Exception as e:
            logging.error(f"Xato: {e}")
            found = []

        contact_btn = [[
            InlineKeyboardButton("🔄 Qaytadan", callback_data="restart"),
            InlineKeyboardButton("📞 Menejer", url=f"https://t.me/{MANAGER}")
        ]]

        if found:
            for i, listing in enumerate(found, 1):
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"📌 E'lon {i}:\n\n{listing}"
                )
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"✅ {len(found)} ta e'lon topildi!",
                reply_markup=InlineKeyboardMarkup(contact_btn)
            )
        else:
            await query.edit_message_text(
                "😔 Mos e'lon topilmadi. Menejer bilan bog'laning!",
                reply_markup=InlineKeyboardMarkup(contact_btn)
            )

    elif data == "restart":
        user_data[user_id] = {}
        keyboard = []
        row = []
        for d in DISTRICTS:
            row.append(InlineKeyboardButton(d, callback_data=f"d_{d}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        await query.edit_message_text(
            "🏙 Tumanni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
