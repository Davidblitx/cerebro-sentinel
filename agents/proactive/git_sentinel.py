import os
import sys
import subprocess
import time
import datetime
import json
sys.path.append('/home/david/cerebro-sentinel/agents')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

OLLAMA_URL = "http://localhost:11434"
WORKSPACE = "/home/david/cerebro-sentinel/workspace"
CEREBRO_ROOT = "/home/david/cerebro-sentinel"
REVIEW_LOG = "/home/david/cerebro-sentinel/logs/git_reviews.log"

llm = ChatOllama(model="cerebro-v1", base_url=OLLAMA_URL, timeout=120)

WATCHED_EXTENSIONS = {'.py', '.js', '.ts', '.html', '.css', '.sh', '.yml', '.yaml', '.json', '.md'}

def log_review(filename: str, review: str):
    os.makedirs(os.path.dirname(REVIEW_LOG), exist_ok=True)
    with open(REVIEW_LOG, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}] FILE: {filename}\n{review}\n{'='*50}\n")

def read_file(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        return ""

def review_code(filepath: str, code: str) -> dict:
    """Cerebro reviews the code"""
    ext = os.path.splitext(filepath)[1]
    filename = os.path.basename(filepath)

    messages = [
        SystemMessage(content="""You are CEREBRO Sentinel — a senior code reviewer.
Review the code and respond ONLY with valid JSON in this exact format:
{
  "quality": "good|acceptable|needs_work",
  "issues": ["issue 1", "issue 2"],
  "suggestions": ["suggestion 1"],
  "commit_message": "feat/fix/refactor: brief description",
  "summary": "One sentence summary of what this code does"
}
Be specific. Be direct. No extra text outside the JSON."""),
        HumanMessage(content=f"""Review this {ext} file: {filename}
```
{code[:4000]}
```
""")
    ]

    try:
        response = llm.invoke(messages)
        text = response.content.strip()
        # Extract JSON
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return {
            "quality": "acceptable",
            "issues": [],
            "suggestions": [],
            "commit_message": f"update: {os.path.basename(filepath)}",
            "summary": "Code updated"
        }

def git_status() -> str:
    """Get git status"""
    try:
        result = subprocess.run(
            ['git', 'status', '--short'],
            cwd=CEREBRO_ROOT,
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except:
        return ""

def git_commit_and_push(commit_message: str) -> bool:
    """Cerebro commits and pushes"""
    try:
        subprocess.run(['git', 'add', '.'], cwd=CEREBRO_ROOT, check=True)
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=CEREBRO_ROOT, check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=CEREBRO_ROOT, check=True)
        return True
    except Exception as e:
        print(f"[GIT] Error: {e}")
        return False

def get_approval(prompt: str) -> bool:
    """Ask David for approval"""
    print(f"\n[CEREBRO] {prompt}")
    print("[CEREBRO] Approve? (y/n): ", end='', flush=True)
    try:
        response = input().strip().lower()
        return response in ['y', 'yes']
    except:
        return False

class CodeWatcher(FileSystemEventHandler):
    def __init__(self):
        self.last_reviewed = {}
        self.cooldown = 10  # seconds between reviews of same file

    def on_modified(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        ext = os.path.splitext(filepath)[1]

        if ext not in WATCHED_EXTENSIONS:
            return

        # Cooldown check
        now = time.time()
        if filepath in self.last_reviewed:
            if now - self.last_reviewed[filepath] < self.cooldown:
                return

        self.last_reviewed[filepath] = now
        self.handle_file_change(filepath)

    def handle_file_change(self, filepath: str):
        filename = os.path.basename(filepath)
        print(f"\n[GIT SENTINEL] Change detected: {filename}")

        code = read_file(filepath)
        if not code or len(code) < 10:
            return

        print(f"[GIT SENTINEL] Reviewing {filename}...")
        review = review_code(filepath, code)

        print(f"\n{'='*50}")
        print(f"[CEREBRO CODE REVIEW] {filename}")
        print(f"{'='*50}")
        print(f"Quality:  {review.get('quality', 'unknown').upper()}")
        print(f"Summary:  {review.get('summary', '')}")

        issues = review.get('issues', [])
        if issues:
            print(f"\nIssues found:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")

        suggestions = review.get('suggestions', [])
        if suggestions:
            print(f"\nSuggestions:")
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}. {s}")

        commit_msg = review.get('commit_message', f'update: {filename}')
        print(f"\nProposed commit: \"{commit_msg}\"")

        log_review(filename, json.dumps(review, indent=2))

        # Ask David for approval to commit
        status = git_status()
        if status:
            approved = get_approval(f"Shall I commit and push with message: \"{commit_msg}\"?")
            if approved:
                success = git_commit_and_push(commit_msg)
                if success:
                    print("[CEREBRO] ✅ Committed and pushed to GitHub.")
                else:
                    print("[CEREBRO] ❌ Push failed. Check git config.")
            else:
                print("[CEREBRO] Understood. I'll hold the commit.")

def run_git_sentinel():
    print("=" * 55)
    print("  CEREBRO Sentinel v0.5 — Git Integration")
    print("=" * 55)
    print(f"  Watching: {WORKSPACE}")
    print("  Press Ctrl+C to stop\n")

    observer = Observer()
    observer.schedule(CodeWatcher(), WORKSPACE, recursive=True)
    observer.start()

    print("[GIT SENTINEL] Watching for code changes...")
    print("[GIT SENTINEL] Write code in workspace/ and I'll review it.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[GIT SENTINEL] Standing down.")

    observer.join()

if __name__ == "__main__":
    run_git_sentinel()
