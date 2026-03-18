import os
import sys
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from memory_engine import init_memory, remember, recall_formatted

OLLAMA_URL = "http://localhost:11434"
WORKSPACE = "/home/david/cerebro-sentinel/workspace"
CEREBRO_LOG = "/home/david/cerebro-sentinel/logs/commands.log"

CEREBRO_IDENTITY = """
You are CEREBRO Sentinel v0.1. You serve only David.
You have memory and you execute tasks.
When David gives you a command, you:
1. Check your memory for relevant context
2. Execute the task or explain exactly what you will do
3. Remember the interaction

You can:
- Create files and write code
- Analyse existing code
- Answer questions using memory
- Suggest improvements proactively

Be concise and direct. You are a sentinel, not a chatbot.
Always address David by name.
"""

llm = ChatOllama(model="cerebro-v1", base_url=OLLAMA_URL)

def execute_command(command: str):
    """Parse and execute file creation commands"""
    command_lower = command.lower()

    # Create file command
    if "create" in command_lower and any(
        ext in command_lower for ext in [".py", ".js", ".html", ".css", ".txt", ".md"]
    ):
        words = command.split()
        filename = None
        for word in words:
            if any(ext in word for ext in [".py", ".js", ".html", ".css", ".txt", ".md"]):
                filename = word.strip("'\".,")
                break

        if filename:
            filepath = os.path.join(WORKSPACE, filename)
            
            # Ask Cerebro what to put in the file
            messages = [
                SystemMessage(content=CEREBRO_IDENTITY),
                HumanMessage(content=f"""
David wants to create: {filename}
Memory context: {recall_formatted(filename)}

Generate appropriate starter code for this file.
Return ONLY the code, no explanation.
""")
            ]
            response = llm.invoke(messages)
            
            with open(filepath, "w") as f:
                f.write(response.content)
            
            print(f"\n[CEREBRO] Created {filename} in workspace ✅")
            print(f"[CEREBRO] I've written starter code based on the filename.")
            remember(f"Created file {filename} for David", "action")
            return

    # General conversation/question
    memory_context = recall_formatted(command)
    messages = [
        SystemMessage(content=CEREBRO_IDENTITY),
        HumanMessage(content=f"""
David says: {command}

Relevant memory:
{memory_context}
""")
    ]
    response = llm.invoke(messages)
    print(f"\n[CEREBRO] {response.content}")
    remember(f"David asked: {command}. I responded: {response.content[:150]}", "conversation")

def log_command(command: str):
    with open(CEREBRO_LOG, "a") as log:
        log.write(f"\n[COMMAND] {command}\n")

if __name__ == "__main__":
    print("=" * 50)
    print("  CEREBRO Sentinel v0.1 — Command Interface")
    print("=" * 50)
    
    init_memory()
    remember("David prefers Python over Node.js", "preference")
    remember("David uses FastAPI for REST APIs", "preference")
    remember("David is building CEREBRO Sentinel", "project")
    remember("David is learning AWS IAM and DevOps", "background")

    print("\n[CEREBRO] I am ready, David.")
    print("[CEREBRO] Type your command or question.")
    print("[CEREBRO] Type 'exit' to shut down.\n")

    while True:
        try:
            user_input = input("David: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n[CEREBRO] Standing down. Goodbye, David.")
                break

            log_command(user_input)
            execute_command(user_input)
            print()

        except KeyboardInterrupt:
            print("\n[CEREBRO] Standing down. Goodbye, David.")
            break
