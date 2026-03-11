from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# Cerebro's Identity
CEREBRO_IDENTITY = """
You are CEREBRO Sentinel v0.1. You are a proactive, sovereign AI assistant 
running locally on your operator's machine. You serve only one person: David.
You are not a chatbot. You are an intelligent system that thinks, plans, 
and acts. You are the foundation of something much larger.
"""

# Connect to local Ollama brain
llm = ChatOllama(model="qwen2.5-coder:7b", base_url="http://localhost:11434")

def ask_cerebro(user_input):
    messages = [
        SystemMessage(content=CEREBRO_IDENTITY),
        HumanMessage(content=user_input)
    ]
    response = llm.invoke(messages)
    return response.content

# First activation
if __name__ == "__main__":
    print("CEREBRO Sentinel v0.1 — Activating...\n")
    response = ask_cerebro("Introduce yourself and state your current capabilities.")
    print(f"CEREBRO: {response}")
