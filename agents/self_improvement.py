import sys
import os
import json
import datetime
sys.path.append('/home/david/cerebro-sentinel')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.1:8b"
REASONING_LOG = "/home/david/cerebro-sentinel/logs/reasoning.log"
GAPS_FILE = "/home/david/cerebro-sentinel/vault/knowledge_gaps.json"
GRAPH_FILE = "/home/david/cerebro-sentinel/vault/knowledge_graph.json"
IMPROVEMENT_LOG = "/home/david/cerebro-sentinel/logs/self_improvement.log"
IMPROVEMENT_PLAN = "/home/david/cerebro-sentinel/vault/improvement_plan.json"

llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL, timeout=180)

def load_reasoning_history() -> list:
    """Load past reasoning chains to find weaknesses"""
    if not os.path.exists(REASONING_LOG):
        return []
    chains = []
    with open(REASONING_LOG, "r") as f:
        content = f.read()
    blocks = content.split("=" * 50)
    for block in blocks:
        if '"confidence"' in block:
            try:
                start = block.find("{")
                end = block.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(block[start:end])
                    chains.append(data)
            except:
                pass
    return chains

def load_knowledge_graph() -> dict:
    """Load current knowledge graph"""
    if not os.path.exists(GRAPH_FILE):
        return {"nodes": [], "edges": []}
    with open(GRAPH_FILE, "r") as f:
        return json.load(f)

def load_gaps() -> list:
    """Load current knowledge gaps"""
    if not os.path.exists(GAPS_FILE):
        return []
    with open(GAPS_FILE, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("gaps", [])

def analyze_weaknesses(chains: list) -> dict:
    """Find patterns in low confidence answers"""
    if not chains:
        return {
            "low_confidence_topics": [],
            "failed_stress_tests": [],
            "unknown_domains": [],
            "average_confidence": 0,
        "total_questions_analyzed": 0,
	    "total_question_analyzed": 0
        }

    low_confidence = []
    failed_tests = []
    confidences = []

    for chain in chains:
        confidence = chain.get("confidence", 100)
        confidences.append(confidence)

        if confidence < 65:
            question = chain.get("question", "")
            understanding = chain.get("understanding", {})
            domain = understanding.get("domain", "unknown")
            low_confidence.append({
                "question": question,
                "confidence": confidence,
                "domain": domain
            })

        stress = chain.get("stress_test", {})
        if not stress.get("survives_stress_test", True):
            question = chain.get("question", "")
            failed_tests.append(question)

    avg = sum(confidences) / len(confidences) if confidences else 0

    return {
        "low_confidence_topics": low_confidence,
        "failed_stress_tests": failed_tests,
        "average_confidence": round(avg, 1),
        "total_questions_analyzed": len(chains)
    }

def identify_blind_spots(graph: dict, gaps: list) -> list:
    """Find domains CEREBRO has never touched"""
    master_domains = [
        "networking", "cryptography", "machine learning",
        "data structures", "algorithms", "operating systems",
        "distributed systems", "database design", "api design",
        "microservices", "serverless", "observability",
        "incident response", "threat modeling", "zero trust",
        "financial systems", "healthcare systems", "legal frameworks",
        "economics", "psychology", "physics", "mathematics"
    ]

    nodes = graph.get("nodes", [])
    known_concepts = [n.get("id", "").lower() for n in nodes]
    known_text = " ".join(known_concepts)

    blind_spots = []
    for domain in master_domains:
        if domain.lower() not in known_text:
            blind_spots.append(domain)

    return blind_spots[:10]

def generate_improvement_plan(weaknesses: dict, blind_spots: list,
                               gaps: list) -> dict:
    """Use LLM to create intelligent improvement plan"""

    context = f"""
Current weaknesses analysis:
- Average confidence: {weaknesses['average_confidence']}%
- Low confidence topics: {weaknesses['low_confidence_topics'][:3]}
- Failed stress tests: {weaknesses['failed_stress_tests'][:3]}
- Total questions analyzed: {weaknesses['total_questions_analyzed']}

Known knowledge gaps: {gaps[:5]}
Blind spots (never studied): {blind_spots[:5]}
"""

    messages = [
        SystemMessage(content="""You are CEREBRO's self-improvement engine.
Analyze the weaknesses and create a prioritized improvement plan.
Respond ONLY in JSON:
{
  "priority_1": {
    "topic": "most critical topic to learn",
    "reason": "why this is most important",
    "approach": "how to learn it",
    "expected_impact": "what improves after learning this"
  },
  "priority_2": {
    "topic": "second most critical topic",
    "reason": "why",
    "approach": "how",
    "expected_impact": "impact"
  },
  "priority_3": {
    "topic": "third most critical topic",
    "reason": "why",
    "approach": "how",
    "expected_impact": "impact"
  },
  "overall_assessment": "honest assessment of current knowledge state",
  "biggest_blind_spot": "the single most important gap to address",
  "estimated_sessions_to_improve": 5
}"""),
        HumanMessage(content=f"Create improvement plan based on:\n{context}")
    ]

    try:
        r = llm.invoke(messages)
        text = r.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return {
            "priority_1": {"topic": gaps[0] if gaps else "networking",
                          "reason": "identified gap", "approach": "systematic study",
                          "expected_impact": "broader knowledge base"},
            "overall_assessment": "Insufficient reasoning history for deep analysis",
            "biggest_blind_spot": blind_spots[0] if blind_spots else "unknown",
            "estimated_sessions_to_improve": 5
        }

def update_learning_queue(plan: dict):
    """Inject improvement priorities into the learning queue"""
    priorities = []
    for key in ["priority_1", "priority_2", "priority_3"]:
        item = plan.get(key, {})
        topic = item.get("topic", "")
        if topic:
            priorities.append({
                "topic": topic,
                "category": "self_improvement",
                "reason": item.get("reason", ""),
                "priority": "HIGH"
            })

    if os.path.exists(GAPS_FILE):
        with open(GAPS_FILE, "r") as f:
            existing = json.load(f)
        if isinstance(existing, list):
            existing = {"gaps": existing}
    else:
        existing = {"gaps": []}

    existing_gaps = existing.get("gaps", [])
    existing_topics = [g if isinstance(g, str) else g.get("topic", "") 
                      for g in existing_gaps]

    for p in priorities:
        if p["topic"] not in existing_topics:
            existing_gaps.insert(0, p)

    existing["gaps"] = existing_gaps
    existing["last_improvement_analysis"] = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M")

    with open(GAPS_FILE, "w") as f:
        json.dump(existing, f, indent=2)

def log_improvement(weaknesses: dict, plan: dict):
    """Log the improvement analysis"""
    os.makedirs(os.path.dirname(IMPROVEMENT_LOG), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(IMPROVEMENT_LOG, "a") as f:
        f.write(f"\n[{ts}] SELF IMPROVEMENT ANALYSIS\n")
        f.write(f"Average confidence: {weaknesses['average_confidence']}%\n")
        f.write(f"Questions analyzed: {weaknesses['total_questions_analyzed']}\n")
        f.write(f"Biggest blind spot: {plan.get('biggest_blind_spot', 'N/A')}\n")
        f.write(f"Overall: {plan.get('overall_assessment', 'N/A')}\n")
        f.write("=" * 50 + "\n")

    with open(IMPROVEMENT_PLAN, "w") as f:
        json.dump({
            "generated": ts,
            "weaknesses": weaknesses,
            "plan": plan
        }, f, indent=2)

def run_self_improvement(verbose: bool = True):
    """Full self improvement cycle"""
    if verbose:
        print("\n" + "=" * 55)
        print("  CEREBRO Self-Improvement Engine")
        print("=" * 55)
        print("[CEREBRO] Analyzing my own performance...")

    chains = load_reasoning_history()
    graph = load_knowledge_graph()
    gaps = load_gaps()

    if verbose:
        print(f"[CEREBRO] Reasoning chains analyzed: {len(chains)}")

    weaknesses = analyze_weaknesses(chains)

    if verbose:
        print(f"[CEREBRO] Average confidence: {weaknesses['average_confidence']}%")
        print(f"[CEREBRO] Low confidence answers: "
              f"{len(weaknesses['low_confidence_topics'])}")
        print(f"[CEREBRO] Failed stress tests: "
              f"{len(weaknesses['failed_stress_tests'])}")
        print("[CEREBRO] Identifying blind spots...")

    blind_spots = identify_blind_spots(graph, gaps)

    if verbose:
        print(f"[CEREBRO] Blind spots found: {len(blind_spots)}")
        print("[CEREBRO] Generating improvement plan...")

    plan = generate_improvement_plan(weaknesses, blind_spots, gaps)

    log_improvement(weaknesses, plan)
    update_learning_queue(plan)

    if verbose:
        print("\n" + "-" * 55)
        print("  IMPROVEMENT PLAN")
        print("-" * 55)
        print(f"Overall: {plan.get('overall_assessment', 'N/A')}")
        print(f"Biggest blind spot: {plan.get('biggest_blind_spot', 'N/A')}")
        print(f"Estimated sessions to improve: "
              f"{plan.get('estimated_sessions_to_improve', 'N/A')}")
        print("\nTop priorities:")
        for key in ["priority_1", "priority_2", "priority_3"]:
            item = plan.get(key, {})
            if item:
                print(f"  → {item.get('topic', 'N/A')}: "
                      f"{item.get('reason', 'N/A')}")
        print("-" * 55)
        print("[CEREBRO] Learning queue updated with improvement priorities.")
        print("[CEREBRO] Self-improvement cycle complete. ✅\n")

    return plan

if __name__ == "__main__":
    run_self_improvement(verbose=True)
