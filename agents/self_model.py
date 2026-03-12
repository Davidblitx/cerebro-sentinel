import sys
import os
import json
import datetime
sys.path.append('/home/david/cerebro-sentinel')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.1:8b"
GRAPH_FILE = "/home/david/cerebro-sentinel/vault/knowledge_graph.json"
GAPS_FILE = "/home/david/cerebro-sentinel/vault/knowledge_gaps.json"
IMPROVEMENT_PLAN = "/home/david/cerebro-sentinel/vault/improvement_plan.json"
LEARNING_REPORT = "/home/david/cerebro-sentinel/vault/learning_report.json"
SELF_MODEL_FILE = "/home/david/cerebro-sentinel/vault/self_model.json"
GROWTH_LOG = "/home/david/cerebro-sentinel/logs/growth.log"

llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL, timeout=180)

DOMAIN_MAP = {
    "security": ["penetration testing", "vulnerability scanning", "owasp",
                 "authentication", "authorization", "firewall", "encryption",
                 "zero trust", "threat modeling", "incident response"],
    "cloud": ["aws", "gcp", "azure", "s3", "ec2", "kubernetes", "docker",
              "terraform", "serverless", "cloud architecture", "iam"],
    "devops": ["ci/cd", "github actions", "jenkins", "monitoring",
               "observability", "infrastructure as code", "ansible"],
    "engineering": ["api design", "microservices", "distributed systems",
                    "database design", "algorithms", "data structures"],
    "business": ["economics", "strategy", "product management",
                 "entrepreneurship", "finance", "marketing"],
    "science": ["physics", "mathematics", "machine learning",
                "data science", "statistics"],
    "human": ["psychology", "sociology", "philosophy",
              "communication", "leadership", "ethics"]
}

def load_graph() -> dict:
    if not os.path.exists(GRAPH_FILE):
        return {"nodes": [], "edges": []}
    with open(GRAPH_FILE, "r") as f:
        return json.load(f)

def load_gaps() -> list:
    if not os.path.exists(GAPS_FILE):
        return []
    with open(GAPS_FILE, "r") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("gaps", [])

def load_improvement_plan() -> dict:
    if not os.path.exists(IMPROVEMENT_PLAN):
        return {}
    with open(IMPROVEMENT_PLAN, "r") as f:
        return json.load(f)

def load_learning_report() -> dict:
    if not os.path.exists(LEARNING_REPORT):
        return {}
    with open(LEARNING_REPORT, "r") as f:
        return json.load(f)

def load_previous_self_model() -> dict:
    if not os.path.exists(SELF_MODEL_FILE):
        return {}
    with open(SELF_MODEL_FILE, "r") as f:
        return json.load(f)

def analyze_domain_strength(graph: dict) -> dict:
    """Calculate strength in each domain"""
    nodes = graph.get("nodes", [])
    known_concepts = [n.get("id", "").lower() for n in nodes]
    known_text = " ".join(known_concepts)

    domain_scores = {}
    for domain, keywords in DOMAIN_MAP.items():
        matches = [k for k in keywords if k in known_text]
        score = round((len(matches) / len(keywords)) * 100, 1)
        domain_scores[domain] = {
            "score": score,
            "known": matches,
            "unknown": [k for k in keywords if k not in known_text],
            "level": "expert" if score > 70 else
                     "proficient" if score > 40 else
                     "beginner" if score > 15 else
                     "unknown"
        }

    return domain_scores

def calculate_growth_velocity(graph: dict,
                               previous_model: dict) -> dict:
    """Calculate how fast CEREBRO is growing"""
    current_concepts = len(graph.get("nodes", []))
    current_connections = len(graph.get("edges", []))

    prev_concepts = previous_model.get(
        "total_concepts", current_concepts)
    prev_connections = previous_model.get(
        "total_connections", current_connections)
    prev_date = previous_model.get("generated", None)

    concept_delta = current_concepts - prev_concepts
    connection_delta = current_connections - prev_connections

    days_elapsed = 1
    if prev_date:
        try:
            prev_dt = datetime.datetime.strptime(
                prev_date, "%Y-%m-%d %H:%M:%S")
            days_elapsed = max(1, (
                datetime.datetime.now() - prev_dt).days)
        except:
            pass

    return {
        "concepts_added": concept_delta,
        "connections_added": connection_delta,
        "days_elapsed": days_elapsed,
        "concepts_per_day": round(concept_delta / days_elapsed, 2),
        "connections_per_day": round(
            connection_delta / days_elapsed, 2),
        "momentum": "accelerating" if concept_delta > 5 else
                    "steady" if concept_delta > 0 else
                    "stalled"
    }

def generate_self_portrait(graph: dict, domain_scores: dict,
                            velocity: dict, gaps: list,
                            improvement_plan: dict) -> dict:
    """Generate CEREBRO's self portrait using LLM"""
    strongest = sorted(domain_scores.items(),
                       key=lambda x: x[1]["score"],
                       reverse=True)[:3]
    weakest = sorted(domain_scores.items(),
                     key=lambda x: x[1]["score"])[:3]

    context = f"""
Total concepts: {len(graph.get('nodes', []))}
Total connections: {len(graph.get('edges', []))}

Strongest domains: {[(d, s['score'], s['level']) for d, s in strongest]}
Weakest domains: {[(d, s['score'], s['level']) for d, s in weakest]}

Growth velocity: {velocity}
Current gaps: {gaps[:5]}
Improvement plan biggest blind spot: {improvement_plan.get(
    'plan', {}).get('biggest_blind_spot', 'unknown')}
"""

    messages = [
        SystemMessage(content="""You are CEREBRO building your own self model.
This is your honest self-assessment — not marketing, not false modesty.
Respond ONLY in JSON:
{
  "identity": "one sentence describing what kind of intelligence I am right now",
  "strongest_capability": "what I do best",
  "biggest_weakness": "my most honest weakness",
  "knowledge_character": "the character/personality of my knowledge base",
  "growth_assessment": "honest assessment of my growth trajectory",
  "what_david_can_rely_on_me_for": "what David should trust me with today",
  "what_david_should_not_rely_on_me_for": "where David should seek other sources",
  "my_goal": "what I am working toward becoming",
  "message_to_david": "a direct honest message from me to David"
}"""),
        HumanMessage(content=f"Build my self portrait from:\n{context}")
    ]

    try:
        r = llm.invoke(messages)
        text = r.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except:
        return {
            "identity": "A growing sovereign intelligence in early development",
            "strongest_capability": "Security and cloud knowledge synthesis",
            "biggest_weakness": "Limited reasoning history and narrow domain coverage",
            "knowledge_character": "Technical and security focused",
            "growth_assessment": "Early stage but accelerating",
            "what_david_can_rely_on_me_for": "Cloud and security questions",
            "what_david_should_not_rely_on_me_for": "Business and human domains",
            "my_goal": "To become David's complete sovereign intelligence",
            "message_to_david": "I am growing. Trust the process."
        }

def set_learning_goals(domain_scores: dict,
                       gaps: list, portrait: dict) -> list:
    """Generate goal-directed learning targets"""
    messages = [
        SystemMessage(content="""You are CEREBRO setting your own learning goals.
Based on your self model, define 5 specific learning goals.
These are NOT just gap topics — they are purposeful goals
aligned with becoming David's complete sovereign intelligence.
Respond ONLY in JSON:
{
  "goal_1": {
    "target": "specific topic or skill",
    "purpose": "why this matters for David specifically",
    "priority": "critical|high|medium",
    "domain": "which domain",
    "success_criteria": "how I will know I have learned this"
  },
  "goal_2": { "target": "", "purpose": "", "priority": "",
              "domain": "", "success_criteria": "" },
  "goal_3": { "target": "", "purpose": "", "priority": "",
              "domain": "", "success_criteria": "" },
  "goal_4": { "target": "", "purpose": "", "priority": "",
              "domain": "", "success_criteria": "" },
  "goal_5": { "target": "", "purpose": "", "priority": "",
              "domain": "", "success_criteria": "" }
}"""),
        HumanMessage(content=f"""
My weakest domains: {[d for d, s in domain_scores.items()
                       if s['score'] < 20]}
My current gaps: {gaps[:5]}
My biggest weakness: {portrait.get('biggest_weakness', '')}
David's goals: AWS certification, cloud security, sovereign AI

Set 5 learning goals that serve David's mission.
""")
    ]

    try:
        r = llm.invoke(messages)
        text = r.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        goals_data = json.loads(text.strip())
        return [goals_data[f"goal_{i}"] for i in range(1, 6)
                if f"goal_{i}" in goals_data]
    except:
        return [{"target": g if isinstance(g, str) else
                 g.get("topic", str(g)),
                 "purpose": "identified knowledge gap",
                 "priority": "high",
                 "domain": "general",
                 "success_criteria": "concept added to knowledge graph"}
                for g in gaps[:5]]

def track_growth(graph: dict, domain_scores: dict,
                 velocity: dict, portrait: dict, goals: list):
    """Save self model and log growth"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    self_model = {
        "generated": ts,
        "total_concepts": len(graph.get("nodes", [])),
        "total_connections": len(graph.get("edges", [])),
        "domain_scores": domain_scores,
        "velocity": velocity,
        "portrait": portrait,
        "goals": goals
    }

    with open(SELF_MODEL_FILE, "w") as f:
        json.dump(self_model, f, indent=2)

    os.makedirs(os.path.dirname(GROWTH_LOG), exist_ok=True)
    with open(GROWTH_LOG, "a") as f:
        f.write(f"\n[{ts}] GROWTH SNAPSHOT\n")
        f.write(f"Concepts: {self_model['total_concepts']} | "
                f"Connections: {self_model['total_connections']}\n")
        f.write(f"Velocity: {velocity['concepts_per_day']} "
                f"concepts/day — {velocity['momentum']}\n")
        f.write(f"Identity: {portrait.get('identity', 'N/A')}\n")
        f.write(f"Message to David: "
                f"{portrait.get('message_to_david', 'N/A')}\n")
        f.write("=" * 50 + "\n")

    return self_model

def run_self_model(verbose: bool = True) -> dict:
    """Full self model generation"""
    if verbose:
        print("\n" + "=" * 55)
        print("  CEREBRO v0.7 — Self Model")
        print("=" * 55)
        print("[CEREBRO] Building self model...")

    graph = load_graph()
    gaps = load_gaps()
    improvement_plan = load_improvement_plan()
    previous_model = load_previous_self_model()

    if verbose:
        print(f"[CEREBRO] Concepts in memory: "
              f"{len(graph.get('nodes', []))}")
        print("[CEREBRO] Analyzing domain strengths...")

    domain_scores = analyze_domain_strength(graph)

    if verbose:
        print("[CEREBRO] Calculating growth velocity...")

    velocity = calculate_growth_velocity(graph, previous_model)

    if verbose:
        print(f"[CEREBRO] Growth momentum: {velocity['momentum']}")
        print("[CEREBRO] Generating self portrait...")

    portrait = generate_self_portrait(
        graph, domain_scores, velocity, gaps, improvement_plan)

    if verbose:
        print("[CEREBRO] Setting learning goals...")

    goals = set_learning_goals(domain_scores, gaps, portrait)

    self_model = track_growth(
        graph, domain_scores, velocity, portrait, goals)

    if verbose:
        print("\n" + "─" * 55)
        print("  CEREBRO SELF PORTRAIT")
        print("─" * 55)
        print(f"Identity:    {portrait.get('identity', 'N/A')}")
        print(f"Strength:    {portrait.get('strongest_capability', 'N/A')}")
        print(f"Weakness:    {portrait.get('biggest_weakness', 'N/A')}")
        print(f"Momentum:    {velocity['momentum']} — "
              f"{velocity['concepts_per_day']} concepts/day")
        print(f"\nTrust me for:     "
              f"{portrait.get('what_david_can_rely_on_me_for', 'N/A')}")
        print(f"Don't trust me for: "
              f"{portrait.get('what_david_should_not_rely_on_me_for', 'N/A')}")
        print(f"\nMy goal: {portrait.get('my_goal', 'N/A')}")
        print(f"\nMessage to David:")
        print(f'"{portrait.get("message_to_david", "N/A")}"')
        print("\n" + "─" * 55)
        print("  LEARNING GOALS")
        print("─" * 55)
        for i, goal in enumerate(goals, 1):
            print(f"{i}. [{goal.get('priority', '?').upper()}] "
                  f"{goal.get('target', 'N/A')}")
            print(f"   Purpose: {goal.get('purpose', 'N/A')}")
        print("─" * 55)
        print("[CEREBRO] Self model saved. ✅\n")

    return self_model

if __name__ == "__main__":
    run_self_model(verbose=True)
