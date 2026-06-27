import os
import time
import telebot
import google.generativeai as genai
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

# 2. Configure Official Google Generative AI SDK
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

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

# 3. Secure and Reliable SDK Chat Connection
def ask_gemini(user_prompt):
    try:
        # Initialize the official Google Generative Model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Request generation
        response = model.generate_content(user_prompt)
        return response.text
        
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "401" in error_msg:
            return (
                "❌ API Key Unauthorized:\n"
                "The GEMINI_API_KEY saved in your Render settings is invalid.\n\n"
                "Please verify that you copied the key correctly from Google AI Studio and did not include any extra spaces or hidden characters."
            )
        return f"❌ AI Connection Error: {error_msg}"

# 4. Initialize Telegram Bot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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
            # Drop old webhooks and flush pending messages to prevent conflict
            bot.delete_webhook(drop_pending_updates=True)
            # infinity_polling automatically manages reconnects and delays
            bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Polling crashed: {str(e)}. Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    start_polling()
