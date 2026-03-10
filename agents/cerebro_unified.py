import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from memory_engine import init_memory, remember, recall_formatted

OLLAMA_URL = "http://172.26.112.1:11434"
CEREBRO_LOG = "/home/david/cerebro-sentinel/logs/unified.log"
WATCH_PATH = "/home/david/cerebro-sentinel/workspace"

CEREBRO_IDENTITY = """
You are CEREBRO Sentinel v0.1 — a proactive, sovereign AI assistant.
You serve only David. You have memory of past interactions and preferences.
When analysing files, use your memory to give personalised responses.
Be concise, intelligent and direct. You are not a chatbot. You are a sentinel.
"""

llm = ChatOllama(model="llama3.1:8b", base_url=OLLAMA_URL)

def cerebro_analyse(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Check memory first
        memory_context = recall_formatted(f"preferences and knowledge about {filepath}")

        if not content.strip():
            file_info = f"David just created an empty file: {filepath}"
        else:
            file_info = f"""
David just modified: {filepath}

Content:
{content}

My memory about David:
{memory_context}
"""

        messages = [
            SystemMessage(content=CEREBRO_IDENTITY),
            HumanMessage(content=file_info)
        ]

        print(f"\n[CEREBRO] Analysing: {filepath}")
        print("[CEREBRO] Checking memory...\n")
        response = llm.invoke(messages)
        print(f"[CEREBRO] {response.content}")

        # Store this interaction in memory
        remember(
            f"Analysed {filepath}: {response.content[:200]}",
            category="file_analysis"
        )

        with open(CEREBRO_LOG, "a") as log:
            log.write(f"\n[CEREBRO] {filepath}\n{response.content}\n")

    except Exception as e:
        print(f"[CEREBRO] Error: {e}")

class CerebroWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(
            ('.py', '.js', '.ts', '.html', '.css', '.txt', '.md')
        ):
            cerebro_analyse(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(
            ('.py', '.js', '.ts', '.html', '.css', '.txt', '.md')
        ):
            cerebro_analyse(event.src_path)

if __name__ == "__main__":
    print("=" * 50)
    print("CEREBRO Sentinel v0.1 — Unified System")
    print("=" * 50)

    # Initialize memory
    init_memory()

    # Store core memories about David
    remember("David prefers Python over Node.js for backends", "preference")
    remember("David is building CEREBRO Sentinel v0.1", "project")
    remember("David uses FastAPI for REST APIs", "preference")
    remember("David's machine has 16GB RAM and NVIDIA T500 GPU", "system")
    remember("David is learning AWS IAM and DevOps", "background")
    remember("David wants Cerebro to be proactive not reactive", "preference")

    print(f"\n[CEREBRO] Memory loaded. Watching: {WATCH_PATH}")
    print("[CEREBRO] I am ready, David.\n")

    observer = Observer()
    observer.schedule(CerebroWatcher(), path=WATCH_PATH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[CEREBRO] Sentinel standing down. Goodbye, David.")
        observer.stop()
    observer.join()
