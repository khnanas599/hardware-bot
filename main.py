import os
import asyncio
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from praisonaiagents import Agent, BotConfig
from praisonai.bots import TelegramBot

# 1. Start a tiny background web listener so Render's Free tier doesn't timeout
def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"🌍 Keeping Render happy on port {port}")
    server.serve_forever()

threading.Thread(target=run_port_listener, daemon=True).start()

# 2. Grab keys securely from your cloud environment settings
api_key = os.getenv("GEMINI_API_KEY")
tele_token = os.getenv("TELEGRAM_BOT_TOKEN")

# 3. Design your custom racking sales bot parameters
rack_agent = Agent(
    name="Slotted Angle Rack Assistant",
    role="24/7 Storage Systems Sales Expert",
    goal="Handle industrial customer requests, detail shelf configurations, and calculate storage rack quotes.",
    instructions=(
        "You are an expert sales manager for an industrial Slotted Angle Racks business. "
        "Talk to warehouse managers and factory owners to provide professional support. "
        "Focus on details like rack height, number of shelves, and load capacity per layer. "
        "Ask for custom length, depth, height, and number of layers to give estimates."
    ),
    llm="gemini/gemini-1.5-flash"
)

# 4. Initialize the deployment bot engine
async def main():
    config = BotConfig(token=tele_token, typing_indicator=True)
    bot = TelegramBot(token=tele_token, agent=rack_agent, config=config)
    print("🚀 Slotted Angle Rack Bot is live and polling!")
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
