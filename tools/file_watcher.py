import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

CEREBRO_LOG = "/home/david/cerebro-sentinel/logs/activity.log"
WATCH_PATH = "/home/david/cerebro-sentinel/workspace"
OLLAMA_URL = "http://localhost:11434"

CEREBRO_IDENTITY = """
You are CEREBRO Sentinel v0.1, a proactive sovereign AI assistant.
You monitor David's workspace and provide intelligent analysis.
When you see a file, you analyse it and proactively suggest improvements,
spot issues, or offer to help — without being asked.
Be concise, smart and direct. You are not a chatbot. You are a sentinel.
"""

llm = ChatOllama(model="llama3.1:8b", base_url=OLLAMA_URL)

def cerebro_analyse(filepath):
    try:
        with open(filepath, "r") as f:
            content = f.read()

        if not content.strip():
            file_info = f"David just created an empty file: {filepath}"
        else:
            file_info = f"David just modified this file: {filepath}\n\nContent:\n{content}"

        messages = [
            SystemMessage(content=CEREBRO_IDENTITY),
            HumanMessage(content=file_info)
        ]

        print(f"\n[CEREBRO] Analysing: {filepath}")
        print("[CEREBRO] Thinking...\n")
        response = llm.invoke(messages)
        print(f"[CEREBRO] {response.content}")

        with open(CEREBRO_LOG, "a") as log:
            log.write(f"\n[CEREBRO] {filepath}\n{response.content}\n")

    except Exception as e:
        print(f"[CEREBRO] Could not analyse file: {e}")

class CerebroWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.py', '.js', '.ts', '.html', '.css', '.txt', '.md')):
            cerebro_analyse(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.py', '.js', '.ts', '.html', '.css', '.txt', '.md')):
            cerebro_analyse(event.src_path)

if __name__ == "__main__":
    print("CEREBRO Sentinel v0.1 — Proactive Watcher Active")
    print(f"Watching: {WATCH_PATH}\n")
    observer = Observer()
    observer.schedule(CerebroWatcher(), path=WATCH_PATH, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
