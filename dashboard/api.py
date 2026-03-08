import sys
import os
import json
import datetime
import psutil

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

sys.path.append('/home/david/cerebro-sentinel/agents')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(title="CEREBRO Sentinel Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

VAULT = "/home/david/cerebro-sentinel/vault"
LOGS  = "/home/david/cerebro-sentinel/logs"

def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

def read_log_tail(path, lines=20):
    try:
        with open(path) as f:
            all_lines = f.readlines()
            return [l.strip() for l in all_lines[-lines:] if l.strip()]
    except:
        return []

@app.get("/api/stats")
def get_stats():
    graph = read_json(f"{VAULT}/knowledge_graph.json")
    gaps  = read_json(f"{VAULT}/knowledge_gaps.json")
    reports = read_json(f"{VAULT}/learning_report.json")
    last_report = reports[-1] if isinstance(reports, list) and reports else {}

    return {
        "brain": {
            "concepts": len(graph.get("nodes", [])),
            "connections": len(graph.get("edges", [])),
        },
        "gaps": len(gaps) if isinstance(gaps, list) else 0,
        "last_session": {
            "topics": last_report.get("topics_learned", []),
            "new_concepts": last_report.get("new_concepts", 0),
            "new_connections": last_report.get("new_connections", 0),
            "time": last_report.get("started_at", "never")[:16].replace("T", " ") if last_report.get("started_at") else "never"
        }
    }

@app.get("/api/system")
def get_system():
    disk = psutil.disk_usage('/')
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "disk": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 1)
    }

@app.get("/api/graph")
def get_graph():
    graph = read_json(f"{VAULT}/knowledge_graph.json")
    nodes = [{"id": n["id"], "category": n.get("category", "general")}
             for n in graph.get("nodes", [])]
    edges = [{"source": e["source"], "target": e["target"], "relation": e.get("relation", "")}
             for e in graph.get("edges", [])]
    return {"nodes": nodes[:100], "edges": edges[:150]}

@app.get("/api/gaps")
def get_gaps():
    gaps = read_json(f"{VAULT}/knowledge_gaps.json")
    if isinstance(gaps, list):
        return {"gaps": gaps[:10]}
    return {"gaps": []}

@app.get("/api/alerts")
def get_alerts():
    lines = read_log_tail(f"{LOGS}/alerts.log", 15)
    return {"alerts": lines}

@app.get("/api/activity")
def get_activity():
    lines = read_log_tail(f"{LOGS}/audit.log", 15)
    return {"activity": lines}

@app.get("/api/sources")
def get_sources():
    sources = read_json(f"{VAULT}/learned_sources.json")
    if isinstance(sources, list):
        return {"sources": sources[-10:], "total": len(sources)}
    return {"sources": [], "total": 0}


@app.get("/")
def serve_dashboard():
    return FileResponse("/home/david/cerebro-sentinel/dashboard/index.html")