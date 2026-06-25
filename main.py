import os
import telebot
import requests
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

# 1. Start background web listener for Render
def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print("🌍 Web port active")
    server.serve_forever()

threading.Thread(target=run_port_listener, daemon=True).start()

# 2. Setup Bot & API Keys
API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SYSTEM_INSTRUCTION = (
    "You are an expert sales manager for an industrial Slotted Angle Racks business. "
    "Talk to warehouse managers and factory owners to provide professional support "
    "about industrial racking solutions, heavy duty storage racks, and configurations."
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 3. Direct Gemini Call
def ask_gemini(user_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": user_prompt}]
        }],
        "systemInstruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"❌ Google API Error (Status {response.status_code}):\n{response.text}"
    except Exception as e:
        return f"❌ HTTP Connection Error:\n{str(e)}"

# 4. Handle Telegram Messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not API_KEY:
        bot.reply_to(message, "❌ CONFIG ERROR: GEMINI_API_KEY is missing in Render settings.")
        return
    ai_response = ask_gemini(message.text)
    bot.reply_to(message, ai_response)

print("🚀 Bot is running!")
bot.infinity_polling()
