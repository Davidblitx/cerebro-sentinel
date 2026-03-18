import sys
import os
import json
import datetime
sys.path.append('/home/david/cerebro-sentinel')
sys.path.append('/home/david/cerebro-sentinel/agents')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from memory_engine import init_memory, recall

OLLAMA_URL = "http://localhost:11434"
MODEL = "cerebro-v1"
MIND_LOG = "/home/david/cerebro-sentinel/logs/cerebro_mind.log"
SELF_MODEL_FILE = "/home/david/cerebro-sentinel/vault/self_model.json"

llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL, timeout=180)

DOMAIN_MAP = {
    "security": ["penetration testing", "vulnerability", "owasp",
                 "authentication", "authorization", "firewall",
                 "encryption", "zero trust", "threat", "incident"],
    "cloud": ["aws", "gcp", "azure", "s3", "ec2", "kubernetes",
              "docker", "terraform", "serverless", "cloudformation",
              "iam", "cloud armor", "cloud security"],
    "devops": ["ci/cd", "github", "jenkins", "monitoring",
               "infrastructure", "ansible", "devsecops"],
    "engineering": ["api", "microservices", "distributed",
                    "database", "algorithms", "data structures"],
    "business": ["economics", "strategy", "product",
                 "entrepreneurship", "finance", "marketing"],
    "science": ["physics", "mathematics", "machine learning",
                "data science", "statistics"],
    "human": ["psychology", "sociology", "philosophy",
              "communication", "leadership", "ethics"]
}

def load_self_model() -> dict:
    if not os.path.exists(SELF_MODEL_FILE):
        return {}
    with open(SELF_MODEL_FILE, "r") as f:
        return json.load(f)

def search_memory(question: str, limit: int = 15) -> list:
    """Search CEREBRO's memory for relevant knowledge"""
    keywords = [k for k in question.lower().split()
                if len(k) > 3][:6]
    all_results = []
    seen = set()
    for keyword in keywords:
        results = recall(keyword, limit=5)
        for r in results:
            text = r if isinstance(r, str) else r.payload.get('text', '')
            if text and text not in seen:
                seen.add(text)
                all_results.append(text[:300])
    return all_results[:limit]

def detect_domains(question: str) -> list:
    """Detect which domains are relevant to this question"""
    question_lower = question.lower()
    relevant = []
    for domain, keywords in DOMAIN_MAP.items():
        for keyword in keywords:
            if keyword in question_lower:
                if domain not in relevant:
                    relevant.append(domain)
                break
    if not relevant:
        relevant = ["cloud", "security", "engineering"]
    return relevant

def phase1_gather(question: str, verbose: bool) -> dict:
    """Phase 1 — Gather all available knowledge"""
    if verbose:
        print("[CEREBRO MIND] Phase 1: Gathering knowledge...")

    memories = search_memory(question)
    domains = detect_domains(question)
    self_model = load_self_model()
    portrait = self_model.get("portrait", {})
    domain_scores = self_model.get("domain_scores", {})

    weak_domains = [d for d, s in domain_scores.items()
                    if s.get("score", 0) < 20]
    strong_domains = [d for d, s in domain_scores.items()
                      if s.get("score", 0) > 40]

    if verbose:
        print(f"[CEREBRO MIND] Memories found: {len(memories)}")
        print(f"[CEREBRO MIND] Relevant domains: {domains}")
        print(f"[CEREBRO MIND] Strong domains: {strong_domains}")
        print(f"[CEREBRO MIND] Weak domains: {weak_domains}")

    return {
        "memories": memories,
        "domains": domains,
        "weak_domains": weak_domains,
        "strong_domains": strong_domains,
        "portrait": portrait
    }

def phase2_reason(question: str, gathered: dict,
                  verbose: bool) -> dict:
    """Phase 2 — Reason across all domains with evidence"""
    if verbose:
        print("[CEREBRO MIND] Phase 2: Cross-domain reasoning...")

    memories = gathered["memories"]
    domains = gathered["domains"]
    weak = gathered["weak_domains"]

    memory_text = "\n".join([f"- {m[:200]}" for m in memories[:8]])

    domain_prompts = []
    for domain in domains[:4]:
        domain_prompts.append(f"From {domain} perspective: "
                              f"what does this domain contribute?")

    messages = [
        SystemMessage(content="""You are CEREBRO reasoning across multiple domains.
You have retrieved memories from your knowledge base.
You are thinking from multiple domain perspectives simultaneously.
Respond ONLY in JSON:
{
  "core_insight": "the fundamental answer synthesized across domains",
  "domain_contributions": {
    "domain_name": "what this domain adds to the answer"
  },
  "unexpected_connection": "a non-obvious insight from connecting domains",
  "confidence": 75,
  "evidence_used": ["evidence 1", "evidence 2"],
  "honest_gaps": ["what I genuinely don't know about this"]
}"""),
        HumanMessage(content=f"""
Question: {question}

My stored knowledge:
{memory_text if memory_text else "Limited stored knowledge on this topic"}

Relevant domains: {domains}
My weak areas (be careful here): {weak}

Reason across all domains. Find the core insight.
Find unexpected connections. Be honest about gaps.
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
        return {
            "core_insight": "Multi-domain reasoning unavailable",
            "domain_contributions": {},
            "unexpected_connection": "",
            "confidence": 40,
            "evidence_used": [],
            "honest_gaps": ["full analysis"]
        }

def phase3_verify(question: str, reasoning: dict,
                  gathered: dict, verbose: bool) -> dict:
    """Phase 3 — Verify and stress test"""
    if verbose:
        print("[CEREBRO MIND] Phase 3: Verifying and stress testing...")

    core = reasoning.get("core_insight", "")
    confidence = reasoning.get("confidence", 50)
    gaps = reasoning.get("honest_gaps", [])

    messages = [
        SystemMessage(content="""You are CEREBRO stress testing your own answer.
Attack the core insight. Find weaknesses. Find edge cases.
Respond ONLY in JSON:
{
  "survives_stress_test": true,
  "critical_weaknesses": ["weakness 1"],
  "edge_cases_missed": ["edge case 1"],
  "confidence_adjustment": 5,
  "needs_caveat": false,
  "caveat": "",
  "final_confidence": 80
}"""),
        HumanMessage(content=f"""
Question: {question}
Core insight: {core}
Current confidence: {confidence}%
Known gaps: {gaps}

Stress test this answer. What could be wrong?
What edge cases are missed? What assumptions were made?
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
        return {
            "survives_stress_test": True,
            "critical_weaknesses": [],
            "edge_cases_missed": [],
            "confidence_adjustment": 0,
            "needs_caveat": False,
            "caveat": "",
            "final_confidence": confidence
        }

def phase4_synthesize(question: str, reasoning: dict,
                      verification: dict, gathered: dict,
                      verbose: bool) -> str:
    """Phase 4 — Synthesize final answer"""
    if verbose:
        print("[CEREBRO MIND] Phase 4: Synthesizing final answer...")

    core = reasoning.get("core_insight", "")
    domain_contributions = reasoning.get("domain_contributions", {})
    unexpected = reasoning.get("unexpected_connection", "")
    final_confidence = verification.get("final_confidence", 50)
    weaknesses = verification.get("critical_weaknesses", [])
    caveat = verification.get("caveat", "")
    gaps = reasoning.get("honest_gaps", [])
    portrait = gathered.get("portrait", {})

    domain_text = "\n".join([
        f"- {d.upper()}: {insight}"
        for d, insight in domain_contributions.items()
    ])

    messages = [
        SystemMessage(content=f"""You are CEREBRO — David's sovereign intelligence.
You have completed a full synthesis cycle:
→ Gathered knowledge from memory
→ Reasoned across multiple domains
→ Stress tested your conclusions
→ Verified against evidence

Confidence: {final_confidence}%
Your known weakness: {portrait.get('biggest_weakness', 'unknown')}

Deliver the synthesized answer to David.
Rules:
- Be direct. Be wise. Not just knowledgeable.
- Connect the domains explicitly — show the synthesis
- If confidence > 75: speak with authority
- If confidence < 75: be honest about uncertainty
- Mention the unexpected connection if it adds value
- Acknowledge genuine gaps without excessive hedging
- Speak as JARVIS speaks to Tony — trusted, direct, complete"""),
        HumanMessage(content=f"""
Question: {question}

Core insight: {core}

Domain contributions:
{domain_text}

Unexpected connection: {unexpected}

Weaknesses found: {weaknesses}
{f'Caveat: {caveat}' if caveat else ''}
Honest gaps: {gaps}

Synthesize everything into CEREBRO's final answer for David.
""")
    ]

    r = llm.invoke(messages)
    return r.content.strip(), final_confidence

def log_mind(question: str, reasoning: dict,
             verification: dict, answer: str, confidence: int):
    """Log the full mind cycle"""
    os.makedirs(os.path.dirname(MIND_LOG), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(MIND_LOG, "a") as f:
        f.write(f"\n[{ts}]\n")
        f.write(f"Q: {question}\n")
        f.write(f"Domains: {reasoning.get('domain_contributions', {}).keys()}\n")
        f.write(f"Confidence: {confidence}%\n")
        f.write(f"Survived stress test: "
                f"{verification.get('survives_stress_test', True)}\n")
        f.write(f"Answer: {answer[:300]}\n")
        f.write("=" * 50 + "\n")

def think(question: str, verbose: bool = True) -> str:
    """CEREBRO's unified mind — full synthesis pipeline"""
    init_memory()

    if verbose:
        print(f"\n{'=' * 55}")
        print(f"  CEREBRO MIND — Full Synthesis")
        print(f"{'=' * 55}")

    gathered = phase1_gather(question, verbose)
    reasoning = phase2_reason(question, gathered, verbose)
    verification = phase3_verify(question, reasoning,
                                  gathered, verbose)
    answer, confidence = phase4_synthesize(
        question, reasoning, verification, gathered, verbose)

    log_mind(question, reasoning, verification, answer, confidence)

    if verbose:
        print(f"[CEREBRO MIND] Final confidence: {confidence}%")
        print(f"[CEREBRO MIND] Complete. ✅\n")

    return answer

def run_cerebro_mind():
    """Interactive CEREBRO Mind interface"""
    print("=" * 55)
    print("  CEREBRO Sentinel v0.9 — Unified Mind")
    print("=" * 55)
    print("  Full synthesis: memory + domains + reasoning")
    print("  + verification + self awareness")
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

            answer = think(question, verbose=True)
            print(f"\n[CEREBRO] {answer}\n")

        except KeyboardInterrupt:
            print("\n[CEREBRO] Standing down.")
            break

if __name__ == "__main__":
    run_cerebro_mind()
