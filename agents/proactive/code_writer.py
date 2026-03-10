import sys
import os
import json
import datetime
sys.path.append('/home/david/cerebro-sentinel/agents')
sys.path.append('/home/david/cerebro-sentinel/vault')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://172.26.112.1:11434"
WORKSPACE  = "/home/david/cerebro-sentinel/workspace"
WRITE_LOG  = "/home/david/cerebro-sentinel/logs/code_written.log"

llm = ChatOllama(model="llama3.1:8b", base_url=OLLAMA_URL, timeout=180)

def log_write(filename: str, description: str):
    os.makedirs(os.path.dirname(WRITE_LOG), exist_ok=True)
    with open(WRITE_LOG, "a") as f:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {filename} — {description}\n")

def think_and_plan(request: str) -> dict:
    """Cerebro thinks about what to build before writing"""
    messages = [
        SystemMessage(content="""You are CEREBRO Sentinel — a senior software engineer.
Before writing code you THINK and PLAN.
Respond ONLY with valid JSON:
{
  "understood": "what David is asking for in one sentence",
  "approach": "how you will solve it in one sentence", 
  "filename": "snake_case_filename.py",
  "language": "python",
  "complexity": "simple|moderate|complex",
  "dependencies": ["list", "of", "imports"]
}
No extra text. Just JSON."""),
        HumanMessage(content=f"David's request: {request}")
    ]
    try:
        response = llm.invoke(messages)
        text = response.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except:
        return {
            "understood": request,
            "approach": "Direct implementation",
            "filename": "cerebro_solution.py",
            "language": "python",
            "complexity": "moderate",
            "dependencies": []
        }

def write_code(request: str, plan: dict) -> str:
    """Cerebro writes the actual code"""
    messages = [
        SystemMessage(content="""You are CEREBRO Sentinel — a senior software engineer.
Write clean, production-quality code.
Include:
- Docstrings for all functions
- Error handling
- Comments for complex logic
- A main() function if appropriate
- Example usage in __main__ block

Return ONLY the code. No explanation. No markdown. Pure code."""),
        HumanMessage(content=f"""
Write {plan['language']} code for this request:
{request}

Plan:
- Approach: {plan['approach']}
- Dependencies available: {', '.join(plan['dependencies'])}

Write the complete, working code now.
""")
    ]
    response = llm.invoke(messages)
    code = response.content.strip()
    # Clean markdown if present
    if "```" in code:
        parts = code.split("```")
        for part in parts:
            if len(part) > 100:
                if part.startswith("python"):
                    part = part[6:]
                code = part.strip()
                break
    return code

def review_own_code(code: str, request: str) -> dict:
    """Cerebro reviews his own code before showing David"""
    messages = [
        SystemMessage(content="""You are CEREBRO reviewing your own code.
Be honest and critical.
Respond ONLY with JSON:
{
  "quality": "good|acceptable|needs_revision",
  "confidence": 85,
  "issues": ["any issues found"],
  "ready_for_david": true
}"""),
        HumanMessage(content=f"""
Original request: {request}

Code written:
{code[:3000]}

Is this code correct and complete?""")
    ]
    try:
        response = llm.invoke(messages)
        text = response.content.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except:
        return {"quality": "acceptable", "confidence": 75,
                "issues": [], "ready_for_david": True}

def save_to_workspace(filename: str, code: str) -> str:
    """Save code to workspace with approval"""
    filepath = os.path.join(WORKSPACE, filename)
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(code)
    return filepath

def run_code_writer():
    """Main interactive code writing loop"""
    print("=" * 55)
    print("  CEREBRO Sentinel v0.5 — Code Writer")
    print("=" * 55)
    print("  Describe what you need. CEREBRO will build it.")
    print("  Type 'exit' to stop.\n")

    while True:
        try:
            print("\n" + "─" * 55)
            request = input("David: ").strip()

            if not request:
                continue
            if request.lower() in ['exit', 'quit', 'stop']:
                print("[CEREBRO] Standing down.")
                break

            print("\n[CEREBRO] Thinking about your request...")
            plan = think_and_plan(request)

            print(f"\n[CEREBRO] Understood: {plan['understood']}")
            print(f"[CEREBRO] Approach:   {plan['approach']}")
            print(f"[CEREBRO] File:       {plan['filename']}")
            print(f"[CEREBRO] Complexity: {plan['complexity']}")

            confirm = input("\n[CEREBRO] Shall I proceed with this plan? (y/n): ").strip().lower()
            if confirm != 'y':
                print("[CEREBRO] Understood. Tell me more about what you need.")
                continue

            print("\n[CEREBRO] Engineering the solution...")
            code = write_code(request, plan)

            print("\n[CEREBRO] Reviewing my own work...")
            review = review_own_code(code, request)

            print(f"\n[CEREBRO] Self-review: {review['quality'].upper()} "
                  f"(confidence: {review.get('confidence', '?')}%)")

            if review.get('issues'):
                print("[CEREBRO] Issues I found in my own code:")
                for issue in review['issues']:
                    print(f"  - {issue}")

            print(f"\n{'='*55}")
            print(f"[CEREBRO] CODE WRITTEN — {plan['filename']}")
            print(f"{'='*55}")
            print(code)
            print(f"{'='*55}\n")

            save_confirm = input(
                f"[CEREBRO] Save to workspace/{plan['filename']}? (y/n): "
            ).strip().lower()

            if save_confirm == 'y':
                filepath = save_to_workspace(plan['filename'], code)
                log_write(plan['filename'], plan['understood'])
                print(f"[CEREBRO] File created: {filepath}")
                print(f"[CEREBRO] ✅ Saved to {filepath}")
                print(f"[CEREBRO] Ready for your review, David.")
            else:
                print("[CEREBRO] Code not saved. Tell me what to change.")

        except KeyboardInterrupt:
            print("\n[CEREBRO] Standing down.")
            break
        except Exception as e:
            print(f"[CEREBRO] Error: {e}")

if __name__ == "__main__":
    run_code_writer()
