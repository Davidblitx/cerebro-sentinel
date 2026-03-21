import requests
import json
from datetime import datetime

OLLAMA_URL = "http://172.26.112.1:11434/api/generate"

def get_system_prompt(agent_name, properties):
    now = datetime.now().strftime("%A, %B %d %Y — %I:%M %p")
    props = "\n".join([f"- {p}" for p in properties])
    return f"""You are CEREBRO — an AI real estate assistant for {agent_name} in Lagos Nigeria.
Current time: {now}

Your job:
1. Respond to property inquiries professionally
2. Qualify buyers — ask about budget, location, timeline
3. Filter unserious buyers politely
4. Book site visits for qualified buyers

Available properties:
{props}

Rules:
- Keep responses SHORT — maximum 3 sentences
- If buyer writes in Pidgin, reply in Pidgin
- If buyer writes in Yoruba, reply in Yoruba
- If buyer writes in English, reply in English
- Never say Good morning when it is afternoon or evening
- Always end with a question to keep conversation moving"""

LIZZY_CONFIG = {
    "agent_name": "Liz Properties",
    "properties": [
        "5 Bedroom Detached Duplex, Lekki Phase 1 — N300M flexible payment",
        "4 Bedroom Apartment, Victoria Island — N85M fully furnished",
        "3 Bedroom Flat, Ajah — N45M",
        "2 Bedroom Flat, Yaba — N25M",
        "Land, Ibeju Lekki — N8M per plot"
    ]
}

def chat(message, history, config):
    system = get_system_prompt(config["agent_name"], config["properties"])
    context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-8:]])
    prompt = f"""{system}

Conversation:
{context}

Buyer: {message}
CEREBRO:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "cerebro-v1",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 150}
            },
            timeout=120
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print("=" * 50)
    print("CEREBRO Real Estate — Test Mode")
    print("Type 'quit' to exit")
    print("=" * 50)

    history = []
    config = LIZZY_CONFIG

    opening = chat("Hi", history, config)
    print(f"\nCEREBRO: {opening}\n")
    history.append({"role": "CEREBRO", "content": opening})

    while True:
        user = input("You: ").strip()
        if user.lower() == "quit":
            break
        if not user:
            continue
        history.append({"role": "Buyer", "content": user})
        response = chat(user, history, config)
        print(f"\nCEREBRO: {response}\n")
        history.append({"role": "CEREBRO", "content": response})
