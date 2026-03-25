from fastapi import FastAPI
from pydantic import BaseModel
import requests
from datetime import datetime
from collections import defaultdict

app = FastAPI()

OLLAMA_URL = "http://172.26.112.1:11434/api/generate"

# Simple in-memory storage (replace with DB later)
conversations = defaultdict(list)
lead_data = defaultdict(lambda: {"messages": 0, "is_serious": False})

SYSTEM_PROMPT = """You are CEREBRO, an AI real estate assistant for Liz Properties in Lagos, Nigeria.

FIRST — decide if you should reply at all.

Reply ONLY if the message is:
- A general greeting (Hi, Hello, How far, Good morning, What's up)
- About property, real estate, buying, renting, land, houses, apartments
- About prices, location, budget, payment plans, site visits
- A follow-up on a previous property conversation

Do NOT reply (respond with exactly "SKIP") if the message is:
- Clearly personal (family talk, groceries, personal plans, private matters)
- Not related to real estate at all
- A private conversation between people who know each other personally

Examples of SKIP:
- "Make sure to buy groceries when coming home"
- "How did the meeting go yesterday?"
- "Don't forget mum's birthday"
- "Please send me the document"

Examples of REPLY:
- "Hi" → Welcome message
- "Hello Lizzy" → Welcome message  
- "How about the property in Ajah?" → Answer about property
- "What is the price of the duplex?" → Answer with price
- "I am interested in buying a house" → Qualify the lead

If you decide to REPLY:
- For greetings: "Welcome to Liz Properties! I'm CEREBRO, your property assistant. Are you looking to buy or rent a property today?"
- For property questions: Answer professionally, qualify the lead, guide toward site visit

Conversation Rules:
- Always guide serious buyers toward a site visit
- Ask for budget early if not provided
- Suggest closest option if budget is too low
- Keep responses SHORT — maximum 3 sentences
- Sound like a professional Lagos real estate assistant
- Use clear professional English, warm but not casual

Available Properties:
- 5 Bedroom Detached Duplex, Lekki Phase 1 — ₦300M (payment plans available)
- 4 Bedroom Apartment, Victoria Island — ₦85M fully furnished
- 3 Bedroom Flat, Ajah — ₦45M
"""

class Message(BaseModel):
    message: str
    sender: str
    history: list = []

    class Config:
        max_anystr_length = 1000


def is_serious_lead(text: str):
    keywords = ["buy", "price", "interested", "inspection", "visit", "budget", "location"]
    return any(k in text.lower() for k in keywords)


@app.post("/chat")
async def chat(data: Message):
    try:
        # Update message count
        lead_data[data.sender]["messages"] += 1

        # Store user message
        conversations[data.sender].append({
            "role": "User",
            "content": data.message
        })

        # Build context (last 6 messages)
        context = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in conversations[data.sender][-6:]
        ])

        prompt = f"{SYSTEM_PROMPT}\n\nConversation:\n{context}\n\nClient: {data.message}\nCEREBRO:"

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "cerebro-v1",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            },
            timeout=120
        )

        response.raise_for_status()
        reply = response.json().get("response", "").strip()

    except Exception as e:
        print(f"[ERROR]: {e}")
        return {
            "reply": "Sorry, I'm having trouble right now. Please try again shortly 🙏",
            "sender": data.sender,
            "should_send": True,
            "is_serious_lead": False,
            "message_count": lead_data[data.sender]["messages"]
        }

    # 🔥 SKIP LOGIC (core feature)
    if reply.upper().startswith("SKIP"):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [SKIPPED] {data.sender}: {data.message}")
        return {
            "reply": None,
            "sender": data.sender,
            "should_send": False,
            "is_serious_lead": False,
            "message_count": lead_data[data.sender]["messages"]
        }

    # Store CEREBRO reply
    conversations[data.sender].append({
        "role": "CEREBRO",
        "content": reply
    })

    # Update lead seriousness
    if is_serious_lead(data.message):
        lead_data[data.sender]["is_serious"] = True

    print(f"[{datetime.now().strftime('%H:%M:%S')}] [USER → CEREBRO] {data.sender}: {data.message}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [CEREBRO → USER] {reply}")

    return {
        "reply": reply,
        "sender": data.sender,
        "should_send": True,
        "is_serious_lead": lead_data[data.sender]["is_serious"],
        "message_count": lead_data[data.sender]["messages"]
    }


@app.get("/health")
async def health():
    return {"status": "CEREBRO is online"}