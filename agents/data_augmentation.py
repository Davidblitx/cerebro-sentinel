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
TRAINING_FILE = "/home/david/cerebro-sentinel/vault/training_data.jsonl"

llm = ChatOllama(model=MODEL, base_url=OLLAMA_URL, timeout=180)

AUGMENTATION_TOPICS = [
    # Cloud & AWS
    "AWS IAM policies and roles",
    "AWS S3 bucket security",
    "AWS EC2 instance security",
    "AWS VPC networking",
    "AWS CloudTrail logging",
    "AWS Config compliance",
    "AWS GuardDuty threat detection",
    "AWS Lambda serverless security",
    "AWS KMS encryption",
    "AWS Certificate Manager",
    # Security
    "Zero Trust security model",
    "OAuth2 authentication flow",
    "JWT token security",
    "SSL TLS encryption",
    "SQL injection prevention",
    "Cross site scripting XSS",
    "CSRF protection",
    "Security headers HTTP",
    "Password hashing bcrypt",
    "API security best practices",
    "Network firewall rules",
    "Intrusion detection systems",
    "Security information event management SIEM",
    "Incident response playbook",
    "Threat intelligence feeds",
    # DevOps
    "Docker container security",
    "Kubernetes RBAC",
    "Kubernetes network policies",
    "CI/CD pipeline security",
    "GitHub Actions security",
    "Infrastructure as code security",
    "Terraform state management",
    "Ansible automation",
    "Monitoring and alerting",
    "Log aggregation ELK stack",
    # Engineering
    "REST API design principles",
    "Microservices architecture",
    "Database indexing performance",
    "Caching strategies Redis",
    "Message queues RabbitMQ Kafka",
    "Load balancing strategies",
    "Database replication",
    "Horizontal vertical scaling",
    "Circuit breaker pattern",
    "API rate limiting",
    # Business & AI Automation
    "AI automation business models",
    "SaaS pricing strategies",
    "Nigerian tech market opportunities",
    "Cloud consulting services",
    "DevOps as a service",
    "Security as a service",
    "AI implementation for businesses",
    "Digital transformation Nigeria",
    "Tech startup funding Africa",
    "B2B sales technology services",
    # CEREBRO specific
    "sovereign AI benefits",
    "local LLM deployment advantages",
    "vector database memory systems",
    "autonomous AI learning systems",
    "AI fine tuning process",
    "prompt engineering techniques",
    "RAG retrieval augmented generation",
    "AI agent architectures",
    "LangChain framework",
    "Ollama local deployment"
]

QUESTION_TYPES = [
    "What is {topic}?",
    "How does {topic} work?",
    "Why is {topic} important?",
    "What are the best practices for {topic}?",
    "What are common mistakes with {topic}?",
    "How do you implement {topic}?",
    "What are the benefits of {topic}?",
    "How does {topic} improve security?",
    "What should David know about {topic}?",
    "How does {topic} relate to cloud architecture?"
]

def generate_qa_pair(topic: str, question_template: str) -> dict:
    """Generate a single high quality Q&A pair"""
    question = question_template.format(topic=topic)

    messages = [
        SystemMessage(content="""You are CEREBRO Sentinel — David's sovereign AI.
Answer this question as CEREBRO would — direct, wise, specific.
Give a complete answer in 3-5 sentences.
Be technical but clear. Reference real tools and concepts.
Do NOT say 'As an AI' or 'I cannot'. Just answer directly."""),
        HumanMessage(content=question)
    ]

    try:
        r = llm.invoke(messages)
        answer = r.content.strip()

        if len(answer) < 50:
            return None

        return {
            "instruction": question,
            "input": "",
            "output": answer
        }
    except:
        return None

def generate_multi_turn_samples(topic: str) -> list:
    """Generate a conversation sample about a topic"""
    messages = [
        SystemMessage(content="""You are creating training data for CEREBRO Sentinel.
Generate a short 2-turn conversation between David and CEREBRO about this topic.
David asks a real practical question. CEREBRO gives a wise, specific answer.
Respond ONLY in JSON:
{
  "turn_1": {
    "instruction": "David's question",
    "input": "",
    "output": "CEREBRO's answer (3-5 sentences, specific and practical)"
  },
  "turn_2": {
    "instruction": "David's follow up question",
    "input": "",
    "output": "CEREBRO's follow up answer (3-5 sentences)"
  }
}"""),
        HumanMessage(content=f"Topic: {topic}\nGenerate a 2-turn conversation.")
    ]

    try:
        r = llm.invoke(messages)
        text = r.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        samples = []
        for turn in ["turn_1", "turn_2"]:
            t = data.get(turn, {})
            if t.get("instruction") and t.get("output"):
                if len(t["output"]) > 50:
                    samples.append({
                        "instruction": t["instruction"],
                        "input": "",
                        "output": t["output"]
                    })
        return samples
    except:
        return []

def generate_david_context_samples() -> list:
    """Generate samples specific to David's context"""
    print("[AUGMENT] Generating David context samples...")

    david_scenarios = [
        ("How do I get my first cloud security client in Nigeria?",
         "Getting your first cloud security client in Nigeria requires "
         "targeting fintech companies, banks, and telecoms who face "
         "strict CBN compliance requirements. Build a portfolio by "
         "offering free security audits to 2-3 small businesses first. "
         "Document everything, get testimonials, then use those as "
         "proof when approaching larger enterprises. LinkedIn outreach "
         "to CTOs and IT managers works well in the Nigerian market."),

        ("What AWS certification should I get first?",
         "Start with AWS Cloud Practitioner — it gives you broad "
         "foundational knowledge and takes 1-2 months to prepare. "
         "After that, go straight to AWS Security Specialty since "
         "your background in security makes it a natural fit and it "
         "commands the highest salaries in the Nigerian and remote "
         "job market. Security-certified AWS engineers earn "
         "significantly more than generalists."),

        ("How do I run CEREBRO more efficiently on limited hardware?",
         "On limited hardware, reduce Ollama's context window with "
         "OLLAMA_NUM_CTX=2048, use quantized models like "
         "llama3.1:8b-instruct-q4_0 which use 40% less RAM, and "
         "run heavy tasks like the night loop during off-peak hours. "
         "Also consider running only one service at a time — "
         "stop the dashboard before running learning cycles to "
         "free up RAM for the model."),

        ("What is the fastest way to make money with cloud skills in Nigeria?",
         "The fastest path is cloud cost optimization consulting — "
         "Nigerian companies waste enormous amounts on poorly "
         "configured AWS and Azure resources. You find the waste, "
         "fix it, and charge 20-30% of the first month's savings. "
         "No upfront cost to the client, immediate ROI for them, "
         "immediate income for you. Combine this with security "
         "audits and you have a compelling offer that sells itself."),

        ("How should I think about building CEREBRO as a platform?",
         "Think of CEREBRO as three layers: the personal layer "
         "which is your specific data and context, the platform "
         "layer which is the architecture that anyone can deploy, "
         "and the intelligence layer which improves for everyone "
         "as more people use it. Monetize the platform layer first "
         "through licensing and hosting fees. The personal layer "
         "stays private forever. The intelligence layer becomes "
         "your moat — the more CEREBRO learns, the harder it is "
         "to replicate."),

        ("What makes a sovereign AI different from cloud AI?",
         "Sovereign AI runs on infrastructure you own and control "
         "completely. Your data never leaves your servers, nobody "
         "can read your conversations, nobody can cut off your "
         "access, and you are not dependent on any company's "
         "pricing or policy decisions. Cloud AI like ChatGPT "
         "means your most sensitive business intelligence is "
         "sitting on someone else's servers. For hospitals, "
         "governments, banks, and anyone with sensitive data, "
         "sovereign AI is not optional — it is the only option."),

        ("How do I explain CEREBRO to a potential investor?",
         "Tell them CEREBRO is the AWS of sovereign AI — "
         "the infrastructure layer that every organization needs "
         "but nobody has built properly yet. OpenAI sells "
         "intelligence as a service. CEREBRO sells sovereignty. "
         "The market is every organization that cannot put their "
         "data in OpenAI — hospitals, governments, law firms, "
         "banks, defense contractors. That is not a niche. "
         "That is the majority of enterprise value in the world."),

        ("What should I learn after AWS Cloud Practitioner?",
         "After Cloud Practitioner, go to AWS Security Specialty "
         "directly — skip Solutions Architect for now. Security "
         "Specialty pays more, has less competition, and aligns "
         "perfectly with CEREBRO's architecture. Study IAM deeply, "
         "KMS encryption, CloudTrail, GuardDuty, and Security Hub. "
         "These are exactly the services enterprises need help with "
         "and will pay significant consulting fees for."),
    ]

    samples = []
    for question, answer in david_scenarios:
        samples.append({
            "instruction": question,
            "input": "",
            "output": answer
        })

    print(f"[AUGMENT] Generated {len(samples)} David context samples")
    return samples

def run_augmentation():
    """Full data augmentation pipeline"""
    print("\n" + "=" * 55)
    print("  CEREBRO v1.0 — Data Augmentation")
    print("=" * 55)

    init_memory()
    all_new_samples = []

    # 1. David context samples
    david_samples = generate_david_context_samples()
    all_new_samples.extend(david_samples)

    # 2. Topic Q&A pairs
    print("[AUGMENT] Generating topic Q&A pairs...")
    import random
    qa_count = 0

    for i, topic in enumerate(AUGMENTATION_TOPICS):
        if i % 10 == 0:
            print(f"[AUGMENT] Topic {i+1}/{len(AUGMENTATION_TOPICS)}: "
                  f"{topic}")

        # Pick 2 random question types per topic
        templates = random.sample(QUESTION_TYPES, 2)
        for template in templates:
            qa = generate_qa_pair(topic, template)
            if qa:
                all_new_samples.append(qa)
                qa_count += 1

    print(f"[AUGMENT] Q&A pairs generated: {qa_count}")

    # 3. Multi turn conversations
    print("[AUGMENT] Generating multi-turn conversations...")
    conv_topics = AUGMENTATION_TOPICS[:20]
    conv_count = 0

    for topic in conv_topics:
        samples = generate_multi_turn_samples(topic)
        all_new_samples.extend(samples)
        conv_count += len(samples)

    print(f"[AUGMENT] Conversation samples: {conv_count}")

    # Filter quality
    quality = [s for s in all_new_samples
               if len(s.get("instruction", "")) > 10
               and len(s.get("output", "")) > 50]

    print(f"\n[AUGMENT] New samples generated: {len(quality)}")

    # Append to existing training data
    with open(TRAINING_FILE, "a") as f:
        for s in quality:
            f.write(json.dumps(s) + "\n")

    # Count total
    with open(TRAINING_FILE) as f:
        total = sum(1 for line in f)

    print(f"[AUGMENT] Total training samples now: {total}")
    print(f"[AUGMENT] Ready for fine tuning: "
          f"{'✅ YES' if total >= 500 else f'⚠️ Need {500-total} more'}")
    print("=" * 55)

    return total

if __name__ == "__main__":
    run_augmentation()

