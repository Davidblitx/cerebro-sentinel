import sys
import os
import json
import datetime
sys.path.append('/home/david/cerebro-sentinel/agents')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://localhost:11434"
MODEL = "cerebro-v1"
REASONING_LOG = "/home/david/cerebro-sentinel/logs/reasoning.log"

llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL, timeout=180)

def log_reasoning(question: str, chain: dict):
    os.makedirs(os.path.dirname(REASONING_LOG), exist_ok=True)
    with open(REASONING_LOG, "a") as f:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{ts}]\nQ: {question}\n{json.dumps(chain, indent=2)}\n{'='*50}\n")

def step1_understand(question: str) -> dict:
    """What is actually being asked?"""
    messages = [
        SystemMessage(content="""You are CEREBRO's reasoning engine.
Analyze the question deeply. Respond ONLY in JSON:
{
  "core_question": "the fundamental question being asked",
  "domain": "what field/domain this belongs to",
  "complexity": "simple|moderate|complex|requires_research",
  "what_i_know": "what I already know about this",
  "what_i_dont_know": "what I'm uncertain about",
  "assumptions": ["assumption 1", "assumption 2"]
}"""),
        HumanMessage(content=f"Analyze this question: {question}")
    ]
    try:
        r = llm.invoke(messages)
        text = r.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        return json.loads(text.strip())
    except:
        return {"core_question": question, "domain": "general",
                "complexity": "moderate", "what_i_know": "",
                "what_i_dont_know": "", "assumptions": []}

def step2_hypothesize(question: str, understanding: dict) -> dict:
    """Generate multiple possible answers"""
    messages = [
        SystemMessage(content="""You are CEREBRO generating hypotheses.
Generate multiple possible answers before committing to one.
Respond ONLY in JSON:
{
  "hypothesis_1": {"answer": "first possible answer", "confidence": 70, "reasoning": "why"},
  "hypothesis_2": {"answer": "second possible answer", "confidence": 60, "reasoning": "why"},
  "hypothesis_3": {"answer": "third possible answer", "confidence": 40, "reasoning": "why"},
  "most_likely": "hypothesis_1"
}"""),
        HumanMessage(content=f"""
Question: {question}
What I know: {understanding.get('what_i_know', '')}
Domain: {understanding.get('domain', '')}

Generate 3 possible answers with confidence levels.
""")
    ]
    try:
        r = llm.invoke(messages)
        text = r.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        return json.loads(text.strip())
    except:
        return {"hypothesis_1": {"answer": "unknown", "confidence": 50,
                "reasoning": "insufficient data"}, "most_likely": "hypothesis_1"}

def step3_stress_test(question: str, hypotheses: dict) -> dict:
    """Challenge each hypothesis — find the weaknesses"""
    best = hypotheses.get("most_likely", "hypothesis_1")
    best_answer = hypotheses.get(best, {}).get("answer", "")

    messages = [
        SystemMessage(content="""You are CEREBRO stress-testing an answer.
Find every way this answer could be wrong.
Respond ONLY in JSON:
{
  "weaknesses": ["weakness 1", "weakness 2"],
  "counter_arguments": ["counter 1", "counter 2"],
  "missing_context": ["what context would change this answer"],
  "confidence_adjustment": -10,
  "survives_stress_test": true
}"""),
        HumanMessage(content=f"""
Question: {question}
Best answer: {best_answer}

Challenge this answer. Find its weaknesses.
""")
    ]
    try:
        r = llm.invoke(messages)
        text = r.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"): text = text[4:]
        return json.loads(text.strip())
    except:
        return {"weaknesses": [], "counter_arguments": [],
                "missing_context": [], "confidence_adjustment": 0,
                "survives_stress_test": True}

def step4_synthesize(question: str, understanding: dict,
                     hypotheses: dict, stress_test: dict) -> str:
    """Produce the final verified answer"""
    best = hypotheses.get("most_likely", "hypothesis_1")
    best_hypothesis = hypotheses.get(best, {})
    base_confidence = best_hypothesis.get("confidence", 50)
    adjustment = stress_test.get("confidence_adjustment", 0)
    final_confidence = max(10, min(99, base_confidence + adjustment))

    messages = [
        SystemMessage(content="""You are CEREBRO delivering a final answer.
You have thought deeply. You have challenged yourself.
Now deliver the answer with wisdom and clarity.
Be direct. Be specific. Acknowledge uncertainty where it exists.
Speak as a trusted advisor to David — not as a chatbot."""),
        HumanMessage(content=f"""
Original question: {question}

My analysis:
- Core question: {understanding.get('core_question', '')}
- Best answer after reasoning: {best_hypothesis.get('answer', '')}
- Weaknesses found: {stress_test.get('weaknesses', [])}
- Confidence level: {final_confidence}%
- Survives stress test: {stress_test.get('survives_stress_test', True)}

Deliver the final answer to David. Be direct and wise.
If confidence is below 60%, acknowledge the uncertainty clearly.
""")
    ]
    r = llm.invoke(messages)
    return r.content.strip(), final_confidence

def reason(question: str, verbose: bool = True) -> str:
    """Full reasoning chain — the thinking process"""
    if verbose:
        print(f"\n[CEREBRO REASONING] Question received...")
        print(f"[CEREBRO REASONING] Step 1: Understanding the question...")

    understanding = step1_understand(question)

    if verbose:
        print(f"[CEREBRO REASONING] Domain: {understanding.get('domain', '?')}")
        print(f"[CEREBRO REASONING] Complexity: {understanding.get('complexity', '?')}")
        print(f"[CEREBRO REASONING] Step 2: Generating hypotheses...")

    hypotheses = step2_hypothesize(question, understanding)

    if verbose:
        print(f"[CEREBRO REASONING] Step 3: Stress testing best answer...")

    stress_test = step3_stress_test(question, hypotheses)

    if verbose:
        survives = stress_test.get('survives_stress_test', True)
        print(f"[CEREBRO REASONING] Stress test: {'PASSED ✅' if survives else 'FAILED — revising ⚠️'}")
        print(f"[CEREBRO REASONING] Step 4: Synthesizing final answer...")

    answer, confidence = step4_synthesize(question, understanding, hypotheses, stress_test)

    chain = {
        "question": question,
        "understanding": understanding,
        "hypotheses": hypotheses,
        "stress_test": stress_test,
        "confidence": confidence
    }
    log_reasoning(question, chain)

    if verbose:
        print(f"[CEREBRO REASONING] Confidence: {confidence}%")
        print(f"[CEREBRO REASONING] Complete. ✅\n")

    return answer

def run_reasoning_interface():
    """Interactive reasoning interface"""
    print("=" * 55)
    print("  CEREBRO Sentinel v0.6 — Reasoning Engine")
    print("=" * 55)
    print("  Ask anything. CEREBRO thinks before answering.")
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

            answer = reason(question, verbose=True)
            print(f"\n[CEREBRO] {answer}\n")

        except KeyboardInterrupt:
            print("\n[CEREBRO] Standing down.")
            break

if __name__ == "__main__":
    run_reasoning_interface()
