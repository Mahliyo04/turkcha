import os
from flask import Flask, request
import telebot
from deep_translator import GoogleTranslator
from gtts import gTTS
from dotenv import load_dotenv  # ✅ dotenv qo‘shildi

# ✅ .env faylni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")

# ✅ Token tekshiruvi
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

# User state saqlash uchun dictionary
user_lang = {}

# Inline keyboard
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def language_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Turkcha → O‘zbekcha", callback_data="tr_uz"),
        InlineKeyboardButton("O‘zbekcha → Turkcha", callback_data="uz_tr")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_lang[message.chat.id] = None
    bot.send_message(
        message.chat.id,
        "Salom! Tilni tanlang:",
        reply_markup=language_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data in ["tr_uz", "uz_tr"]:
        user_lang[call.message.chat.id] = call.data
        bot.send_message(call.message.chat.id, "Matnni kiriting:")

@bot.message_handler(func=lambda message: True)
def translate_message(message):
    lang = user_lang.get(message.chat.id)
    if not lang:
        bot.send_message(message.chat.id, "Iltimos, tilni tanlang.", reply_markup=language_keyboard())
        return

    try:
        if lang == "tr_uz":
            translated = GoogleTranslator(source='tr', target='uz').translate(message.text)
            bot.send_message(message.chat.id, translated)
        elif lang == "uz_tr":
            translated = GoogleTranslator(source='uz', target='tr').translate(message.text)
            bot.send_message(message.chat.id, translated)

            # Turkcha ovoz
            tts = gTTS(text=translated, lang='tr')
            tts_file = f"{message.chat.id}_tts.mp3"
            tts.save(tts_file)
            with open(tts_file, "rb") as audio:
                bot.send_audio(message.chat.id, audio)
            os.remove(tts_file)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik yuz berdi: {e}")

# Flask server + webhook
@server.route(f"/{BOT_TOKEN}", methods=["POST"])
def get_message():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    if not APP_URL:
        return "APP_URL .env faylida topilmadi!", 500
    bot.set_webhook(url=f"{APP_URL}/{BOT_TOKEN}")
    return "Bot ishlayapti!", 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    server.run(host="0.0.0.0", port=port)
