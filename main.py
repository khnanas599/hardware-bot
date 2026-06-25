import os
import telebot
import google.generativeai as genai
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

# 1. Start background web listener for Render
def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"🌍 Web port {port} active")
    server.serve_forever()

threading.Thread(target=run_port_listener, daemon=True).start()

# 2. Setup API Keys
API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Force configuration
genai.configure(api_key=API_KEY or "MISSING_KEY")

SYSTEM_INSTRUCTION = (
    "You are an expert sales manager for an industrial Slotted Angle Racks business. "
    "Talk to warehouse managers and factory owners to provide professional support."
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 3. Handle incoming Telegram messages and print errors to chat
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Check if key looks empty
        if not API_KEY or API_KEY == "":
            bot.reply_to(message, "❌ CONFIG ERROR: GEMINI_API_KEY is missing or empty in Render Environment settings.")
            return
            
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        # This will reply with the EXACT error message from Google
        error_msg = f"❌ AI Engine Error:\n{str(e)}"
        bot.reply_to(message, error_msg)

print("🚀 Diagnostic Bot is active!")
bot.infinity_polling()
