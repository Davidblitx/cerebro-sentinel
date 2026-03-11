import sys
import os
import json
import time
import datetime
import schedule
sys.path.append('/home/david/cerebro-sentinel/agents')
sys.path.append('/home/david/cerebro-sentinel/learning/ingestion')
sys.path.append('/home/david/cerebro-sentinel/learning/graph')
sys.path.append('/home/david/cerebro-sentinel/learning/autonomous')

from memory_engine import init_memory, remember
from gap_detector import detect_gaps, prioritize_gaps, save_gaps
from web_searcher import learn_from_search
from knowledge_graph import CerebroKnowledgeGraph

REPORT_FILE = "/home/david/cerebro-sentinel/vault/learning_report.json"
OLLAMA_URL = "http://localhost:11434"

def run_learning_cycle():
    """One full autonomous learning cycle"""
    print("\n" + "=" * 55)
    print(f"  CEREBRO — Autonomous Learning Cycle")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    init_memory()
    session_log = {
        "started_at": datetime.datetime.now().isoformat(),
        "topics_learned": [],
        "topics_failed": [],
        "new_concepts": 0,
        "new_connections": 0
    }

    # Step 1: Detect gaps
    print("\n[CEREBRO NIGHT] Step 1: Scanning for knowledge gaps...")
    gaps = detect_gaps()
    total_gaps = sum(len(v) for v in gaps.values())
    print(f"[CEREBRO NIGHT] Found {total_gaps} gaps across {len(gaps)} domains")

    # Step 2: Prioritize
    print("\n[CEREBRO NIGHT] Step 2: Prioritizing learning queue...")
    prioritized = prioritize_gaps(gaps)
    save_gaps(prioritized)

    if not prioritized:
        print("[CEREBRO NIGHT] No gaps found. Cerebro is fully caught up!")
        return

    print(f"[CEREBRO NIGHT] Tonight's learning plan:")
    for i, item in enumerate(prioritized, 1):
        print(f"  {i}. {item['topic']} ({item['domain']})")

    # Step 3: Learn each topic
    print("\n[CEREBRO NIGHT] Step 3: Learning...")

    # Get graph stats before
    graph = CerebroKnowledgeGraph()
    concepts_before = graph.graph.number_of_nodes()
    connections_before = graph.graph.number_of_edges()

    for item in prioritized[:2]:
        topic = item["topic"]
        print(f"\n[CEREBRO NIGHT] Learning: {topic}")

        try:
            success = learn_from_search(topic)

            if success:
                # Update knowledge graph
                graph.learn_topic(topic, item["domain"])
                graph.save_graph()
                session_log["topics_learned"].append(topic)
                remember(f"Autonomously learned about: {topic}", "autonomous_learning")
                print(f"[CEREBRO NIGHT] ✅ {topic} — learned and connected")
            else:
                session_log["topics_failed"].append(topic)
                print(f"[CEREBRO NIGHT] ⚠️  {topic} — no sources found")

        except Exception as e:
            session_log["topics_failed"].append(topic)
            print("[CEREBRO NIGHT] Cooling down...")

        # Small pause between topics
        time.sleep(90)

    # Step 4: Update stats
    concepts_after = graph.graph.number_of_nodes()
    connections_after = graph.graph.number_of_edges()

    session_log["new_concepts"] = concepts_after - concepts_before
    session_log["new_connections"] = connections_after - connections_before
    session_log["completed_at"] = datetime.datetime.now().isoformat()

    # Step 5: Save report
    reports = []
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "r") as f:
            reports = json.load(f)
    reports.append(session_log)
    with open(REPORT_FILE, "w") as f:
        json.dump(reports, f, indent=2)

    # Summary
    print("\n" + "=" * 55)
    print("  CEREBRO — Learning Cycle Complete")
    print("=" * 55)
    print(f"  ✅ Topics learned: {len(session_log['topics_learned'])}")
    print(f"  ❌ Topics failed: {len(session_log['topics_failed'])}")
    print(f"  🧠 New concepts: {session_log['new_concepts']}")
    print(f"  🔗 New connections: {session_log['new_connections']}")
    print("=" * 55)

def start_night_loop():
    """Start the scheduled autonomous learning"""
    print("=" * 55)
    print("  CEREBRO Sentinel v0.3 — Autonomous Mind")
    print("=" * 55)
    print("\n[CEREBRO NIGHT] Autonomous learning scheduler active")
    print("[CEREBRO NIGHT] Schedule: every night at 02:00 AM")
    print("[CEREBRO NIGHT] Running first cycle now...\n")

    # Run once immediately
    run_learning_cycle()

    # Then schedule nightly
    schedule.every().day.at("02:00").do(run_learning_cycle)

    print("\n[CEREBRO NIGHT] Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_night_loop()
