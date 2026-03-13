from youtube_transcript_api import YouTubeTranscriptApi
import sys
import re
sys.path.append('/home/david/cerebro-sentinel/agents')

from memory_engine import init_memory, remember
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://localhost:11434"
llm = ChatOllama(model="llama3.1:8b", base_url=OLLAMA_URL)

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url  # Assume it's already a video ID

def get_transcript(url: str) -> str:
    """Get transcript from YouTube video"""
    video_id = extract_video_id(url)
    print(f"[CEREBRO LEARNING] Fetching transcript for video: {video_id}")
    
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    full_text = " ".join([entry["text"] for entry in transcript])
    return full_text

def learn_from_youtube(url: str):
    """Main function — feed Cerebro a YouTube video"""
    print(f"\n[CEREBRO LEARNING] Processing YouTube: {url}")
    
    # Get transcript
    text = get_transcript(url)
    if not text:
        print("[CEREBRO LEARNING] ❌ No transcript available")
        return
    
    print(f"[CEREBRO LEARNING] Transcript: {len(text)} characters")
    print("[CEREBRO LEARNING] Understanding content...")
    
    chunk_size = 3000
    chunks = [text[i:i+chunk_size] for i in range(0, min(len(text), 12000), chunk_size)]
    
    total_concepts = 0
    total_qa = 0
    
    init_memory()
    
    for i, chunk in enumerate(chunks):
        print(f"[CEREBRO LEARNING] Processing chunk {i+1}/{len(chunks)}...")
        
        messages = [
            SystemMessage(content="""You are Cerebro's learning engine.
            Extract knowledge from this video transcript.
            Always respond in this exact format:
            
            CONCEPTS: concept1, concept2, concept3
            SUMMARY: one paragraph summary
            QA:
            Q: question1
            A: answer1
            Q: question2
            A: answer2
            """),
            HumanMessage(content=f"Extract knowledge from this transcript:\n\n{chunk}")
        ]
        
        response = llm.invoke(messages)
        content = response.content

        if "CONCEPTS:" in content:
            concepts_line = content.split("CONCEPTS:")[1].split("\n")[0]
            concepts = [c.strip() for c in concepts_line.split(",")]
            for concept in concepts:
                if concept and len(concept) > 2:
                    remember(f"From YouTube {url}: {concept}", "youtube_knowledge")
                    total_concepts += 1

        if "Q:" in content and "A:" in content:
            lines = content.split("\n")
            current_q = None
            for line in lines:
                if line.startswith("Q:"):
                    current_q = line[2:].strip()
                elif line.startswith("A:") and current_q:
                    answer = line[2:].strip()
                    remember(f"Q: {current_q} A: {answer}", "youtube_knowledge_qa")
                    total_qa += 1
                    current_q = None

    print(f"\n[CEREBRO LEARNING] ✅ Stored {total_concepts} concepts")
    print(f"[CEREBRO LEARNING] ✅ Stored {total_qa} Q&A pairs")
    print(f"[CEREBRO LEARNING] 🧠 Learning complete for: {url}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        learn_from_youtube(sys.argv[1])
    else:
        print("Usage: python youtube_reader.py <youtube_url>")
        print("Example: python youtube_reader.py https://youtube.com/watch?v=XXXXX")
