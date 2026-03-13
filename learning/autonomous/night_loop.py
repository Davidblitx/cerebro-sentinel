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

def get_goal_directed_topics() -> list:
    """Read self model goals and return prioritized learning topics"""
    self_model_file = "/home/david/cerebro-sentinel/vault/self_model.json"
    improvement_file = "/home/david/cerebro-sentinel/vault/improvement_plan.json"

    goal_topics = []

    # Load self model goals
    if os.path.exists(self_model_file):
        with open(self_model_file, "r") as f:
            self_model = json.load(f)
        goals = self_model.get("goals", [])
        for goal in goals:
            topic = goal.get("target", "")
            priority = goal.get("priority", "medium")
            domain = goal.get("domain", "general")
            if topic:
                goal_topics.append({
                    "topic": topic,
                    "domain": domain,
                    "priority": priority,
                    "source": "self_model_goal",
                    "purpose": goal.get("purpose", "")
                })

    # Load improvement plan priorities
    if os.path.exists(improvement_file):
        with open(improvement_file, "r") as f:
            improvement = json.load(f)
        plan = improvement.get("plan", {})
        for key in ["priority_1", "priority_2", "priority_3"]:
            item = plan.get(key, {})
            topic = item.get("topic", "")
            if topic:
                goal_topics.append({
                    "topic": topic,
                    "domain": "improvement",
                    "priority": "high",
                    "source": "improvement_plan",
                    "purpose": item.get("reason", "")
                })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    goal_topics.sort(key=lambda x: priority_order.get(
        x.get("priority", "medium").lower(), 2))

    return goal_topics[:3]

def run_goal_directed_cycle():
    """Learning cycle driven by CEREBRO's self model goals"""
    print("\n" + "=" * 55)
    print(f"  CEREBRO — Goal Directed Learning Cycle")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    init_memory()

    # Get goal directed topics
    print("\n[CEREBRO NIGHT] Reading self model goals...")
    goal_topics = get_goal_directed_topics()

    if goal_topics:
        print(f"[CEREBRO NIGHT] Goal directed topics:")
        for i, t in enumerate(goal_topics, 1):
            print(f"  {i}. {t['topic']} [{t['priority'].upper()}]")
            if t.get('purpose'):
                print(f"     Purpose: {t['purpose'][:80]}...")
    else:
        print("[CEREBRO NIGHT] No goals found — falling back to gap detection")
        run_learning_cycle()
        return

    session_log = {
        "started_at": datetime.datetime.now().isoformat(),
        "mode": "goal_directed",
        "topics_learned": [],
        "topics_failed": [],
        "new_concepts": 0,
        "new_connections": 0
    }

    graph = CerebroKnowledgeGraph()
    concepts_before = graph.graph.number_of_nodes()

    # Learn top 2 goal topics
    for item in goal_topics[:2]:
        topic = item["topic"]
        print(f"\n[CEREBRO NIGHT] Learning: {topic}")
        print(f"[CEREBRO NIGHT] Purpose: {item.get('purpose', 'N/A')[:80]}")

        try:
            result = learn_from_search(topic)
            if result:
                session_log["topics_learned"].append(topic)
                print(f"[CEREBRO NIGHT] ✅ {topic} — learned successfully")
            else:
                session_log["topics_failed"].append(topic)
                print(f"[CEREBRO NIGHT] ❌ {topic} — failed")
        except Exception as e:
            session_log["topics_failed"].append(topic)
            print(f"[CEREBRO NIGHT] ❌ {topic} — error: {str(e)[:50]}")

        print("[CEREBRO NIGHT] Cooling down...")
        time.sleep(90)

    # Calculate what was learned
    graph2 = CerebroKnowledgeGraph()
    concepts_after = graph2.graph.number_of_nodes()
    session_log["new_concepts"] = concepts_after - concepts_before
    session_log["new_connections"] = (
        graph2.graph.number_of_edges() -
        graph.graph.number_of_edges())
    session_log["completed_at"] = datetime.datetime.now().isoformat()

    # Save report
    with open(REPORT_FILE, "w") as f:
        json.dump(session_log, f, indent=2)

    # Update self model after learning
    try:
        sys.path.append('/home/david/cerebro-sentinel/agents')
        from self_model import run_self_model
        run_self_model(verbose=False)
        print("\n[CEREBRO NIGHT] Self model updated. ✅")
    except Exception as e:
        print(f"\n[CEREBRO NIGHT] Self model update skipped: {e}")

    print(f"\n[CEREBRO NIGHT] Goal directed cycle complete.")
    print(f"[CEREBRO NIGHT] Learned: {len(session_log['topics_learned'])} topics")
    print(f"[CEREBRO NIGHT] New concepts: {session_log['new_concepts']}")
    print("=" * 55)
