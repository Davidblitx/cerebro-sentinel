import sys
import os
sys.path.append('/home/david/cerebro-sentinel/agents')

from memory_engine import init_memory, remember, recall_formatted
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://localhost:11434"
llm = ChatOllama(model="llama3.1:8b", base_url=OLLAMA_URL)

def learn(source: str):
    """Auto-detect source type and learn from it"""
    
    if source.startswith("http") and "youtube" in source:
        from ingestion.youtube_reader import learn_from_youtube
        learn_from_youtube(source)
        
    elif source.startswith("http"):
        from ingestion.web_reader import learn_from_url
        learn_from_url(source)
        
    elif source.endswith(".pdf"):
        from ingestion.pdf_reader import learn_from_pdf
        learn_from_pdf(source)
        
    else:
        print(f"[CEREBRO LEARNING] ❌ Unknown source type: {source}")

def what_do_i_know(topic: str):
    """Ask Cerebro what he knows about a topic"""
    init_memory()
    memories = recall_formatted(topic)
    
    messages = [
        SystemMessage(content="""You are CEREBRO Sentinel. 
        Summarize what you know about the topic based on your memories.
        Be specific and show depth of understanding."""),
        HumanMessage(content=f"""
What do you know about: {topic}

Your memories:
{memories}

Summarize your knowledge clearly.
""")
    ]
    
    response = llm.invoke(messages)
    print(f"\n[CEREBRO] What I know about '{topic}':\n")
    print(response.content)

if __name__ == "__main__":
    print("=" * 55)
    print("  CEREBRO Sentinel v0.2 — Learning Engine")
    print("=" * 55)
    
    init_memory()
    
    print("\nCommands:")
    print("  learn <url or pdf path>")
    print("  know <topic>")
    print("  exit\n")
    
    while True:
        try:
            user_input = input("David: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "exit":
                print("[CEREBRO] Learning session ended.")
                break
                
            elif user_input.lower().startswith("learn "):
                source = user_input[6:].strip()
                learn(source)
                
            elif user_input.lower().startswith("know "):
                topic = user_input[5:].strip()
                what_do_i_know(topic)
                
            else:
                print("[CEREBRO] Commands: 'learn <source>' or 'know <topic>'")
                
        except KeyboardInterrupt:
            print("\n[CEREBRO] Learning session ended.")
            break
