import sys
import os
sys.path.append('/home/david/cerebro-sentinel/agents')
sys.path.append('/home/david/cerebro-sentinel/learning/ingestion')

from ddgs import DDGS
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

OLLAMA_URL = "http://localhost:11434"
llm = ChatOllama(model="cerebro-v1", base_url=OLLAMA_URL, timeout=120)

def search_best_sources(topic: str) -> list:
    """Search for the best learning sources for a topic"""
    print(f"[CEREBRO SEARCH] Searching for: {topic}")

    search_queries = [
        f"{topic} documentation official",
        f"{topic} tutorial beginners guide",
        f"what is {topic} devops"
    ]

    all_results = []

    with DDGS() as ddgs:
        for query in search_queries[:2]:
            try:
                results = list(ddgs.text(query, max_results=3))
                all_results.extend(results)
            except Exception as e:
                print(f"[CEREBRO SEARCH] Search error: {e}")
                continue

    # Filter for high quality sources
    quality_domains = [
        "docs.", "documentation", "official",
        "kubernetes.io", "docker.com", "aws.amazon.com",
        "terraform.io", "github.com", "mozilla.org",
        "python.org", "fastapi.tiangolo.com",
        "owasp.org", "cloudflare.com", "nginx.org"
    ]

    # Score and filter results
    scored = []
    seen_urls = set()

    for result in all_results:
        url = result.get("href", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        score = 0
        for domain in quality_domains:
            if domain in url:
                score += 2

        # Avoid PDFs and login pages
        if any(skip in url for skip in [".pdf", "login", "signup", "youtube"]):
            continue

        scored.append({"url": url, "title": result.get("title", ""), "score": score})

    # Sort by score
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_urls = [r["url"] for r in scored[:3]]

    print(f"[CEREBRO SEARCH] Found {len(top_urls)} quality sources")
    for url in top_urls:
        print(f"[CEREBRO SEARCH]   → {url}")

    return top_urls

def learn_from_search(topic: str) -> bool:
    """Search and learn about a topic autonomously"""
    from web_reader import learn_from_url, is_already_learned

    urls = search_best_sources(topic)

    if not urls:
        print(f"[CEREBRO SEARCH] No sources found for: {topic}")
        return False

    learned_count = 0
    for url in urls:
        if is_already_learned(url):
            print(f"[CEREBRO SEARCH] Already learned: {url}")
            continue

        try:
            learn_from_url(url)
            learned_count += 1
        except Exception as e:
            print(f"[CEREBRO SEARCH] Failed to learn from {url}: {e}")
            continue

    return learned_count > 0

if __name__ == "__main__":
    print("=" * 55)
    print("  CEREBRO — Autonomous Web Searcher")
    print("=" * 55)

    topic = "helm kubernetes package manager"
    print(f"\n[CEREBRO SEARCH] Topic: {topic}\n")

    urls = search_best_sources(topic)
    print(f"\n[CEREBRO SEARCH] Best sources found: {len(urls)}")
