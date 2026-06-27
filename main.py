import os
import time
import json
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

# Initialize Bot
API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

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

# 1. Direct, Ultra-Stable Gemini Connection
def ask_gemini(user_prompt):
    # Try the standard v1beta endpoint first (supports system instructions perfectly)
    url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]}
    }
    
    try:
        response = requests.post(url_beta, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        pass

    # Fallback to standard stable v1 endpoint if beta is blocked/restricted
    url_stable = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    # Stable v1 doesn't support system instructions parameter directly, so we merge it into the prompt
    merged_prompt = f"System Instructions:\n{SYSTEM_INSTRUCTION}\n\nUser Question:\n{user_prompt}"
    payload_stable = {
        "contents": [{"parts": [{"text": merged_prompt}]}]
    }
    
    try:
        response = requests.post(url_stable, json=payload_stable, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return (
                f"⚠️ Google API Error (Status {response.status_code}):\n"
                "Your Google API Key might not have the 'Generative Language API' enabled.\n"
                "Please get a free key directly from Google AI Studio!"
            )
    except Exception as e:
        return f"❌ Connection Error: Could not reach Google Servers ({str(e)})"

# 2. Handle Telegram Messages
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

# 3. HTTP Server to Handle Webhooks (Zero Conflicts) & Render Health Checks
class WebhookServer(BaseHTTPRequestHandler):
    def do_GET(self):
        # Keeps Render happy and online
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Apex Racks Bot is online!")

    def do_POST(self):
        # Receives messages instantly from Telegram
        if self.path == '/webhook':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                update_json = json.loads(post_data.decode('utf-8'))
                update = telebot.types.Update.de_json(update_json)
                bot.process_new_updates([update])
                self.send_response(200)
                self.end_headers()
            except Exception as e:
                print(f"Error processing update: {e}")
                self.send_response(200)  # Always send 200 to Telegram to prevent retry loops
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return # Suppress console logs to keep Render logs clean

# 4. Webhook Setup Thread
def setup_webhook_delayed():
    time.sleep(5)  # Let HTTP server start first
    public_url = os.getenv("RENDER_EXTERNAL_URL")
    
    if public_url:
        public_url = public_url.rstrip('/')
        webhook_path = f"{public_url}/webhook"
        print(f"🔒 Setting Webhook to: {webhook_path}")
        bot.remove_webhook()
        bot.set_webhook(url=webhook_path)
    else:
        print("⚠️ No RENDER_EXTERNAL_URL found. Falling back to safe Polling mode...")
        bot.remove_webhook()
        # Safe, auto-reconnecting infinity polling for local testing
        bot.infinity_polling(timeout=10, long_polling_timeout=5)

# 5. Main Execution Entry Point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebhookServer)
    
    # Run the webhook registration in the background
    threading.Thread(target=setup_webhook_delayed, daemon=True).start()
    
    print(f"🌍 Server listening on port {port}...")
    server.serve_forever() 
