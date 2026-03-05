# CEREBRO Sentinel v0.1

> A local-first, proactive AI assistant that watches, remembers, and acts — without sending your data anywhere.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Status](https://img.shields.io/badge/status-active-brightgreen)

---

## What is CEREBRO Sentinel?

Most AI tools are **reactive** — they wait for you to ask before they do anything.

CEREBRO Sentinel is **proactive** — it watches your environment, analyses what's happening, and acts on your behalf before you have to ask.

It runs entirely on your local machine. No cloud. No subscriptions. No data leaving your hardware.

---

## Core Capabilities

| Capability | Description |
|---|---|
| 🧠 **Local AI Brain** | Powered by `qwen2.5-coder:7b` via Ollama — runs on your GPU |
| 👁️ **File Watcher** | Monitors your workspace and analyses code changes in real time |
| 🖥️ **System Monitor** | Tracks CPU, RAM and Disk — alerts you proactively when needed |
| 💾 **Persistent Memory** | Vector-based memory via Qdrant — remembers your preferences across sessions |
| 🤝 **Command Interface** | Natural language commands that map to real actions |
| 🔒 **Permission Vault** | IAM-style access control — Cerebro cannot act outside defined boundaries |
| 📋 **Audit Log** | Every action Cerebro takes is logged with timestamp and approval status |

---

## Architecture

```
cerebro-sentinel/
│
├── agents/
│   ├── cerebro_core.py          # Core brain — connects Python to Ollama
│   ├── cerebro_unified.py       # Unified watcher + brain + memory
│   ├── cerebro_voice.py         # Natural language command interface
│   ├── cerebro_secured.py       # Secured interface with vault integration
│   └── memory_engine.py         # Qdrant vector memory system
│
├── tools/
│   ├── file_watcher.py          # Watchdog-based workspace monitor
│   ├── system_monitor.py        # CPU/RAM/Disk proactive monitor
│   └── audit_viewer.py          # Human-readable audit log viewer
│
├── vault/
│   ├── permissions.py           # Permission boundaries and approval flow
│   └── permissions.json         # Saved permission configuration
│
├── workspace/                   # Cerebro's sandboxed working directory
├── logs/                        # Activity, system and audit logs
└── docker-compose.yml           # n8n + Qdrant containerized stack
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Inference | Ollama + qwen2.5-coder:7b | Local AI brain |
| Orchestration | LangChain + LangGraph | Agent logic and chaining |
| Memory | Qdrant (Docker) | Vector-based persistent memory |
| Embeddings | sentence-transformers | Converts text to memory vectors |
| Automation | n8n (Docker) | Event triggers and workflows |
| File Watching | Watchdog | Proactive workspace monitoring |
| System Monitoring | psutil | Hardware health tracking |
| Security | Custom Vault | IAM-style permission boundaries |
| Environment | Python venv + WSL2 | Isolated, reproducible setup |

---

## Prerequisites

- Windows 11 with WSL2 (Ubuntu 22.04)
- Docker Desktop
- Python 3.10+
- 16GB RAM minimum
- NVIDIA GPU recommended (4GB+ VRAM)
- Ollama installed on Windows host

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/cerebro-sentinel.git
cd cerebro-sentinel
```

**2. Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install langchain-ollama langgraph langchain-core python-dotenv requests
pip install watchdog psutil qdrant-client sentence-transformers
pip install SpeechRecognition pyttsx3 pyaudio
```

**4. Pull the local model**
```bash
ollama pull qwen2.5-coder:7b
```

**5. Start the Docker stack**
```bash
docker compose up -d
```

**6. Get your WSL-to-Windows IP**
```bash
ip route show | grep -i default | awk '{ print $3}'
```
Update `OLLAMA_URL` in all agent files with this IP.

---

## Usage

### Secured Command Interface
```bash
python agents/cerebro_secured.py
```

```
David: Who are you and what do you remember about me?
David: Create a file called server.py
David: What should I use for my backend?
David: exit
```

### Proactive File Watcher
```bash
python agents/cerebro_unified.py
```
Cerebro will automatically analyse any file saved to the `workspace/` directory.

### System Monitor
```bash
python tools/system_monitor.py
```
Reports CPU, RAM and Disk every 30 seconds. Alerts intelligently when thresholds are crossed.

### View Audit Log
```bash
python tools/audit_viewer.py
```

---

## Security Model

CEREBRO Sentinel operates on a **least-privilege principle** — the same concept behind AWS IAM.

- ✅ Can read/write inside `workspace/` and `logs/`
- 🚫 Cannot touch `~/.ssh`, `~/.aws`, `/etc`, `/root`
- ✅ Can read files and monitor system
- 🚫 Cannot delete files or execute arbitrary scripts
- ⚠️ File creation requires explicit human approval
- 📋 Every action is logged with timestamp and status

---

## Privacy

- Zero data sent to external servers
- All inference runs locally on your hardware
- Memory stored in local Qdrant instance
- No telemetry, no tracking, no cloud dependency

---

## Roadmap

- [x] v0.1 — Local brain, file watcher, memory, security vault
- [ ] v0.2 — Voice interface via Windows audio bridge
- [ ] v0.3 — Git integration and automated code review
- [ ] v0.4 — Docker container management
- [ ] v1.0 — Full autonomous dev environment

---

## Built With

- [Ollama](https://ollama.com) — Local LLM inference
- [LangChain](https://langchain.com) — AI orchestration
- [Qdrant](https://qdrant.tech) — Vector database
- [n8n](https://n8n.io) — Workflow automation
- [Watchdog](https://github.com/gorakhargosh/watchdog) — File system monitoring

---

## Author

**David Onoja**
Building at the intersection of DevOps, Cloud Security, and AI Infrastructure.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
