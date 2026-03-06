import json
import os
import sys
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

GRAPH_FILE = "/home/david/cerebro-sentinel/vault/knowledge_graph.json"
OUTPUT_FILE = "/home/david/cerebro-sentinel/vault/cerebro_brain.png"

CATEGORY_COLORS = {
    "devops": "#00ff88",
    "cloud_security": "#ff6b6b",
    "security": "#ff9f43",
    "general": "#74b9ff",
    "default": "#a29bfe"
}

def visualize():
    if not os.path.exists(GRAPH_FILE):
        print("No graph found. Run knowledge_graph.py first.")
        return

    with open(GRAPH_FILE, "r") as f:
        data = json.load(f)

    G = nx.DiGraph()

    for node in data["nodes"]:
        G.add_node(
            node["id"],
            category=node.get("category", "general")
        )

    for edge in data["edges"]:
        G.add_edge(
            edge["source"],
            edge["target"],
            relationship=edge.get("relationship", "")
        )

    plt.figure(figsize=(20, 14))
    plt.style.use('dark_background')

    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Color nodes by category
    node_colors = []
    for node in G.nodes:
        category = G.nodes[node].get("category", "default")
        color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["default"])
        node_colors.append(color)

    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        edge_color="#444444",
        arrows=True,
        arrowsize=15,
        width=1.5,
        connectionstyle="arc3,rad=0.1"
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=1200,
        alpha=0.9
    )

    # Draw labels
    nx.draw_networkx_labels(
        G, pos,
        font_size=7,
        font_color="white",
        font_weight="bold"
    )

    # Edge labels
    edge_labels = {
        (u, v): G.edges[u, v]["relationship"]
        for u, v in G.edges
        if G.edges[u, v].get("relationship")
    }
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=edge_labels,
        font_size=5,
        font_color="#aaaaaa"
    )

    # Legend
    legend_patches = [
        mpatches.Patch(color=CATEGORY_COLORS["devops"], label="DevOps"),
        mpatches.Patch(color=CATEGORY_COLORS["cloud_security"], label="Cloud Security"),
        mpatches.Patch(color=CATEGORY_COLORS["security"], label="Security"),
        mpatches.Patch(color=CATEGORY_COLORS["general"], label="General"),
    ]
    plt.legend(handles=legend_patches, loc="upper left", fontsize=10)

    plt.title(
        f"CEREBRO Sentinel — Knowledge Graph\n"
        f"{G.number_of_nodes()} concepts | {G.number_of_edges()} connections",
        fontsize=14,
        color="white",
        pad=20
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches="tight", facecolor="black")
    print(f"\n[CEREBRO GRAPH] Brain visualization saved: {OUTPUT_FILE}")
    print(f"[CEREBRO GRAPH] Concepts: {G.number_of_nodes()}")
    print(f"[CEREBRO GRAPH] Connections: {G.number_of_edges()}")

if __name__ == "__main__":
    visualize()
