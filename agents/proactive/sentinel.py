import os
import sys
import json
import time
import datetime
import psutil
sys.path.append('/home/david/cerebro-sentinel/agents')
sys.path.append('/home/david/cerebro-sentinel/vault')

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://localhost:11434"
GAPS_FILE = "/home/david/cerebro-sentinel/vault/knowledge_gaps.json"
GRAPH_FILE = "/home/david/cerebro-sentinel/vault/knowledge_graph.json"
ALERTS_LOG = "/home/david/cerebro-sentinel/logs/alerts.log"
LAST_STUDY_FILE = "/home/david/cerebro-sentinel/vault/last_study.json"

llm = ChatOllama(model="cerebro-v1", base_url=OLLAMA_URL, timeout=120)

# Alert thresholds
CPU_THRESHOLD = 85
RAM_THRESHOLD = 80
DISK_THRESHOLD = 78
STUDY_GAP_HOURS = 24

def log_alert(alert_type: str, message: str):
    """Log alert to file"""
    os.makedirs(os.path.dirname(ALERTS_LOG), exist_ok=True)
    with open(ALERTS_LOG, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] [{alert_type}] {message}\n")

def check_system_health() -> list:
    """Check CPU, RAM, Disk"""
    alerts = []

    cpu = psutil.cpu_percent(interval=2)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    if cpu > CPU_THRESHOLD:
        alerts.append({
            "type": "SYSTEM",
            "severity": "HIGH",
            "message": f"CPU usage critical at {cpu:.1f}%",
            "value": cpu
        })

    if ram > RAM_THRESHOLD:
        alerts.append({
            "type": "SYSTEM",
            "severity": "HIGH",
            "message": f"RAM usage high at {ram:.1f}%",
            "value": ram
        })

    if disk > DISK_THRESHOLD:
        alerts.append({
            "type": "SYSTEM",
            "severity": "MEDIUM",
            "message": f"Disk usage at {disk:.1f}% — consider cleanup",
            "value": disk
        })

    return alerts

def check_knowledge_gaps() -> list:
    """Check if David has been neglecting topics"""
    alerts = []

    if not os.path.exists(GAPS_FILE):
        return alerts

    with open(GAPS_FILE, "r") as f:
        gaps = json.load(f)

    # Check last study session
    if os.path.exists(LAST_STUDY_FILE):
        with open(LAST_STUDY_FILE, "r") as f:
            last_study = json.load(f)
        last_time = datetime.datetime.fromisoformat(last_study.get("timestamp", "2000-01-01"))
        hours_since = (datetime.datetime.now() - last_time).total_seconds() / 3600

        if hours_since > STUDY_GAP_HOURS:
            top_gap = gaps[0]["topic"] if gaps else "unknown"
            alerts.append({
                "type": "LEARNING",
                "severity": "MEDIUM",
                "message": f"No study session in {hours_since:.0f} hours. Top gap: {top_gap}",
                "value": hours_since
            })

    # Flag critical gaps
    critical_topics = ["kubernetes", "terraform", "aws iam", "ci cd"]
    if gaps:
        top_topics = [g["topic"].lower() for g in gaps[:5]]
        for critical in critical_topics:
            if any(critical in t for t in top_topics):
                alerts.append({
                    "type": "LEARNING",
                    "severity": "LOW",
                    "message": f"Critical gap detected: {critical} still unlearned",
                    "value": critical
                })
                break

    return alerts

def check_knowledge_growth() -> list:
    """Check if knowledge graph is growing"""
    alerts = []

    if not os.path.exists(GRAPH_FILE):
        return alerts

    with open(GRAPH_FILE, "r") as f:
        graph = json.load(f)

    nodes = len(graph.get("nodes", []))
    edges = len(graph.get("edges", []))

    # Celebrate milestones
    milestones = [50, 100, 150, 200, 500]
    for milestone in milestones:
        if nodes >= milestone:
            milestone_file = f"/home/david/cerebro-sentinel/vault/milestone_{milestone}.flag"
            if not os.path.exists(milestone_file):
                open(milestone_file, 'w').close()
                alerts.append({
                    "type": "MILESTONE",
                    "severity": "POSITIVE",
                    "message": f"Knowledge milestone reached: {nodes} concepts, {edges} connections",
                    "value": nodes
                })

    return alerts

def generate_alert_message(alert: dict) -> str:
    """Use LLM to generate natural alert message"""
    messages = [
        SystemMessage(content="""You are CEREBRO Sentinel. 
Generate a single, direct, spoken alert for David.
Be concise — one or two sentences maximum.
Sound like a trusted advisor, not a robot.
For POSITIVE alerts, be proud and encouraging.
For HIGH severity, be urgent but calm.
For MEDIUM/LOW, be informative."""),
        HumanMessage(content=f"""
Alert type: {alert['type']}
Severity: {alert['severity']}
Message: {alert['message']}

Generate the spoken alert now.
""")
    ]
    response = llm.invoke(messages)
    return response.content

def run_sentinel_check():
    """Run one full sentinel check cycle"""
    print(f"\n[SENTINEL] Check at {datetime.datetime.now().strftime('%H:%M:%S')}")

    all_alerts = []
    all_alerts.extend(check_system_health())
    all_alerts.extend(check_knowledge_gaps())
    all_alerts.extend(check_knowledge_growth())

    if not all_alerts:
        print("[SENTINEL] All systems nominal. No alerts.")
        return

    for alert in all_alerts:
        print(f"\n[ALERT] {alert['severity']} — {alert['message']}")
        log_alert(alert['type'], alert['message'])

        # Generate intelligent message
        message = generate_alert_message(alert)
        print(f"[CEREBRO] {message}")

def run_continuous(interval_minutes: int = 5):
    """Run sentinel continuously"""
    print("=" * 55)
    print("  CEREBRO Sentinel v0.5 — Proactive Sentinel")
    print("=" * 55)
    print(f"  Monitoring every {interval_minutes} minutes")
    print("  Press Ctrl+C to stop\n")

    while True:
        try:
            run_sentinel_check()
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n[SENTINEL] Standing down.")
            break
        except Exception as e:
            print(f"[SENTINEL] Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run_continuous(interval_minutes=5)
