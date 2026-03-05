import json
import os

AUDIT_LOG = "/home/david/cerebro-sentinel/logs/audit.log"

def view_audit_log():
    if not os.path.exists(AUDIT_LOG):
        print("[CEREBRO AUDIT] No audit log found yet.")
        return

    print("=" * 60)
    print("  CEREBRO Sentinel — Audit Log")
    print("=" * 60)

    with open(AUDIT_LOG, "r") as f:
        lines = f.readlines()

    if not lines:
        print("No entries yet.")
        return

    for line in lines:
        try:
            entry = json.loads(line)
            status = "✅" if entry["approved"] else "🚫"
            print(f"\n{status} {entry['timestamp']}")
            print(f"   Action:  {entry['action']}")
            print(f"   Details: {entry['details']}")
            print(f"   Status:  {entry['status'].upper()}")
        except:
            continue

    print("\n" + "=" * 60)
    print(f"Total entries: {len(lines)}")

if __name__ == "__main__":
    view_audit_log()
