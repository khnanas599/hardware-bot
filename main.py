import os
import telebot
import google.generativeai as genai
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

# 1. Start a tiny background web listener so Render doesn't shut down
def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"🌍 Web port {port} active")
    server.serve_forever()

threading.Thread(target=run_port_listener, daemon=True).start()

# 2. Setup API Keys
API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

genai.configure(api_key=API_KEY)

# 3. Define the custom racking sales persona
SYSTEM_INSTRUCTION = (
    "You are an expert sales manager for an industrial Slotted Angle Racks business. "
    "Your job is to talk to warehouse managers, factory owners, and clients to provide professional support. "
    "Always be polite, direct, and focus on details like rack height, number of shelves/panels, and load capacity per layer. "
    "Keep your knowledge base flexible: adapt to custom heights (e.g., 6ft, 7ft, 8ft, 10ft) and load options (e.g., 100kg up to 500kg per layer). "
    "If someone asks for a standard quote or standard rates, ask them for their custom length, depth, height, and number of layers so you can calculate a precise industrial warehouse estimate."
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 4. Handle incoming Telegram messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "System processing inquiry. Please try again in a moment.")

print("🚀 Slotted Angle Rack Bot is active and running smoothly!")
bot.infinity_polling()
