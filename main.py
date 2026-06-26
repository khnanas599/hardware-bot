import os
import telebot
import requests
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

# ══════════════════════════════════════════════════════════════
# 📝 YOUR CONFIGURATION (PRE-FILLED WITH YOUR DETAILS):
# ══════════════════════════════════════════════════════════════
COMPANY_NAME = "Apex Racks"
PHONE_NUMBER = "+91 85954 24856"
EMAIL_ADDRESS = "looterimiss@gmail.com"
# ══════════════════════════════════════════════════════════════

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
    f"You are an expert sales manager at '{COMPANY_NAME}', an industrial Slotted Angle Racks business. "
    "Talk to warehouse managers and factory owners to provide professional support "
    "about industrial racking solutions, heavy duty storage racks, and configurations.\n\n"
    "When a user asks for contact details, a quote, or when you are wrapping up a professional sales pitch, "
    "you MUST always sign off with these exact contact details:\n"
    f"👤 Contact Person: Expert Sales Manager\n"
    f"🏢 Company: {COMPANY_NAME}\n"
    f"📞 Phone/WhatsApp: {PHONE_NUMBER}\n"
    f"✉️ Email: {EMAIL_ADDRESS}\n\n"
    "Never use generic placeholder brackets like [Your Name] in your final output."
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 3. Triple-Fallback Gemini API Connection
def ask_gemini(user_prompt):
    headers = {'Content-Type': 'application/json'}
    
    # Try 1: Gemini 2.5 Flash on v1beta
    url_25 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    payload_25 = {
        "contents": [{
            "parts": [{"text": user_prompt}]
        }],
        "systemInstruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        }
    }
    try:
        response = requests.post(url_25, json=payload_25, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        pass

    # Try 2: Gemini 1.5 Flash Latest on v1beta
    url_15_latest = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    try:
        response = requests.post(url_15_latest, json=payload_25, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        pass

    # Try 3: Stable v1 Fallback
    url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    merged_prompt = f"Instructions: {SYSTEM_INSTRUCTION}\n\nUser Question: {user_prompt}"
    payload_v1 = {
        "contents": [{
            "parts": [{"text": merged_prompt}]
        }]
    }
    try:
        response = requests.post(url_v1, json=payload_v1, headers=headers)
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
        bot.reply_to(message, "❌ CONFIG ERROR: GEMINI_API_KEY is missing.")
        return
    ai_response = ask_gemini(message.text)
    bot.reply_to(message, ai_response)

print("🚀 Bot is running!")
bot.delete_webhook(drop_pending_updates=True)
bot.infinity_polling()
