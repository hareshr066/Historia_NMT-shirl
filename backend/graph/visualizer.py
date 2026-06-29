"""
backend/graph/visualizer.py
ChronoIKS Knowledge Graph Visualizer
Generates: Interactive HTML (pyvis), PNG (matplotlib), GraphML, JSON
"""
import os
import json
import logging
from typing import Optional
import networkx as nx
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

logger = logging.getLogger("KGVisualizer")

# Node type → colour mapping
NODE_COLORS = {
    "Concept":     "#3b82f6",   # blue
    "LiteraryWork":"#8b5cf6",   # purple
    "Author":      "#10b981",   # emerald
    "Era":         "#f59e0b",   # amber
    "Commentary":  "#ec4899",   # pink
    "Translator":  "#06b6d4",   # cyan
    "Theme":       "#84cc16",   # lime
    "Thinai":      "#f97316",   # orange
    "Philosophy":  "#a78bfa",   # violet
    "Deity":       "#fcd34d",   # yellow
    "Location":    "#6ee7b7",   # mint
    "Kingdom":     "#fca5a5",   # rose
    "Emotion":     "#c4b5fd",   # lavender
    "GrammarRule": "#93c5fd",   # light blue
}
DEFAULT_COLOR = "#94a3b8"

# Edge relationship → colour mapping
EDGE_COLORS = {
    "RELATED_TO":    "#3b82f6",
    "DEFINED_IN":    "#8b5cf6",
    "WRITTEN_BY":    "#10b981",
    "BELONGS_TO_ERA":"#f59e0b",
    "COMMENTED_BY":  "#ec4899",
    "HAS_THEME":     "#84cc16",
    "PART_OF":       "#f97316",
    "SIMILAR_TO":    "#06b6d4",
    "INFLUENCED_BY": "#ef4444",
    "SYNONYM_OF":    "#a78bfa",
    "ANTONYM_OF":    "#fcd34d",
    "MENTIONED_IN":  "#64748b",
    "HAS_TRANSLATION":"#94a3b8",
}


class KnowledgeGraphVisualizer:
    HTML_PATH = "results/knowledge_graph.html"
    PNG_PATH  = "results/knowledge_graph.png"

    def __init__(self, G: Optional[nx.DiGraph] = None):
        if G is None:
            from backend.graph.builder import KnowledgeGraphBuilder
            builder = KnowledgeGraphBuilder()
            G = builder.load()
            if G is None:
                raise RuntimeError("Graph not built. Run: python chronoiks.py graph build")
        self.G = G
        os.makedirs("results", exist_ok=True)

    # ── Interactive HTML via pyvis ─────────────────────────────────────────────

    def generate_html(self, subgraph: Optional[nx.DiGraph] = None) -> str:
        try:
            from pyvis.network import Network
        except ImportError:
            logger.error("pyvis not installed. Run: pip install pyvis")
            return ""

        G = subgraph if subgraph is not None else self.G
        net = Network(
            height="900px", width="100%",
            bgcolor="#0f0f13", font_color="#e2e8f0",
            directed=True,
            notebook=False,
        )
        net.set_options("""
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -60,
              "centralGravity": 0.005,
              "springLength": 120,
              "springConstant": 0.08
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 200}
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.6}},
            "smooth": {"type": "curvedCW", "roundness": 0.2},
            "font": {"size": 9, "color": "#94a3b8"}
          },
          "nodes": {
            "font": {"size": 12, "face": "Inter, sans-serif"},
            "borderWidth": 2,
            "shadow": true
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 150,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        """)

        for nid, data in G.nodes(data=True):
            ntype = data.get("node_type", "Concept")
            color = NODE_COLORS.get(ntype, DEFAULT_COLOR)
            label = data.get("name", nid)
            tamil = data.get("tamil", "")
            tip   = (f"<b>{label}</b><br/>Type: {ntype}<br/>"
                     f"Tamil: {tamil}<br/>{data.get('english', '')}")
            size  = 20 if ntype == "Concept" else (
                    18 if ntype in ("LiteraryWork", "Thinai", "Philosophy") else 14)
            net.add_node(nid, label=label, color=color, title=tip,
                         size=size, shape="dot")

        for u, v, data in G.edges(data=True):
            rel   = data.get("relationship", "CONNECTED")
            color = EDGE_COLORS.get(rel, "#475569")
            net.add_edge(u, v, label=rel, color=color, width=1.5)

        net.save_graph(self.HTML_PATH)
        logger.info(f"Saved interactive HTML: {self.HTML_PATH}")
        return self.HTML_PATH

    # ── Static PNG via matplotlib ─────────────────────────────────────────────

    def generate_png(self, max_nodes: int = 80) -> str:
        G = self.G
        # Limit to top nodes by degree for readability
        if G.number_of_nodes() > max_nodes:
            top = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:max_nodes]
            G = G.subgraph([n for n, _ in top]).copy()

        fig, ax = plt.subplots(figsize=(22, 16))
        fig.patch.set_facecolor("#0f0f13")
        ax.set_facecolor("#0f0f13")

        # Layout
        try:
            pos = nx.kamada_kawai_layout(G)
        except Exception:
            pos = nx.spring_layout(G, seed=42, k=2.0)

        # Draw edges
        for u, v, data in G.edges(data=True):
            rel = data.get("relationship", "")
            color = EDGE_COLORS.get(rel, "#334155")
            nx.draw_networkx_edges(
                G, pos, edgelist=[(u, v)], edge_color=[color],
                ax=ax, alpha=0.5, arrows=True,
                arrowsize=10, arrowstyle="-|>",
                connectionstyle="arc3,rad=0.1", width=0.8,
            )

        # Draw nodes grouped by type
        node_types = {}
        for nid, data in G.nodes(data=True):
            nt = data.get("node_type", "Concept")
            node_types.setdefault(nt, []).append(nid)

        for ntype, nodes in node_types.items():
            color = NODE_COLORS.get(ntype, DEFAULT_COLOR)
            size  = 600 if ntype == "Concept" else (
                    500 if ntype in ("LiteraryWork", "Thinai") else 350)
            nx.draw_networkx_nodes(
                G, pos, nodelist=nodes, node_color=color,
                node_size=size, ax=ax, alpha=0.92,
            )

        # Labels
        labels = {n: G.nodes[n].get("name", n)[:14] for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=6,
                                font_color="#e2e8f0", ax=ax)

        # Legend
        legend_patches = [
            mpatches.Patch(color=c, label=t)
            for t, c in NODE_COLORS.items()
            if any(G.nodes[n].get("node_type") == t for n in G.nodes())
        ]
        ax.legend(handles=legend_patches, loc="upper left",
                  fontsize=7, facecolor="#1e1e2e", labelcolor="#e2e8f0",
                  framealpha=0.85, ncol=2)

        ax.set_title("ChronoIKS Knowledge Graph v1",
                     color="#e2e8f0", fontsize=14, pad=12)
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(self.PNG_PATH, dpi=140, bbox_inches="tight",
                    facecolor="#0f0f13")
        plt.close()
        logger.info(f"Saved PNG: {self.PNG_PATH}")
        return self.PNG_PATH

    # ── Export all formats ────────────────────────────────────────────────────

    def export_all(self) -> dict:
        paths = {}
        paths["html"]    = self.generate_html()
        paths["png"]     = self.generate_png()
        paths["graphml"] = "results/knowledge_graph.graphml"   # already saved by builder
        paths["json"]    = "results/knowledge_graph.json"       # already saved by builder
        return paths
