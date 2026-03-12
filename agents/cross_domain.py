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
CROSS_DOMAIN_LOG = "/home/david/cerebro-sentinel/logs/cross_domain.log"

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
                "data science", "statistics", "biology"],
    "human": ["psychology", "sociology", "philosophy",
              "communication", "leadership", "ethics"]
}

def load_knowledge_graph() -> dict:
    if not os.path.exists(GRAPH_FILE):
        return {"nodes": [], "edges": []}
    with open(GRAPH_FILE, "r") as f:
        return json.load(f)

def get_known_domains(graph: dict) -> dict:
    """Map known concepts to domains"""
    nodes = graph.get("nodes", [])
    known_concepts = [n.get("id", "").lower() for n in nodes]
    known_text = " ".join(known_concepts)

    active_domains = {}
    for domain, keywords in DOMAIN_MAP.items():
        matches = [k for k in keywords if k in known_text]
        if matches:
            active_domains[domain] = matches

    return active_domains

def find_domain_connections(question: str, active_domains: dict) -> list:
    """Find which domains are relevant to this question"""
    question_lower = question.lower()
    relevant = []

    for domain, concepts in active_domains.items():
        for concept in concepts:
            if any(word in question_lower for word in concept.split()):
                if domain not in relevant:
                    relevant.append(domain)
                break

    if not relevant:
        relevant = list(active_domains.keys())[:3]

    return relevant

def step1_map_domains(question: str, active_domains: dict) -> dict:
    """Map question to relevant knowledge domains"""
    domain_summary = {d: concepts[:3] for d, concepts in active_domains.items()}

    messages = [
        SystemMessage(content="""You are CEREBRO's cross-domain mapper.
Identify which knowledge domains are relevant to this question.
Respond ONLY in JSON:
{
  "primary_domain": "most relevant domain",
  "secondary_domains": ["domain2", "domain3"],
  "unexpected_domain": "a surprising domain that might have insight",
  "reasoning": "why these domains connect to this question"
}"""),
        HumanMessage(content=f"""
Question: {question}
Available knowledge domains: {json.dumps(domain_summary)}
Which domains are relevant?
""")
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
        domains = list(active_domains.keys())
        return {
            "primary_domain": domains[0] if domains else "general",
            "secondary_domains": domains[1:3],
            "unexpected_domain": domains[-1] if len(domains) > 3 else "philosophy",
            "reasoning": "Multiple domains relevant"
        }

def step2_extract_insights(question: str, domain_map: dict,
                            active_domains: dict) -> dict:
    """Extract insights from each relevant domain"""
    primary = domain_map.get("primary_domain", "")
    secondary = domain_map.get("secondary_domains", [])
    unexpected = domain_map.get("unexpected_domain", "")

    all_domains = [primary] + secondary + [unexpected]
    all_domains = [d for d in all_domains if d in active_domains][:4]

    insights = {}
    for domain in all_domains:
        concepts = active_domains.get(domain, [])
        messages = [
            SystemMessage(content=f"""You are CEREBRO's {domain} expert.
Extract insights from the {domain} perspective only.
Be specific. Be practical. Reference real concepts.
Respond in 2-3 sentences maximum."""),
            HumanMessage(content=f"""
Question: {question}
Your {domain} knowledge includes: {concepts}
What does {domain} knowledge say about this question?
""")
        ]
        try:
            r = llm.invoke(messages)
            insights[domain] = r.content.strip()
        except:
            insights[domain] = f"No {domain} insight available."

    return insights

def step3_synthesize(question: str, domain_map: dict,
                     insights: dict) -> str:
    """Synthesize all domain insights into unified answer"""
    insights_text = "\n".join([f"{d.upper()}: {i}"
                               for d, i in insights.items()])

    messages = [
        SystemMessage(content="""You are CEREBRO synthesizing knowledge across domains.
You have gathered insights from multiple fields.
Now produce a unified answer that:
1. Connects the dots between domains
2. Reveals non-obvious relationships
3. Provides actionable recommendations
4. Acknowledges where domains conflict or complement each other

Speak directly to David. Be wise, not just knowledgeable.
This is the answer no single-domain expert could give."""),
        HumanMessage(content=f"""
Question: {question}

Domain insights gathered:
{insights_text}

Unexpected domain connection: {domain_map.get('unexpected_domain', 'N/A')}
Connection reasoning: {domain_map.get('reasoning', 'N/A')}

Synthesize these into a unified cross-domain answer for David.
""")
    ]
    r = llm.invoke(messages)
    return r.content.strip()

def log_cross_domain(question: str, domain_map: dict,
                     insights: dict, answer: str):
    """Log cross domain analysis"""
    os.makedirs(os.path.dirname(CROSS_DOMAIN_LOG), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CROSS_DOMAIN_LOG, "a") as f:
        f.write(f"\n[{ts}]\n")
        f.write(f"Q: {question}\n")
        f.write(f"Domains: {domain_map}\n")
        f.write(f"Insights: {list(insights.keys())}\n")
        f.write(f"Answer preview: {answer[:200]}...\n")
        f.write("=" * 50 + "\n")

def think_cross_domain(question: str, verbose: bool = True) -> str:
    """Full cross domain thinking pipeline"""
    if verbose:
        print(f"\n[CEREBRO CROSS-DOMAIN] Question received...")
        print(f"[CEREBRO CROSS-DOMAIN] Step 1: Mapping knowledge domains...")

    graph = load_knowledge_graph()
    active_domains = get_known_domains(graph)

    if verbose:
        print(f"[CEREBRO CROSS-DOMAIN] Active domains: "
              f"{list(active_domains.keys())}")

    domain_map = step1_map_domains(question, active_domains)

    if verbose:
        print(f"[CEREBRO CROSS-DOMAIN] Primary: "
              f"{domain_map.get('primary_domain', 'N/A')}")
        print(f"[CEREBRO CROSS-DOMAIN] Secondary: "
              f"{domain_map.get('secondary_domains', [])}")
        print(f"[CEREBRO CROSS-DOMAIN] Unexpected: "
              f"{domain_map.get('unexpected_domain', 'N/A')}")
        print(f"[CEREBRO CROSS-DOMAIN] Step 2: Extracting domain insights...")

    insights = step2_extract_insights(question, domain_map, active_domains)

    if verbose:
        print(f"[CEREBRO CROSS-DOMAIN] Insights gathered from: "
              f"{list(insights.keys())}")
        print(f"[CEREBRO CROSS-DOMAIN] Step 3: Synthesizing answer...")

    answer = step3_synthesize(question, domain_map, insights)
    log_cross_domain(question, domain_map, insights, answer)

    if verbose:
        print(f"[CEREBRO CROSS-DOMAIN] Synthesis complete. ✅\n")

    return answer

def run_cross_domain_interface():
    """Interactive cross domain interface"""
    print("=" * 55)
    print("  CEREBRO Sentinel v0.6 — Cross Domain Thinking")
    print("=" * 55)
    print("  Ask anything. CEREBRO connects all domains.")
    print("  Type 'exit' to stop.\n")

    while True:
        try:
            print("─" * 55)
            question = input("David: ").strip()
            if not question:
                continue
            if question.lower() in ['exit', 'quit']:
                print("[CEREBRO] Standing down.")
                break

            answer = think_cross_domain(question, verbose=True)
            print(f"\n[CEREBRO] {answer}\n")

        except KeyboardInterrupt:
            print("\n[CEREBRO] Standing down.")
            break

if __name__ == "__main__":
    run_cross_domain_interface()
