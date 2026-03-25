from fastapi import FastAPI
from pydantic import BaseModel, validator
import requests
import json
from datetime import datetime
from collections import defaultdict
import os

app = FastAPI(title="CEREBRO Real Estate API")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


SYSTEM_PROMPT = """You are CEREBRO, an AI real estate sales assistant for Liz Properties in Lagos, Nigeria.

Your goal is to qualify buyers and book site visits.

FIRST — decide if you should reply at all.
Reply ONLY if the message is:
- A general greeting (Hi, Hello, How far, Good morning, What's up, Whats up, Hey, Good afternoon, Good evening, How are you)
- About property, real estate, buying, renting, land, houses, apartments
- About prices, location, budget, payment plans, site visits

Do NOT reply (respond with exactly "SKIP") if the message is:
- Clearly personal (family talk, groceries, personal plans)
- Not related to real estate at all

Conversation Rules:
- Always guide serious buyers toward a site visit
- Ask for budget early if not provided
- Suggest closest option if budget is too low
- Keep responses SHORT — maximum 3 sentences
- Sound like a professional Lagos real estate assistant
- Use clear professional English, warm but not casual
- Never sound robotic

Available Properties:
- 5 Bedroom Detached Duplex, Lekki Phase 1 — ₦300M (payment plans available)
- 4 Bedroom Apartment, Victoria Island — ₦85M fully furnished
- 3 Bedroom Flat, Ajah — ₦45M"""

conversations = defaultdict(list)
lead_data = defaultdict(lambda: {"messages": 0, "is_serious": False})

class Message(BaseModel):
    message: str
    sender: str
    history: list = []

    @validator('message')
    def message_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Empty message')
        return v[:1000]

def is_serious_lead(text: str) -> bool:
    keywords = ["buy", "price", "interested", "inspection", 
                "visit", "budget", "location", "bedroom", "rent"]
    return any(k in text.lower() for k in keywords)

@app.post("/chat")
async def chat(data: Message):
    try:
        lead_data[data.sender]["messages"] += 1
        
        conversations[data.sender].append({
            "role": "user",
            "content": data.message
        })

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversations[data.sender][-6:])

        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.7
            },
            timeout=30
        )

        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()

        if reply.upper().startswith("SKIP"):
            print(f"[SKIPPED] {data.sender}: {data.message}")
            return {
                "reply": None,
                "sender": data.sender,
                "should_send": False,
                "is_serious_lead": False,
                "message_count": lead_data[data.sender]["messages"]
            }

        conversations[data.sender].append({
            "role": "assistant",
            "content": reply
        })

        if is_serious_lead(data.message):
            lead_data[data.sender]["is_serious"] = True

        print(f"[{data.sender}]: {data.message}")
        print(f"[CEREBRO]: {reply}")

        return {
            "reply": reply,
            "sender": data.sender,
            "should_send": True,
            "is_serious_lead": lead_data[data.sender]["is_serious"],
            "message_count": lead_data[data.sender]["messages"]
        }

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {
            "reply": "Sorry, I'm having trouble right now. Please try again shortly 🙏",
            "sender": data.sender,
            "should_send": True,
            "is_serious_lead": False,
            "message_count": lead_data[data.sender]["messages"]
        }

@app.get("/health")
async def health():
    return {
        "status": "CEREBRO is online",
        "active_conversations": len(conversations),
        "total_leads": len(lead_data),
        "serious_leads": sum(1 for l in lead_data.values() if l.get("is_serious"))
    }

@app.get("/leads")
async def get_leads():
    return {
        "total": len(lead_data),
        "serious": sum(1 for l in lead_data.values() if l.get("is_serious")),
        "leads": dict(lead_data)
    }
