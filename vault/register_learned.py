import json
import os
import datetime

LEARNED_SOURCES_FILE = "/home/david/cerebro-sentinel/vault/learned_sources.json"

already_learned = [
    "https://docs.docker.com/guides/docker-overview/",
    "https://docs.docker.com/get-started/",
    "https://kubernetes.io/docs/concepts/overview/",
    "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
    "https://www.terraform.io/intro",
    "https://fastapi.tiangolo.com/",
    "https://docs.python.org/3/tutorial/",
    "https://owasp.org/www-project-top-ten/",
    "https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html",
    "https://docs.github.com/en/actions/about-github-actions/understanding-github-actions",
]

learned = {}
for url in already_learned:
    learned[url] = {"learned_at": datetime.datetime.now().isoformat()}

os.makedirs(os.path.dirname(LEARNED_SOURCES_FILE), exist_ok=True)
with open(LEARNED_SOURCES_FILE, "w") as f:
    json.dump(learned, f, indent=2)

print(f"[CEREBRO VAULT] Registered {len(learned)} learned sources ✅")
