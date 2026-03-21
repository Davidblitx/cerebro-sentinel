import sys
import json
import os
sys.path.append('/home/david/cerebro-sentinel/agents')
sys.path.append('/home/david/cerebro-sentinel/learning/graph')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from memory_engine import init_memory, recall_formatted

OLLAMA_URL = "http://localhost:11434"
GAPS_FILE = "/home/david/cerebro-sentinel/vault/knowledge_gaps.json"
GRAPH_FILE = "/home/david/cerebro-sentinel/vault/knowledge_graph.json"

llm = ChatOllama(model="cerebro-v1", base_url=OLLAMA_URL, timeout=120)

# NEW CURRICULUM — AI & World Intelligence
MASTER_CURRICULUM = {
    "ai_fundamentals": [
        "machine learning", "deep learning", "neural networks",
        "supervised learning", "unsupervised learning", "reinforcement learning",
        "transformer architecture", "attention mechanism", "backpropagation",
        "gradient descent", "overfitting", "regularization",
        "feature engineering", "model evaluation", "cross validation"
    ],
    "large_language_models": [
        "large language models", "GPT architecture", "BERT",
        "tokenization", "embeddings", "fine tuning",
        "prompt engineering", "RAG retrieval augmented generation",
        "context window", "temperature sampling", "RLHF",
        "instruction tuning", "chain of thought reasoning",
        "few shot learning", "zero shot learning"
    ],
    "ai_companies_research": [
        "OpenAI GPT5", "Anthropic Claude", "Google Gemini",
        "Meta Llama", "xAI Grok", "Mistral AI",
        "DeepSeek China AI", "Baidu ERNIE", "Alibaba Qwen",
        "AI safety research", "AI alignment problem",
        "compute scaling laws", "emergent capabilities",
        "AI regulation policy", "EU AI Act"
    ],
    "superintelligence": [
        "artificial general intelligence", "superintelligence",
        "intelligence explosion", "recursive self improvement",
        "AI consciousness", "chinese room argument",
        "orthogonality thesis", "instrumental convergence",
        "friendly AI", "control problem", "corrigibility",
        "whole brain emulation", "cognitive architecture",
        "WKU wisdom knowledge understanding", "sovereign AI"
    ],
    "ai_infrastructure": [
        "GPU computing", "CUDA programming", "TPU architecture",
        "distributed training", "model parallelism",
        "quantization", "pruning", "knowledge distillation",
        "ONNX", "TensorRT", "vLLM inference",
        "vector databases", "semantic search",
        "Hugging Face ecosystem", "Ollama local deployment"
    ],
    "chatbots_agents": [
        "chatbot architecture", "dialogue management",
        "intent recognition", "entity extraction",
        "conversational AI", "AI agents",
        "autonomous agents", "multi agent systems",
        "LangChain framework", "LangGraph",
        "tool use function calling", "agentic loops",
        "memory systems", "planning algorithms"
    ],
    "ai_world_impact": [
        "AI in healthcare", "AI in finance",
        "AI in education", "AI in agriculture",
        "AI in Africa", "AI economic impact",
        "job displacement automation", "AI inequality",
        "open source AI movement", "AI ethics",
        "bias in AI", "explainable AI",
        "AI governance", "digital sovereignty"
    ],
    "ml_engineering": [
        "MLOps", "model deployment", "model monitoring",
        "data pipeline", "feature store", "model registry",
        "A/B testing models", "continuous training",
        "experiment tracking", "model serving",
        "FastAPI ML deployment", "Docker ML containers"
    ]
}

def get_known_concepts() -> list:
    """Get all concepts Cerebro currently knows from graph"""
    if not os.path.exists(GRAPH_FILE):
        return []
    with open(GRAPH_FILE, "r") as f:
        data = json.load(f)
    return [node["id"].lower() for node in data.get("nodes", [])]

def detect_gaps() -> dict:
    """Find what Cerebro doesn't know yet"""
    known = get_known_concepts()
    gaps = {}

    for domain, topics in MASTER_CURRICULUM.items():
        domain_gaps = []
        for topic in topics:
            # Check if topic or similar concept exists
            topic_known = any(
                topic.lower() in known_concept or
                known_concept in topic.lower()
                for known_concept in known
            )
            if not topic_known:
                domain_gaps.append(topic)

        if domain_gaps:
            gaps[domain] = domain_gaps

    return gaps

def prioritize_gaps(gaps: dict) -> list:
    """Use Cerebro to prioritize what to learn next"""
    if not gaps:
        return []

    all_gaps = []
    for domain, topics in gaps.items():
        for topic in topics:
            all_gaps.append({"topic": topic, "domain": domain})

    # Ask Cerebro to prioritize
    gaps_text = "\n".join([f"- {g['topic']} ({g['domain']})" for g in all_gaps[:20]])

    messages = [
        SystemMessage(content="""You are Cerebro's learning planner.
        Prioritize topics to learn based on importance and dependencies.
        Return ONLY a numbered list of topic names, most important first.
        Maximum 5 topics. No explanations."""),
        HumanMessage(content=f"""
Prioritize these knowledge gaps for a DevOps/Cloud Security learner:

{gaps_text}

Return top 5 as:
1. topic name
2. topic name
3. topic name
4. topic name
5. topic name
""")
    ]

    response = llm.invoke(messages)
    content = response.content

    prioritized = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            topic = line.split(".", 1)[-1].strip()
            # Find domain for this topic
            domain = "general"
            for d, topics in gaps.items():
                if any(topic.lower() in t.lower() or t.lower() in topic.lower() for t in topics):
                    domain = d
                    break
            prioritized.append({"topic": topic, "domain": domain})

    return prioritized[:5]

def save_gaps(gaps: list):
    """Save detected gaps for the learning loop"""
    os.makedirs(os.path.dirname(GAPS_FILE), exist_ok=True)
    with open(GAPS_FILE, "w") as f:
        json.dump(gaps, f, indent=2)

def load_gaps() -> list:
    """Load saved gaps"""
    if not os.path.exists(GAPS_FILE):
        return []
    with open(GAPS_FILE, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    print("=" * 55)
    print("  CEREBRO — Knowledge Gap Detector")
    print("=" * 55)

    init_memory()

    print("\n[CEREBRO GAP] Scanning knowledge graph...")
    gaps = detect_gaps()

    total_gaps = sum(len(v) for v in gaps.values())
    print(f"[CEREBRO GAP] Found {total_gaps} knowledge gaps\n")

    for domain, topics in gaps.items():
        print(f"[CEREBRO GAP] {domain.upper()}: missing {len(topics)} topics")
        for topic in topics[:3]:
            print(f"              - {topic}")
        if len(topics) > 3:
            print(f"              ... and {len(topics)-3} more")

    print("\n[CEREBRO GAP] Prioritizing what to learn next...")
    prioritized = prioritize_gaps(gaps)

    print("\n[CEREBRO GAP] Learning Queue:")
    for i, item in enumerate(prioritized, 1):
        print(f"  {i}. {item['topic']} ({item['domain']})")

    save_gaps(prioritized)
    print("\n[CEREBRO GAP] Queue saved. Ready for autonomous learning.")
