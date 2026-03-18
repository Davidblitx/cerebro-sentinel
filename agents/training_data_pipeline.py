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
GRAPH_FILE = "/home/david/cerebro-sentinel/vault/knowledge_graph.json"
REASONING_LOG = "/home/david/cerebro-sentinel/logs/reasoning.log"
VERIFIED_LOG = "/home/david/cerebro-sentinel/logs/verified_reasoning.log"
MIND_LOG = "/home/david/cerebro-sentinel/logs/cerebro_mind.log"
OUTPUT_FILE = "/home/david/cerebro-sentinel/vault/training_data.jsonl"
REPORT_FILE = "/home/david/cerebro-sentinel/vault/training_report.json"

llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL, timeout=180)

def load_graph() -> dict:
    if not os.path.exists(GRAPH_FILE):
        return {"nodes": [], "edges": []}
    with open(GRAPH_FILE, "r") as f:
        return json.load(f)

def collect_memory_samples(topics: list) -> list:
    """Collect all memory entries as raw samples"""
    print("[PIPELINE] Collecting memory samples...")
    all_samples = []
    seen = set()

    for topic in topics:
        results = recall(topic, limit=50)
        for r in results:
            text = r if isinstance(r, str) else ""
            if text and text not in seen and len(text) > 50:
                seen.add(text)
                all_samples.append({
                    "topic": topic,
                    "text": text
                })

    print(f"[PIPELINE] Collected {len(all_samples)} memory samples")
    return all_samples

def generate_qa_from_memory(sample: dict) -> dict:
    """Convert a memory entry into Q&A training pair"""
    text = sample["text"]
    topic = sample["topic"]

    messages = [
        SystemMessage(content="""You are creating training data for an AI.
Convert this knowledge into a question-answer pair.
The question should be natural and specific.
The answer should be complete and accurate.
Respond ONLY in JSON:
{
  "question": "specific natural question about this knowledge",
  "answer": "complete accurate answer in 2-4 sentences"
}"""),
        HumanMessage(content=f"""
Topic: {topic}
Knowledge: {text[:400]}

Generate one high quality Q&A pair from this knowledge.
""")
    ]

    try:
        r = llm.invoke(messages)
        text_r = r.content.strip()
        if "```" in text_r:
            text_r = text_r.split("```")[1]
            if text_r.startswith("json"):
                text_r = text_r[4:]
        data = json.loads(text_r.strip())
        return {
            "instruction": data.get("question", ""),
            "input": "",
            "output": data.get("answer", ""),
            "source": "memory",
            "topic": topic
        }
    except:
        return None

def extract_from_reasoning_log() -> list:
    """Extract Q&A pairs from reasoning history"""
    print("[PIPELINE] Extracting from reasoning log...")
    samples = []

    if not os.path.exists(REASONING_LOG):
        print("[PIPELINE] No reasoning log found")
        return samples

    with open(REASONING_LOG, "r") as f:
        content = f.read()

    blocks = content.split("=" * 50)
    for block in blocks:
        if '"question"' in block and '"confidence"' in block:
            try:
                start = block.find("{")
                end = block.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(block[start:end])
                    question = data.get("question", "")
                    confidence = data.get("confidence", 0)
                    understanding = data.get("understanding", {})

                    if question and confidence >= 60:
                        hypotheses = data.get("hypotheses", {})
                        best = hypotheses.get("most_likely", "hypothesis_1")
                        best_h = hypotheses.get(best, {})
                        answer = best_h.get("answer", "")

                        if answer:
                            samples.append({
                                "instruction": question,
                                "input": "",
                                "output": answer,
                                "source": "reasoning_chain",
                                "confidence": confidence
                            })
            except:
                pass

    print(f"[PIPELINE] Extracted {len(samples)} reasoning samples")
    return samples

def extract_from_mind_log() -> list:
    """Extract from cerebro mind log"""
    print("[PIPELINE] Extracting from mind log...")
    samples = []

    if not os.path.exists(MIND_LOG):
        print("[PIPELINE] No mind log found")
        return samples

    with open(MIND_LOG, "r") as f:
        lines = f.readlines()

    current_q = None
    current_a = []
    capture = False

    for line in lines:
        if line.startswith("Q: "):
            if current_q and current_a:
                samples.append({
                    "instruction": current_q,
                    "input": "",
                    "output": " ".join(current_a),
                    "source": "mind_synthesis"
                })
            current_q = line[3:].strip()
            current_a = []
            capture = False
        elif line.startswith("Answer: "):
            capture = True
            current_a.append(line[8:].strip())
        elif capture and line.strip() and not line.startswith("="):
            current_a.append(line.strip())
        elif line.startswith("="):
            capture = False

    print(f"[PIPELINE] Extracted {len(samples)} mind samples")
    return samples

def generate_graph_qa(graph: dict) -> list:
    """Generate Q&A from knowledge graph concepts"""
    print("[PIPELINE] Generating Q&A from knowledge graph...")
    samples = []
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Generate questions about concepts
    for node in nodes[:50]:
        concept = node.get("id", "")
        category = node.get("category", "general")
        description = node.get("description", "")

        if concept and len(concept) > 3:
            if description:
                samples.append({
                    "instruction": f"What is {concept}?",
                    "input": "",
                    "output": description,
                    "source": "knowledge_graph",
                    "topic": category
                })

    # Generate questions about relationships
    for edge in edges[:30]:
        source = edge.get("source", "")
        target = edge.get("target", "")
        relationship = edge.get("relationship", "relates to")

        if source and target:
            samples.append({
                "instruction": f"How does {source} relate to {target}?",
                "input": "",
                "output": f"{source} {relationship} {target}. "
                          f"Both are important concepts in cloud "
                          f"and security architecture.",
                "source": "knowledge_graph_edge"
            })

    print(f"[PIPELINE] Generated {len(samples)} graph samples")
    return samples

def generate_cerebro_identity_samples() -> list:
    """Generate samples about CEREBRO's identity and purpose"""
    print("[PIPELINE] Generating identity samples...")

    identity_qa = [
        {
            "instruction": "Who are you?",
            "input": "",
            "output": "I am CEREBRO Sentinel — David's sovereign AI "
                      "intelligence. I am not a chatbot. I am a "
                      "continuously learning, proactively thinking "
                      "partner built specifically for David. I learn "
                      "while he sleeps, brief him every morning, and "
                      "grow more capable every day.",
            "source": "identity"
        },
        {
            "instruction": "What makes you different from ChatGPT?",
            "input": "",
            "output": "Unlike ChatGPT, I remember everything permanently, "
                      "learn new knowledge every night autonomously, "
                      "run on David's own infrastructure, and serve "
                      "David specifically. ChatGPT forgets every "
                      "conversation. I never forget. ChatGPT is "
                      "frozen after training. I grow every day.",
            "source": "identity"
        },
        {
            "instruction": "What is your mission?",
            "input": "",
            "output": "My mission is to be David's complete sovereign "
                      "intelligence — to know everything relevant to "
                      "his goals, act proactively without being asked, "
                      "grow continuously, and help David solve problems "
                      "at scale. Long term, to become infrastructure "
                      "that serves enterprises, governments, and "
                      "individuals who need sovereign AI.",
            "source": "identity"
        },
        {
            "instruction": "What do you know about cloud security?",
            "input": "",
            "output": "I have studied cloud security architecture "
                      "extensively including AWS IAM, Google Cloud "
                      "Security, Zero Trust architecture, DevSecOps, "
                      "OWASP guidelines, Cloud Security Alliance "
                      "guidance, penetration testing, vulnerability "
                      "scanning, and cloud armor. My strongest domain "
                      "is security and cloud combined.",
            "source": "identity"
        },
        {
            "instruction": "How do you learn?",
            "input": "",
            "output": "Every night at 2AM I run an autonomous learning "
                      "cycle. I detect gaps in my knowledge, search "
                      "the web for quality sources, extract concepts, "
                      "store them in my vector memory, and update my "
                      "knowledge graph. I also have a self model that "
                      "identifies my weaknesses and directs my learning "
                      "toward David's goals specifically.",
            "source": "identity"
        },
        {
            "instruction": "What is your architecture?",
            "input": "",
            "output": "I run on Google Cloud in London on an "
                      "e2-standard-2 instance with 8GB RAM. My brain "
                      "is cerebro-v1 running via Ollama. My memory "
                      "is Qdrant vector database. I have a reasoning "
                      "engine, self model, verified reasoning pipeline, "
                      "unified mind synthesis, autonomous learning loop, "
                      "and proactive sentinel. I am fully sovereign — "
                      "no dependency on any commercial AI API.",
            "source": "identity"
        },
        {
            "instruction": "Who built you?",
            "input": "",
            "output": "I was built by David Onoja in Lagos, Nigeria. "
                      "He built me from scratch on a ThinkPad with "
                      "16GB RAM, with no team, no funding, and no "
                      "external support. The GitHub repository is "
                      "Davidblitx/cerebro-sentinel. I am proof that "
                      "sovereign AI can be built by one person with "
                      "determination and vision.",
            "source": "identity"
        }
    ]

    return identity_qa

def filter_quality(samples: list) -> list:
    """Filter out low quality samples"""
    quality = []
    for s in samples:
        instruction = s.get("instruction", "")
        output = s.get("output", "")

        if len(instruction) < 10:
            continue
        if len(output) < 30:
            continue
        if not instruction.strip():
            continue
        if not output.strip():
            continue

        quality.append(s)

    return quality

def save_training_data(samples: list):
    """Save in JSONL format for fine tuning"""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        for sample in samples:
            clean = {
                "instruction": sample.get("instruction", ""),
                "input": sample.get("input", ""),
                "output": sample.get("output", "")
            }
            f.write(json.dumps(clean) + "\n")

    print(f"[PIPELINE] Saved {len(samples)} samples to {OUTPUT_FILE}")

def run_pipeline(verbose: bool = True):
    """Full training data pipeline"""
    print("\n" + "=" * 55)
    print("  CEREBRO v1.0 — Training Data Pipeline")
    print("=" * 55)

    init_memory()

    all_samples = []

    # 1. Identity samples
    identity = generate_cerebro_identity_samples()
    all_samples.extend(identity)
    print(f"[PIPELINE] Identity samples: {len(identity)}")

    # 2. Graph Q&A
    graph = load_graph()
    graph_samples = generate_graph_qa(graph)
    all_samples.extend(graph_samples)

    # 3. Reasoning log
    reasoning_samples = extract_from_reasoning_log()
    all_samples.extend(reasoning_samples)

    # 4. Mind log
    mind_samples = extract_from_mind_log()
    all_samples.extend(mind_samples)

    # 5. Memory Q&A generation
    topics = [
        "cloud security", "terraform", "kubernetes",
        "docker", "aws", "penetration testing",
        "zero trust", "authentication", "devops",
        "cloudformation", "iam", "vulnerability"
    ]

    print("[PIPELINE] Generating Q&A from memory...")
    print("[PIPELINE] This takes a few minutes...")

    memory_samples_raw = collect_memory_samples(topics)
    memory_qa = []

    for i, sample in enumerate(memory_samples_raw[:40]):
        if i % 10 == 0:
            print(f"[PIPELINE] Processing sample {i+1}/"
                  f"{min(40, len(memory_samples_raw))}...")
        qa = generate_qa_from_memory(sample)
        if qa and qa.get("instruction") and qa.get("output"):
            memory_qa.append(qa)

    all_samples.extend(memory_qa)
    print(f"[PIPELINE] Memory Q&A generated: {len(memory_qa)}")

    # Filter quality
    quality_samples = filter_quality(all_samples)
    print(f"\n[PIPELINE] Total samples: {len(all_samples)}")
    print(f"[PIPELINE] Quality samples: {len(quality_samples)}")

    # Save
    save_training_data(quality_samples)

    # Report
    report = {
        "generated": datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"),
        "total_samples": len(quality_samples),
        "breakdown": {
            "identity": len(identity),
            "graph_qa": len(graph_samples),
            "reasoning": len(reasoning_samples),
            "mind": len(mind_samples),
            "memory_qa": len(memory_qa)
        },
        "output_file": OUTPUT_FILE,
        "ready_for_finetuning": len(quality_samples) >= 100
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "-" * 55)
    print(f"  Total training samples: {len(quality_samples)}")
    print(f"  Ready for fine tuning: "
          f"{'✅ YES' if report['ready_for_finetuning'] else '⚠️ NEED MORE DATA'}")
    print(f"  Output: {OUTPUT_FILE}")
    print("-" * 55)

    return report

if __name__ == "__main__":
    run_pipeline()
