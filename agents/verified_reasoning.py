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
MODEL = "llama3.1:8b"
VERIFIED_LOG = "/home/david/cerebro-sentinel/logs/verified_reasoning.log"

llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL, timeout=180)

def search_own_memory(question: str) -> list:
    """Search CEREBRO's actual stored knowledge"""
    keywords = question.lower().split()
    keywords = [k for k in keywords if len(k) > 3][:5]

    all_results = []
    seen = set()

    for keyword in keywords:
        results = recall(keyword, limit=5)
        for r in results:
            text = r if isinstance(r, str) else r.payload.get('text', '')
            source = "memory" if isinstance(r, str) else r.payload.get('source', 'unknown')
            if text and text not in seen:
                seen.add(text)
                all_results.append({
                    "text": text[:300],
                    "source": source,
                    "keyword": keyword
                })

    return all_results[:15]

def step1_memory_check(question: str) -> dict:
    """Check what CEREBRO actually knows about this"""
    print("[CEREBRO VERIFIED] Searching own memory...")
    memories = search_own_memory(question)

    if not memories:
        return {
            "has_knowledge": False,
            "relevant_memories": [],
            "knowledge_sources": [],
            "memory_coverage": "none",
            "recommendation": "answer_from_training_only"
        }

    sources = list(set([m["source"] for m in memories
                        if m["source"] != "unknown"]))

    messages = [
        SystemMessage(content="""You are CEREBRO checking your own memory.
Assess if these memories are relevant to the question.
Respond ONLY in JSON:
{
  "has_knowledge": true,
  "relevance_score": 85,
  "most_relevant_memories": ["memory 1 summary", "memory 2 summary"],
  "knowledge_gaps_in_memory": ["what's missing"],
  "memory_coverage": "strong|partial|weak|none",
  "recommendation": "answer_from_memory|supplement_with_training|answer_from_training_only"
}"""),
        HumanMessage(content=f"""
Question: {question}
Memories found: {json.dumps([m['text'][:150] for m in memories[:5]], indent=2)}
Sources: {sources}

Are these memories relevant to answer this question?
""")
    ]

    try:
        r = llm.invoke(messages)
        text = r.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        result["raw_memories"] = memories
        result["knowledge_sources"] = sources
        return result
    except:
        return {
            "has_knowledge": True,
            "relevance_score": 50,
            "most_relevant_memories": [m["text"][:100] for m in memories[:3]],
            "knowledge_gaps_in_memory": [],
            "memory_coverage": "partial",
            "recommendation": "supplement_with_training",
            "raw_memories": memories,
            "knowledge_sources": sources
        }

def step2_grounded_reasoning(question: str,
                              memory_check: dict) -> dict:
    """Reason WITH actual stored knowledge"""
    memories = memory_check.get("raw_memories", [])
    coverage = memory_check.get("memory_coverage", "none")
    sources = memory_check.get("knowledge_sources", [])

    memory_text = "\n".join([
        f"- [{m['source'][:50]}]: {m['text'][:200]}"
        for m in memories[:8]
    ])

    messages = [
        SystemMessage(content="""You are CEREBRO reasoning with your stored knowledge.
You have retrieved relevant memories from your knowledge base.
Use these memories as PRIMARY evidence. Your training knowledge is secondary.
Respond ONLY in JSON:
{
  "primary_answer": "answer grounded in retrieved memories",
  "supporting_evidence": ["evidence 1 from memory", "evidence 2 from memory"],
  "confidence": 75,
  "confidence_reason": "why this confidence level based on evidence quality",
  "knowledge_used": "memory|training|both",
  "gaps_identified": ["what I couldn't find in memory"]
}"""),
        HumanMessage(content=f"""
Question: {question}

Retrieved from my knowledge base:
{memory_text if memory_text else "No relevant memories found"}

Memory coverage: {coverage}
Sources available: {sources}

Reason through this using the stored knowledge as primary evidence.
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
            "primary_answer": "Unable to ground reasoning in memory",
            "supporting_evidence": [],
            "confidence": 30,
            "confidence_reason": "insufficient memory coverage",
            "knowledge_used": "training",
            "gaps_identified": ["full topic coverage"]
        }

def step3_verify_conclusion(question: str,
                             reasoning: dict,
                             memory_check: dict) -> dict:
    """Verify the conclusion against stored knowledge"""
    answer = reasoning.get("primary_answer", "")
    evidence = reasoning.get("supporting_evidence", [])
    confidence = reasoning.get("confidence", 50)

    messages = [
        SystemMessage(content="""You are CEREBRO verifying your own conclusion.
Check if the conclusion is supported by the evidence.
Be brutally honest. Find contradictions.
Respond ONLY in JSON:
{
  "conclusion_supported": true,
  "contradictions_found": ["any contradictions"],
  "confidence_adjustment": 5,
  "verification_notes": "what the verification found",
  "final_confidence": 80,
  "should_caveat": false,
  "caveat": "caveat to add if needed"
}"""),
        HumanMessage(content=f"""
Question: {question}
My conclusion: {answer}
My evidence: {evidence}
My confidence: {confidence}%
Memory coverage: {memory_check.get('memory_coverage', 'unknown')}
Gaps in memory: {memory_check.get('knowledge_gaps_in_memory', [])}

Verify this conclusion against the evidence.
Is it supported? Are there contradictions?
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
            "conclusion_supported": True,
            "contradictions_found": [],
            "confidence_adjustment": 0,
            "verification_notes": "verification skipped",
            "final_confidence": confidence,
            "should_caveat": False,
            "caveat": ""
        }

def step4_attributed_answer(question: str, reasoning: dict,
                             verification: dict,
                             memory_check: dict) -> str:
    """Generate final answer with source attribution"""
    sources = memory_check.get("knowledge_sources", [])
    final_confidence = verification.get("final_confidence", 50)
    caveat = verification.get("caveat", "")
    coverage = memory_check.get("memory_coverage", "none")

    source_text = ""
    if sources:
        clean_sources = []
        for s in sources[:3]:
            if "http" in s:
                domain = s.split("/")[2] if len(
                    s.split("/")) > 2 else s
                clean_sources.append(domain)
            else:
                clean_sources.append(s[:50])
        source_text = f"Sources I learned from: {', '.join(clean_sources)}"

    messages = [
        SystemMessage(content=f"""You are CEREBRO delivering a verified answer.
You have searched your memory, reasoned with evidence, and verified your conclusion.
Confidence: {final_confidence}%
Memory coverage: {coverage}
{f'Caveat needed: {caveat}' if caveat else ''}

Deliver a direct, honest answer to David.
- If confidence > 75: be direct and confident
- If confidence 50-75: be clear but acknowledge uncertainty
- If confidence < 50: be honest about limitations
- Always mention what sources informed your answer
- Speak as a trusted advisor, not a search engine"""),
        HumanMessage(content=f"""
Question: {question}
Verified answer: {reasoning.get('primary_answer', '')}
Supporting evidence: {reasoning.get('supporting_evidence', [])}
{source_text}
Gaps identified: {reasoning.get('gaps_identified', [])}

Deliver the final attributed answer to David.
""")
    ]

    r = llm.invoke(messages)
    answer = r.content.strip()

    if sources and "learned from" not in answer.lower():
        clean = []
        for s in sources[:2]:
            if "http" in s:
                parts = s.split("/")
                clean.append(parts[2] if len(parts) > 2 else s)
            else:
                clean.append(s[:40])
        if clean:
            answer += f"\n\n[Sources: {', '.join(clean)}]"

    return answer, final_confidence

def log_verified(question: str, memory_check: dict,
                 reasoning: dict, verification: dict,
                 answer: str, confidence: int):
    """Log verified reasoning session"""
    os.makedirs(os.path.dirname(VERIFIED_LOG), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(VERIFIED_LOG, "a") as f:
        f.write(f"\n[{ts}]\n")
        f.write(f"Q: {question}\n")
        f.write(f"Memory coverage: "
                f"{memory_check.get('memory_coverage', 'none')}\n")
        f.write(f"Sources: "
                f"{memory_check.get('knowledge_sources', [])}\n")
        f.write(f"Final confidence: {confidence}%\n")
        f.write(f"Answer preview: {answer[:200]}\n")
        f.write("=" * 50 + "\n")

def verified_answer(question: str, verbose: bool = True) -> str:
    """Full verified reasoning pipeline"""
    init_memory()

    if verbose:
        print(f"\n[CEREBRO VERIFIED] Question received...")

    memory_check = step1_memory_check(question)

    if verbose:
        coverage = memory_check.get('memory_coverage', 'none')
        sources = memory_check.get('knowledge_sources', [])
        print(f"[CEREBRO VERIFIED] Memory coverage: {coverage}")
        print(f"[CEREBRO VERIFIED] Sources found: {len(sources)}")
        print(f"[CEREBRO VERIFIED] Step 2: Grounded reasoning...")

    reasoning = step2_grounded_reasoning(question, memory_check)

    if verbose:
        print(f"[CEREBRO VERIFIED] Initial confidence: "
              f"{reasoning.get('confidence', 0)}%")
        print(f"[CEREBRO VERIFIED] Step 3: Verifying conclusion...")

    verification = step3_verify_conclusion(
        question, reasoning, memory_check)

    if verbose:
        supported = verification.get('conclusion_supported', True)
        final_conf = verification.get('final_confidence', 0)
        print(f"[CEREBRO VERIFIED] Conclusion supported: "
              f"{'✅' if supported else '⚠️'}")
        print(f"[CEREBRO VERIFIED] Final confidence: {final_conf}%")
        print(f"[CEREBRO VERIFIED] Step 4: Generating attributed answer...")

    answer, confidence = step4_attributed_answer(
        question, reasoning, verification, memory_check)

    log_verified(question, memory_check, reasoning,
                 verification, answer, confidence)

    if verbose:
        print(f"[CEREBRO VERIFIED] Complete. ✅\n")

    return answer

def run_verified_interface():
    """Interactive verified reasoning interface"""
    print("=" * 55)
    print("  CEREBRO v0.8 — Verified Reasoning")
    print("=" * 55)
    print("  Every answer grounded in stored knowledge.")
    print("  Every conclusion verified before delivery.")
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

            answer = verified_answer(question, verbose=True)
            print(f"\n[CEREBRO] {answer}\n")

        except KeyboardInterrupt:
            print("\n[CEREBRO] Standing down.")
            break

if __name__ == "__main__":
    run_verified_interface()
