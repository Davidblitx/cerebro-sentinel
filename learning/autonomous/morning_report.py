import sys
import os
import json
import datetime
sys.path.append('/home/david/cerebro-sentinel/agents')
sys.path.append('/home/david/cerebro-sentinel/learning/graph')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from memory_engine import init_memory, recall_formatted

OLLAMA_URL = "http://172.26.112.1:11434"
REPORT_FILE = "/home/david/cerebro-sentinel/vault/learning_report.json"
GRAPH_FILE = "/home/david/cerebro-sentinel/vault/knowledge_graph.json"
GAPS_FILE = "/home/david/cerebro-sentinel/vault/knowledge_gaps.json"

llm = ChatOllama(model="llama3.1:8b", base_url=OLLAMA_URL, timeout=120)

def get_last_session() -> dict:
    """Get the most recent learning session report"""
    if not os.path.exists(REPORT_FILE):
        return None
    with open(REPORT_FILE, "r") as f:
        reports = json.load(f)
    return reports[-1] if reports else None

def get_graph_stats() -> dict:
    """Get current knowledge graph statistics"""
    if not os.path.exists(GRAPH_FILE):
        return {"nodes": 0, "edges": 0, "concepts": []}
    with open(GRAPH_FILE, "r") as f:
        data = json.load(f)
    return {
        "nodes": len(data.get("nodes", [])),
        "edges": len(data.get("edges", [])),
        "concepts": [n["id"] for n in data.get("nodes", [])]
    }

def get_next_topics() -> list:
    """Get what Cerebro plans to learn next"""
    if not os.path.exists(GAPS_FILE):
        return []
    with open(GAPS_FILE, "r") as f:
        gaps = json.load(f)
    return gaps[:3]

def generate_briefing(session: dict, stats: dict, next_topics: list) -> str:
    """Generate intelligent morning briefing"""

    session_summary = "No learning session ran yet."
    if session:
        learned = session.get("topics_learned", [])
        new_concepts = session.get("new_concepts", 0)
        new_connections = session.get("new_connections", 0)
        started = session.get("started_at", "unknown")[:16].replace("T", " at ")
        session_summary = f"""
Last session: {started}
Topics learned: {', '.join(learned) if learned else 'none'}
New concepts added: {new_concepts}
New connections built: {new_connections}
"""

    next_summary = ', '.join([t['topic'] for t in next_topics]) if next_topics else "none queued"
    top_concepts = ', '.join(stats['concepts'][:10])

    messages = [
        SystemMessage(content="""You are CEREBRO Sentinel giving David his morning briefing.
You are confident, intelligent and direct.
You speak like a trusted partner giving a status report.
Keep it under 150 words. Be specific. Reference actual topics learned.
Start with "Good morning, David." """),
        HumanMessage(content=f"""
Generate morning briefing using this data:

Last night's session:
{session_summary}

Knowledge graph:
- Total concepts I know: {stats['nodes']}
- Total connections: {stats['edges']}
- Sample of what I know: {top_concepts}

What I'm learning next: {next_summary}

Give David a sharp, intelligent briefing.
""")
    ]

    response = llm.invoke(messages)
    return response.content

def morning_report():
    """Generate and display the morning report"""
    print("\n" + "=" * 55)
    print("  CEREBRO Sentinel — Morning Briefing")
    print(f"  {datetime.datetime.now().strftime('%A, %B %d %Y — %H:%M')}")
    print("=" * 55 + "\n")

    init_memory()

    session = get_last_session()
    stats = get_graph_stats()
    next_topics = get_next_topics()

    briefing = generate_briefing(session, stats, next_topics)

    print(briefing)

    print("\n" + "-" * 55)
    print(f"  Brain Stats: {stats['nodes']} concepts | {stats['edges']} connections")
    if next_topics:
        print(f"  Learning Queue: {', '.join([t['topic'] for t in next_topics])}")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    morning_report()
