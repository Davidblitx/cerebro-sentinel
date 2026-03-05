import json
import datetime
import os

AUDIT_LOG = "/home/david/cerebro-sentinel/logs/audit.log"
PERMISSIONS_FILE = "/home/david/cerebro-sentinel/vault/permissions.json"

# Define what Cerebro CAN and CANNOT do
PERMISSIONS = {
    "allowed_paths": [
        "/home/david/cerebro-sentinel/workspace",
        "/home/david/cerebro-sentinel/logs",
    ],
    "denied_paths": [
        "/home/david/.ssh",
        "/home/david/.aws",
        "/etc",
        "/root",
        "/sys",
    ],
    "allowed_actions": [
        "read_file",
        "write_file",
        "create_file",
        "analyse_file",
        "system_monitor",
    ],
    "denied_actions": [
        "delete_file",
        "execute_script",
        "network_request",
        "install_package",
    ],
    "require_approval": [
        "write_file",
        "create_file",
    ]
}

def save_permissions():
    """Save permissions to vault"""
    os.makedirs("/home/david/cerebro-sentinel/vault", exist_ok=True)
    with open(PERMISSIONS_FILE, "w") as f:
        json.dump(PERMISSIONS, f, indent=2)
    print("[CEREBRO VAULT] Permissions saved ✅")

def load_permissions():
    """Load permissions from vault"""
    if os.path.exists(PERMISSIONS_FILE):
        with open(PERMISSIONS_FILE, "r") as f:
            return json.load(f)
    return PERMISSIONS

def is_path_allowed(filepath: str) -> tuple[bool, str]:
    """Check if Cerebro is allowed to access a path"""
    perms = load_permissions()
    
    # Check denied paths first
    for denied in perms["denied_paths"]:
        if filepath.startswith(denied):
            return False, f"Path {filepath} is in denied zone"
    
    # Check allowed paths
    for allowed in perms["allowed_paths"]:
        if filepath.startswith(allowed):
            return True, "Path allowed"
    
    return False, f"Path {filepath} is outside Cerebro's boundaries"

def is_action_allowed(action: str) -> tuple[bool, str]:
    """Check if Cerebro is allowed to perform an action"""
    perms = load_permissions()
    
    if action in perms["denied_actions"]:
        return False, f"Action '{action}' is not permitted"
    
    if action in perms["allowed_actions"]:
        return True, "Action allowed"
    
    return False, f"Action '{action}' is not in permitted list"

def requires_approval(action: str) -> bool:
    """Check if action needs human approval"""
    perms = load_permissions()
    return action in perms["require_approval"]

def request_approval(action: str, details: str) -> bool:
    """Ask David for approval before executing"""
    print(f"\n[CEREBRO VAULT] ⚠️  Approval Required")
    print(f"[CEREBRO VAULT] Action: {action}")
    print(f"[CEREBRO VAULT] Details: {details}")
    response = input("[CEREBRO VAULT] Do you approve? (y/n): ").strip().lower()
    approved = response == "y"
    audit_log(action, details, approved)
    return approved

def audit_log(action: str, details: str, approved: bool = True):
    """Log every action Cerebro takes"""
    os.makedirs("/home/david/cerebro-sentinel/logs", exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "action": action,
        "details": details,
        "approved": approved,
        "status": "executed" if approved else "blocked"
    }
    with open(AUDIT_LOG, "a") as log:
        log.write(json.dumps(entry) + "\n")
    
    status = "✅ APPROVED" if approved else "🚫 BLOCKED"
    print(f"[CEREBRO AUDIT] {status} — {action}: {details[:50]}")

if __name__ == "__main__":
    save_permissions()
    
    print("\n[CEREBRO VAULT] Testing permission system...\n")
    
    # Test allowed path
    allowed, msg = is_path_allowed("/home/david/cerebro-sentinel/workspace/test.py")
    print(f"Workspace access: {'✅' if allowed else '🚫'} — {msg}")
    
    # Test denied path
    allowed, msg = is_path_allowed("/home/david/.ssh/id_rsa")
    print(f"SSH key access: {'✅' if allowed else '🚫'} — {msg}")
    
    # Test allowed action
    allowed, msg = is_action_allowed("read_file")
    print(f"Read file: {'✅' if allowed else '🚫'} — {msg}")
    
    # Test denied action
    allowed, msg = is_action_allowed("delete_file")
    print(f"Delete file: {'✅' if allowed else '🚫'} — {msg}")
    
    print("\n[CEREBRO VAULT] Permission system active ✅")
