import json
import os
import sys
sys.path.append('/home/david/cerebro-sentinel/agents')

import networkx as nx
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from memory_engine import init_memory, remember, recall_formatted

OLLAMA_URL = "http://localhost:11434"
GRAPH_FILE = "/home/david/cerebro-sentinel/vault/knowledge_graph.json"

llm = ChatOllama(
    model="cerebro-v1",
    base_url=OLLAMA_URL,
    timeout=120
)

class CerebroKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.load_graph()

    def load_graph(self):
        """Load existing graph from disk"""
        if os.path.exists(GRAPH_FILE):
            with open(GRAPH_FILE, "r") as f:
                data = json.load(f)
            for node in data.get("nodes", []):
                self.graph.add_node(
                    node["id"],
                    category=node.get("category", "general"),
                    description=node.get("description", "")
                )
            for edge in data.get("edges", []):
                self.graph.add_edge(
                    edge["source"],
                    edge["target"],
                    relationship=edge.get("relationship", "relates_to")
                )
            print(f"[CEREBRO GRAPH] Loaded {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        else:
            print("[CEREBRO GRAPH] New knowledge graph created")

    def save_graph(self):
        """Save graph to disk"""
        data = {
            "nodes": [
                {
                    "id": node,
                    "category": self.graph.nodes[node].get("category", "general"),
                    "description": self.graph.nodes[node].get("description", "")
                }
                for node in self.graph.nodes
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "relationship": self.graph.edges[u, v].get("relationship", "relates_to")
                }
                for u, v in self.graph.edges
            ]
        }
        os.makedirs(os.path.dirname(GRAPH_FILE), exist_ok=True)
        with open(GRAPH_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def add_concept(self, concept: str, category: str, description: str = ""):
        """Add a concept node to the graph"""
        concept = concept.strip().lower()
        if concept and len(concept) > 2:
            self.graph.add_node(
                concept,
                category=category,
                description=description
            )

    def add_relationship(self, source: str, target: str, relationship: str):
        """Add a relationship between two concepts"""
        source = source.strip().lower()
        target = target.strip().lower()
        if source and target and source != target:
            if not self.graph.has_node(source):
                self.graph.add_node(source, category="general", description="")
            if not self.graph.has_node(target):
                self.graph.add_node(target, category="general", description="")
            self.graph.add_edge(source, target, relationship=relationship)

    def extract_relationships(self, topic: str, memories: str) -> list:
        """Use Cerebro to find relationships between concepts"""
        messages = [
            SystemMessage(content="""You are Cerebro's knowledge graph builder.
            Find relationships between concepts.
            Always respond in this EXACT format only, nothing else:
            
            RELATIONSHIPS:
            concept1 -> concept2 : relationship
            concept2 -> concept3 : relationship
            
            Use relationships like: uses, runs_on, manages, secures, 
            part_of, enables, requires, deploys, monitors, extends
            
            Maximum 10 relationships. Be specific and accurate."""),
            HumanMessage(content=f"""
Topic: {topic}

Known information:
{memories}

Extract concept relationships:
""")
        ]

        response = llm.invoke(messages)
        content = response.content

        relationships = []
        if "RELATIONSHIPS:" in content:
            lines = content.split("RELATIONSHIPS:")[1].strip().split("\n")
            for line in lines:
                line = line.strip()
                if "->" in line and ":" in line:
                    try:
                        parts = line.split("->")
                        source = parts[0].strip()
                        rest = parts[1].split(":")
                        target = rest[0].strip()
                        relationship = rest[1].strip() if len(rest) > 1 else "relates_to"
                        if source and target:
                            relationships.append({
                                "source": source,
                                "target": target,
                                "relationship": relationship
                            })
                    except:
                        continue

        return relationships

    def learn_topic(self, topic: str, category: str = "general"):
        """Build graph connections for a topic"""
        print(f"\n[CEREBRO GRAPH] Building connections for: {topic}")

        # Get memories about this topic
        init_memory()
        memories = recall_formatted(topic)

        if "No relevant memories" in memories:
            print(f"[CEREBRO GRAPH] No memories found for '{topic}'")
            print(f"[CEREBRO GRAPH] Feed Cerebro some knowledge first.")
            return

        # Extract relationships
        relationships = self.extract_relationships(topic, memories)

        # Add to graph
        self.add_concept(topic, category)
        added = 0
        for rel in relationships:
            self.add_relationship(
                rel["source"],
                rel["target"],
                rel["relationship"]
            )
            added += 1
            print(f"[CEREBRO GRAPH] ✅ {rel['source']} --[{rel['relationship']}]--> {rel['target']}")

        self.save_graph()
        print(f"\n[CEREBRO GRAPH] Added {added} connections for '{topic}'")
        return relationships

    def find_connections(self, concept_a: str, concept_b: str):
        """Find how two concepts are connected"""
        concept_a = concept_a.strip().lower()
        concept_b = concept_b.strip().lower()

        if not self.graph.has_node(concept_a):
            return f"I don't have '{concept_a}' in my knowledge graph yet."
        if not self.graph.has_node(concept_b):
            return f"I don't have '{concept_b}' in my knowledge graph yet."

        try:
            path = nx.shortest_path(self.graph, concept_a, concept_b)
            result = f"Connection found:\n"
            for i in range(len(path) - 1):
                rel = self.graph.edges[path[i], path[i+1]].get("relationship", "relates_to")
                result += f"  {path[i]} --[{rel}]--> {path[i+1]}\n"
            return result
        except nx.NetworkXNoPath:
            return f"No direct connection found between '{concept_a}' and '{concept_b}' yet."

    def what_uses(self, concept: str) -> list:
        """Find what concepts use this concept"""
        concept = concept.strip().lower()
        predecessors = list(self.graph.predecessors(concept))
        return predecessors

    def what_does_it_use(self, concept: str) -> list:
        """Find what this concept uses"""
        concept = concept.strip().lower()
        successors = list(self.graph.successors(concept))
        return successors

    def get_stats(self):
        """Get graph statistics"""
        return {
            "total_concepts": self.graph.number_of_nodes(),
            "total_connections": self.graph.number_of_edges(),
            "concepts": list(self.graph.nodes)[:20]
        }


if __name__ == "__main__":
    graph = CerebroKnowledgeGraph()

    print("\n[CEREBRO GRAPH] Building knowledge connections...\n")

    # Build connections for everything Cerebro has learned
    topics = [
        ("docker", "devops"),
        ("kubernetes", "devops"),
        ("aws iam", "cloud_security"),
        ("containers", "devops"),
        ("owasp", "security"),
    ]

    for topic, category in topics:
        graph.learn_topic(topic, category)

    # Show stats
    stats = graph.get_stats()
    print(f"\n[CEREBRO GRAPH] Knowledge Graph Stats:")
    print(f"  Total concepts: {stats['total_concepts']}")
    print(f"  Total connections: {stats['total_connections']}")
    print(f"  Known concepts: {', '.join(stats['concepts'][:10])}")

    # Test connection finding
    print("\n[CEREBRO GRAPH] Testing connections...")
    print(graph.find_connections("docker", "kubernetes"))
