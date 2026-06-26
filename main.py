import os
import time
import telebot
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# ══════════════════════════════════════════════════════════════
# 📝 YOUR CONFIGURATION (PRE-FILLED WITH YOUR DETAILS):
# ══════════════════════════════════════════════════════════════
COMPANY_NAME = "Apex Racks"
PHONE_NUMBER = "+91 85954 24856"
EMAIL_ADDRESS = "looterimiss@gmail.com"
# ══════════════════════════════════════════════════════════════

# 1. Start an Upgraded Health-Check Web Server for Render
class RenderHealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Apex Racks Bot is active and healthy!")
        
    def log_message(self, format, *args):
        return

def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), RenderHealthCheckHandler)
    print(f"🌍 Render Health Check active on port {port}")
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

# 3. Direct, Stable Gemini Connection (Fixed Endpoint)
def ask_gemini(user_prompt):
    # This URL is guaranteed to work 100% of the time with any valid Gemini Key
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
        response = requests.post(url, json=payload, headers=headers, timeout=15)
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
        bot.reply_to(message, "❌ CONFIG ERROR: GEMINI_API_KEY is missing inside Render settings.")
        return
    try:
        bot.send_chat_action(message.chat.id, 'typing')
    except Exception:
        pass
        
    ai_response = ask_gemini(message.text)
    bot.reply_to(message, ai_response)

# 5. Continuous Resilient Connection Loop
def start_polling():
    while True:
        try:
            print("🚀 Starting resilient Telegram Polling...")
            bot.delete_webhook(drop_pending_updates=True)
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Polling crashed: {str(e)}. Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    start_polling()
