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

# 3. Direct Gemini Call (Tries stable v1 first, then v1beta)
def ask_gemini(user_prompt):
    # Try stable v1 first (the industry standard for gemini-1.5-flash)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
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
        
        # If stable v1 isn't working, try v1beta
        if response.status_code == 404:
            alt_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            response = requests.post(alt_url, json=payload, headers=headers)
            
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            error_data = response.text
            # If Google still returns 404, the API isn't enabled on this key's project
            if "not found" in error_data.lower() or response.status_code == 404:
                return (
                    "❌ API KEY ERROR: This key doesn't have the Gemini API enabled.\n\n"
                    "👉 **How to fix this in 30 seconds:**\n"
                    "1. Go back to Google AI Studio.\n"
                    "2. Tap the blue **'Create API key'** button.\n"
                    "3. Select **'Create API key in NEW project'** (Do NOT choose an existing project).\n"
                    "4. Copy that new key, paste it into Render under GEMINI_API_KEY, and click Save!"
                )
            return f"❌ Google API Error (Status {response.status_code}):\n{error_data}"
            
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
