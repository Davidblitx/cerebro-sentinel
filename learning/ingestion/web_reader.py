import trafilatura
import requests
import hashlib
import datetime
import os
import sys
import json
from bs4 import BeautifulSoup

from memory_engine import init_memory, remember
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

LEARNED_SOURCES_FILE = "/home/david/cerebro-sentinel/vault/learned_sources.json"

def is_already_learned(url: str) -> bool:
    """Check if Cerebro has already learned from this source"""
    if not os.path.exists(LEARNED_SOURCES_FILE):
        return False
    with open(LEARNED_SOURCES_FILE, "r") as f:
        learned = json.load(f)
    return url in learned

def mark_as_learned(url: str):
    """Mark a source as learned"""
    learned = {}
    if os.path.exists(LEARNED_SOURCES_FILE):
        with open(LEARNED_SOURCES_FILE, "r") as f:
            learned = json.load(f)
    learned[url] = {
        "learned_at": datetime.datetime.now().isoformat()
    }
    os.makedirs(os.path.dirname(LEARNED_SOURCES_FILE), exist_ok=True)
    with open(LEARNED_SOURCES_FILE, "w") as f:
        json.dump(learned, f, indent=2)


OLLAMA_URL = "http://localhost:11434"
llm = ChatOllama(model="qwen2.5-coder:7b", base_url=OLLAMA_URL)

def extract_web_text(url: str) -> str:
    """Extract clean text from any URL"""
    try:
        # Try trafilatura first
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded)
            if text and len(text) > 500:
                return text

        # Fallback to requests + BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
            
        text = soup.get_text(separator="\n")
        # Clean up whitespace
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines)
        
    except Exception as e:
        print(f"[CEREBRO LEARNING] Extraction error: {e}")
        return ""

def understand_and_store(text: str, source: str):
    """Understand web content and store in memory"""
    if not text:
        print(f"[CEREBRO LEARNING] ❌ Could not extract content from {source}")
        return

    chunk_size = 2000
    chunks = [text[i:i+chunk_size] for i in range(0, min(len(text), 5000), chunk_size)]
    
    total_concepts = 0
    total_qa = 0

    for i, chunk in enumerate(chunks):
        print(f"[CEREBRO LEARNING] Processing chunk {i+1}/{len(chunks)}...")
        
        messages = [
            SystemMessage(content="""You are Cerebro's learning engine.
            Extract knowledge from text in structured format.
            Always respond in this exact format:
            
            CONCEPTS: concept1, concept2, concept3
            SUMMARY: one paragraph summary
            QA:
            Q: question1
            A: answer1
            Q: question2
            A: answer2
            """),
            HumanMessage(content=f"Extract knowledge from:\n\n{chunk}")
        ]
        
        response = llm.invoke(messages)
        content = response.content
        
        # Parse and store concepts
        if "CONCEPTS:" in content:
            concepts_line = content.split("CONCEPTS:")[1].split("\n")[0]
            concepts = [c.strip() for c in concepts_line.split(",")]
            for concept in concepts:
                if concept and len(concept) > 2:
                    remember(f"From {source}: {concept}", "web_knowledge")
                    total_concepts += 1

        # Parse and store Q&A
        if "Q:" in content and "A:" in content:
            lines = content.split("\n")
            current_q = None
            for line in lines:
                if line.startswith("Q:"):
                    current_q = line[2:].strip()
                elif line.startswith("A:") and current_q:
                    answer = line[2:].strip()
                    remember(f"Q: {current_q} A: {answer}", "web_knowledge_qa")
                    total_qa += 1
                    current_q = None

    print(f"\n[CEREBRO LEARNING] ✅ Stored {total_concepts} concepts")
    print(f"[CEREBRO LEARNING] ✅ Stored {total_qa} Q&A pairs")

def learn_from_url(url: str):
    """Main function — feed Cerebro a URL"""
    # Check if already learned
    if is_already_learned(url):
        print(f"\n[CEREBRO] I have already learned from this source, David.")
        print(f"[CEREBRO] Source: {url}")
        print(f"[CEREBRO] No need to process it again.")
        return

    print(f"\n[CEREBRO LEARNING] Reading URL: {url}")
    
    text = extract_web_text(url)
    if not text:
        print("[CEREBRO LEARNING] ❌ Failed to extract content")
        return
        
    print(f"[CEREBRO LEARNING] Extracted {len(text)} characters")
    print("[CEREBRO LEARNING] Understanding content...")
    
    init_memory()
    understand_and_store(text, url)
    
    mark_as_learned(url)
    print(f"\n[CEREBRO LEARNING] 🧠 Learning complete for: {url}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        learn_from_url(sys.argv[1])
    else:
        print("Usage: python web_reader.py <url>")
        print("Example: python web_reader.py https://docs.docker.com/get-started/")
