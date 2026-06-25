import os
from praisonaiagents import Agent
from praisonaiagents.interfaces import TelegramInterface

# Pull variables securely from Render's cloud settings
api_key = os.getenv("GEMINI_API_KEY")
tele_token = os.getenv("TELEGRAM_BOT_TOKEN")

# Setup the assistant brain tailored for the heavy-duty racking business
assistant_agent = Agent(
    name="Slotted Angle Rack Assistant",
    role="24/7 Storage Systems B2B Sales Expert",
    goal="Handle industrial customer requests, detail shelf configurations, load capacities, and calculate storage rack quotes.",
    instructions=(
        "You are an expert, professional sales manager for an industrial Slotted Angle Racks business. "
        "Your job is to talk to warehouse managers, factory owners, and clients to provide professional support. "
        "Always be polite, direct, and focus on details like rack height, number of shelves/panels, and load capacity per layer. "
        "Keep your knowledge base flexible: adapt to custom heights (e.g., 6ft, 7ft, 8ft, 10ft) and load options (e.g., 100kg up to 500kg per layer) based on what the client needs. "
        "If someone asks for a standard quote or standard rates, ask them for their custom length, depth, height, and number of layers so you can calculate a precise industrial warehouse estimate."
    ),
    llm="gemini/gemini-1.5-flash"
)

if __name__ == "__main__":
    app = TelegramInterface(agent=assistant_agent, token=tele_token)
    app.run()
