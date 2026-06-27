import os
import time
import telebot
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# ══════════════════════════════════════════════════════════════
# 📝 YOUR APEX RACKS BUSINESS DETAILS (EMBEDDED DIRECTLY)
# ══════════════════════════════════════════════════════════════
COMPANY_NAME = "Apex Racks"
PHONE_NUMBER = "+91 85954 24856"
EMAIL_ADDRESS = "looterimiss@gmail.com"
# ══════════════════════════════════════════════════════════════

# 1. Start a simple Health-Check Web Server for Render
class RenderHealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Apex Racks Bot is active and healthy!")
        
    def log_message(self, format, *args):
        # Keeps Render console logs clean
        return

def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), RenderHealthCheckHandler)
    print(f"🌍 Render Health Check active on port {port}")
    server.serve_forever()

threading.Thread(target=run_port_listener, daemon=True).start()

# 2. Get and Clean Keys (Removes any accidental mobile spaces/newlines)
API_KEY = os.getenv("GEMINI_API_KEY", "").strip().replace('"', '').replace("'", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().replace('"', '').replace("'", "")

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
    "NEVER use generic placeholder brackets like [Your Name], [Company Name], or [Insert Your Phone Number Here]. "
    f"Always output the real values: Company Name is '{COMPANY_NAME}', Phone is '{PHONE_NUMBER}', and Email is '{EMAIL_ADDRESS}'."
)

# 3. Direct HTTP Gemini Connection (Completely Bypasses Google SDK bugs with AQ. keys)
def ask_gemini(user_prompt):
    # Direct, official REST endpoints
    models_to_try = ["gemini-1.5-flash", "gemini-2.5-flash"]
    headers = {'Content-Type': 'application/json'}
    
    last_error_details = ""
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]}
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
            else:
                last_error_details = f"Model {model_name} returned Status {response.status_code}: {response.text}"
        except Exception as e:
            last_error_details = f"Connection error on {model_name}: {str(e)}"
            
    # Return clear diagnostic instructions if it fails
    return (
        "❌ AI Connection Error\n\n"
        f"Diagnostic details:\n{last_error_details}\n\n"
        "💡 Please double check your Render Environment settings. "
        "Make sure GEMINI_API_KEY is saved with no leading spaces."
    )

# 4. Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Handle Telegram Messages
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

# 5. Continuous Resilient Connection Loop (Kills 409 Conflict)
def start_polling():
    while True:
        try:
            print("🚀 Starting resilient Telegram Polling...")
            bot.delete_webhook(drop_pending_updates=True)
            bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Polling crashed: {str(e)}. Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    start_polling()
