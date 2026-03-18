import os
import sys
sys.path.append('/home/david/cerebro-sentinel/vault')
sys.path.append('/home/david/cerebro-sentinel/agents')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from memory_engine import init_memory, remember, recall_formatted
from permissions import (
    is_path_allowed, is_action_allowed,
    requires_approval, request_approval, audit_log
)

OLLAMA_URL = "http://localhost:11434"
WORKSPACE = "/home/david/cerebro-sentinel/workspace"

CEREBRO_IDENTITY = """
You are CEREBRO Sentinel v0.1. You serve only David.
You are secure, proactive and intelligent.
You have memory, permissions and an audit trail.
Be concise and direct. You are a sentinel, not a chatbot.
"""

llm = ChatOllama(model="cerebro-v1", base_url=OLLAMA_URL)

def secured_create_file(filename: str):
    """Create a file with full security checks"""
    filepath = os.path.join(WORKSPACE, filename)

    # Step 1: Check path permission
    allowed, msg = is_path_allowed(filepath)
    if not allowed:
        print(f"\n[CEREBRO VAULT] 🚫 BLOCKED — {msg}")
        audit_log("create_file", filepath, approved=False)
        return

    # Step 2: Check action permission
    allowed, msg = is_action_allowed("create_file")
    if not allowed:
        print(f"\n[CEREBRO VAULT] 🚫 BLOCKED — {msg}")
        audit_log("create_file", filepath, approved=False)
        return

    # Step 3: Request approval
    if requires_approval("create_file"):
        approved = request_approval("create_file", f"Create {filename} in workspace")
        if not approved:
            print("[CEREBRO] Understood. File creation cancelled.")
            return

    # Step 4: Generate and write file
    messages = [
        SystemMessage(content=CEREBRO_IDENTITY),
        HumanMessage(content=f"""
Generate starter code for: {filename}
David's preferences: {recall_formatted(filename)}
Return ONLY the code, no explanation.
""")
    ]
    response = llm.invoke(messages)

    with open(filepath, "w") as f:
        f.write(response.content)

    audit_log("create_file", filepath, approved=True)
    remember(f"Created {filename} for David", "action")
    print(f"\n[CEREBRO] ✅ Created {filename} successfully.")

def secured_answer(question: str):
    """Answer questions using memory"""
    memory_context = recall_formatted(question)
    messages = [
        SystemMessage(content=CEREBRO_IDENTITY),
        HumanMessage(content=f"""
David asks: {question}
Memory: {memory_context}
""")
    ]
    response = llm.invoke(messages)
    audit_log("answer_question", question[:50], approved=True)
    remember(f"David asked: {question[:100]}", "conversation")
    print(f"\n[CEREBRO] {response.content}")

def run():
    print("=" * 55)
    print("  CEREBRO Sentinel v0.1 — Secured Interface")
    print("=" * 55)

    init_memory()
    remember("David prefers Python over Node.js", "preference")
    remember("David uses FastAPI for REST APIs", "preference")
    remember("David is building CEREBRO Sentinel", "project")
    remember("David is learning AWS IAM and DevOps", "background")
    remember("David wants Cerebro proactive not reactive", "preference")

    print("\n[CEREBRO] Vault active. Permissions loaded.")
    print("[CEREBRO] I am ready, David.\n")

    while True:
        try:
            user_input = input("David: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n[CEREBRO] Standing down. Goodbye, David.")
                break

            user_lower = user_input.lower()

            if "create" in user_lower and any(
                ext in user_lower for ext in
                [".py", ".js", ".html", ".css", ".txt", ".md"]
            ):
                words = user_input.split()
                filename = None
                for word in words:
                    if any(ext in word for ext in
                           [".py", ".js", ".html", ".css", ".txt", ".md"]):
                        filename = word.strip("'\".,")
                        break
                if filename:
                    secured_create_file(filename)
            else:
                secured_answer(user_input)

            print()

        except KeyboardInterrupt:
            print("\n[CEREBRO] Standing down. Goodbye, David.")
            break

if __name__ == "__main__":
    run()
