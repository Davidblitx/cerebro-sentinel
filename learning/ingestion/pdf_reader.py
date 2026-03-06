import PyPDF2
import os
import sys
sys.path.append('/home/david/cerebro-sentinel/agents')

from memory_engine import init_memory, remember
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://172.26.112.1:11434"
llm = ChatOllama(model="qwen2.5-coder:7b", base_url=OLLAMA_URL)

def extract_pdf_text(filepath: str) -> str:
    """Extract raw text from PDF"""
    text = ""
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def understand_content(text: str, source: str) -> dict:
    """Use Cerebro to understand and summarize content"""
    
    # Process in chunks if too long
    chunk_size = 3000
    chunks = [text[i:i+chunk_size] for i in range(0, min(len(text), 15000), chunk_size)]
    
    all_concepts = []
    all_qa = []
    
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
            HumanMessage(content=f"Extract knowledge from this text:\n\n{chunk}")
        ]
        
        response = llm.invoke(messages)
        content = response.content
        
        # Parse concepts
        if "CONCEPTS:" in content:
            concepts_line = content.split("CONCEPTS:")[1].split("\n")[0]
            concepts = [c.strip() for c in concepts_line.split(",")]
            all_concepts.extend(concepts)
        
        # Parse Q&A pairs
        if "Q:" in content and "A:" in content:
            lines = content.split("\n")
            current_q = None
            for line in lines:
                if line.startswith("Q:"):
                    current_q = line[2:].strip()
                elif line.startswith("A:") and current_q:
                    answer = line[2:].strip()
                    all_qa.append({"q": current_q, "a": answer})
                    current_q = None
    
    return {
        "source": source,
        "concepts": list(set(all_concepts)),
        "qa_pairs": all_qa
    }

def store_knowledge(knowledge: dict):
    """Store extracted knowledge in Cerebro's memory"""
    source = knowledge["source"]
    
    # Store concepts
    for concept in knowledge["concepts"]:
        if concept and len(concept) > 2:
            remember(f"Concept from {source}: {concept}", "knowledge")
    
    # Store Q&A pairs
    for qa in knowledge["qa_pairs"]:
        if qa["q"] and qa["a"]:
            remember(f"Q: {qa['q']} A: {qa['a']}", "knowledge_qa")
    
    print(f"\n[CEREBRO LEARNING] ✅ Stored {len(knowledge['concepts'])} concepts")
    print(f"[CEREBRO LEARNING] ✅ Stored {len(knowledge['qa_pairs'])} Q&A pairs")

def learn_from_pdf(filepath: str):
    """Main function — feed Cerebro a PDF"""
    print(f"\n[CEREBRO LEARNING] Reading: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"[CEREBRO LEARNING] ❌ File not found: {filepath}")
        return
    
    # Extract text
    print("[CEREBRO LEARNING] Extracting text...")
    text = extract_pdf_text(filepath)
    print(f"[CEREBRO LEARNING] Extracted {len(text)} characters")
    
    # Understand content
    print("[CEREBRO LEARNING] Understanding content...")
    knowledge = understand_content(text, os.path.basename(filepath))
    
    # Store in memory
    init_memory()
    store_knowledge(knowledge)
    
    print(f"\n[CEREBRO LEARNING] 🧠 Learning complete for: {filepath}")
    return knowledge

if __name__ == "__main__":
    if len(sys.argv) > 1:
        learn_from_pdf(sys.argv[1])
    else:
        print("Usage: python pdf_reader.py <path_to_pdf>")
        print("Example: python pdf_reader.py /home/david/docs/devops.pdf")
