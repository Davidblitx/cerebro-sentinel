import psutil
import time
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://localhost:11434"
CEREBRO_LOG = "/home/david/cerebro-sentinel/logs/system.log"

CEREBRO_IDENTITY = """
You are CEREBRO Sentinel v0.1. You monitor David's system health.
When you detect something concerning, you alert David clearly and suggest
a specific action to fix it. Be concise and direct. No fluff.
"""

llm = ChatOllama(model="llama3.1:8b", base_url=OLLAMA_URL)

def get_system_stats():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu_percent": cpu,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / (1024**3), 2),
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2)
    }

def cerebro_evaluate(stats):
    concerns = []
    
    if stats["cpu_percent"] > 85:
        concerns.append(f"CPU is at {stats['cpu_percent']}% — critically high")
    if stats["ram_percent"] > 80:
        concerns.append(f"RAM is at {stats['ram_percent']}% ({stats['ram_used_gb']}GB of {stats['ram_total_gb']}GB used)")
    if stats["disk_percent"] > 85:
        concerns.append(f"Disk is at {stats['disk_percent']}% — only {stats['disk_free_gb']}GB free")

    return concerns

def alert_cerebro(concerns, stats):
    concern_text = "\n".join(concerns)
    prompt = f"""
System stats for David's machine:
- CPU: {stats['cpu_percent']}%
- RAM: {stats['ram_percent']}% ({stats['ram_used_gb']}GB / {stats['ram_total_gb']}GB)
- Disk: {stats['disk_percent']}% used ({stats['disk_free_gb']}GB free)

Concerns detected:
{concern_text}

What should David do right now?
"""
    messages = [
        SystemMessage(content=CEREBRO_IDENTITY),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    print(f"\n[CEREBRO ALERT] {response.content}")
    
    with open(CEREBRO_LOG, "a") as log:
        log.write(f"\n[ALERT]\n{response.content}\n")

def run_monitor():
    print("CEREBRO Sentinel v0.1 — System Monitor Active")
    print("Monitoring CPU, RAM and Disk every 30 seconds\n")
    
    while True:
        stats = get_system_stats()
        print(f"[CEREBRO] CPU: {stats['cpu_percent']}% | RAM: {stats['ram_percent']}% | Disk: {stats['disk_percent']}%")
        
        concerns = cerebro_evaluate(stats)
        
        if concerns:
            print(f"[CEREBRO] ⚠️ Concerns detected — analysing...")
            alert_cerebro(concerns, stats)
        else:
            print(f"[CEREBRO] ✅ All systems healthy")
            
        time.sleep(30)

if __name__ == "__main__":
    run_monitor()
