"""
backend/graph/reasoner.py
ChronoIKS Semantic Reasoner
Receives a user query (Tamil/English/Romanized) and produces
a structured reasoning report across the Knowledge Graph.
"""
import json
import logging
from typing import Optional
import networkx as nx
from backend.graph.query import KnowledgeGraphQuery

logger = logging.getLogger("KGReasoner")


class KnowledgeGraphReasoner:
    def __init__(self, G: Optional[nx.DiGraph] = None):
        self.query_engine = KnowledgeGraphQuery(G)

    def reason(self, user_input: str) -> dict:
        """
        Main reasoning entry point.
        Returns a structured report with related concepts, historical context,
        commentaries, similar concepts, theme, era, and author.
        """
        q = user_input.strip()
        expansion = self.query_engine.expand_concept(q)

        if "error" in expansion:
            return {
                "input":   q,
                "status":  "not_found",
                "message": expansion["error"],
                "suggestions": self._suggest_similar(q),
            }

        # Build concise reasoning report
        report = {
            "input":            q,
            "status":           "found",
            "concept":          expansion["concept"],
            "tamil":            expansion["tamil"],
            "english_meaning":  expansion["english"],
            "definition":       expansion["definition"],
            "node_type":        expansion["node_type"],
            "related_concepts": [c["name"] for c in expansion["related_concepts"]],
            "historical_context":[c["name"] for c in expansion["historical_context"]],
            "commentaries":     [c["name"] for c in expansion["commentaries"]],
            "similar_concepts": [c["name"] for c in expansion["similar_concepts"]],
            "synonyms":         [c["name"] for c in expansion["synonyms"]],
            "antonyms":         [c["name"] for c in expansion["antonyms"]],
            "themes":           [c["name"] for c in expansion["themes"]],
            "eras":             [c["name"] for c in expansion["eras"]],
            "source_works":     list({c["name"] for c in expansion["source_works"]}),
            "philosophies":     [c["name"] for c in expansion["philosophies"]],
        }

        # Path reasoning: connect concept to its deepest philosophical root
        roots = ["Mupporul", "Tinai", "Akam-Puram", "Ahimsa", "Dharma"]
        for root in roots:
            path = self.query_engine.shortest_path(q, root)
            if "error" not in path and path.get("path_length", 99) <= 4:
                report["philosophical_root"] = {
                    "root":        root,
                    "path_length": path["path_length"],
                    "path":        [p["name"] for p in path["path"]],
                }
                break

        return report

    def _suggest_similar(self, query: str) -> list:
        """Return node names that partially match the query string."""
        q_lower = query.lower()
        matches = []
        for nid, data in self.query_engine.G.nodes(data=True):
            name  = data.get("name", "").lower()
            tamil = data.get("tamil", "")
            roman = data.get("romanization", "").lower()
            if (q_lower in name or name in q_lower
                    or q_lower in roman or tamil == query.strip()):
                matches.append(data.get("name", nid))
                if len(matches) >= 8:
                    break
        return matches

    def format_report(self, report: dict) -> str:
        """Format reasoning report as readable terminal text."""
        if report["status"] == "not_found":
            lines = [
                f"\n  Concept not found: '{report['input']}'",
                f"  {report['message']}",
            ]
            if report.get("suggestions"):
                lines.append(f"  Did you mean: {', '.join(report['suggestions'])}")
            return "\n".join(lines)

        lines = [
            f"\n  Concept          : {report['concept']} ({report['tamil']})",
            f"  Node Type        : {report['node_type']}",
            f"  English Meaning  : {report['english_meaning']}",
        ]
        if report["definition"]:
            lines.append(f"  Definition       : {report['definition'][:120]}...")

        def _fmt(label, items):
            if items:
                lines.append(f"  {label:<20}: {', '.join(str(i) for i in items[:8])}")

        _fmt("Related Concepts",   report["related_concepts"])
        _fmt("Philosophies",       report["philosophies"])
        _fmt("Themes",             report["themes"])
        _fmt("Eras",               report["eras"])
        _fmt("Source Works",       report["source_works"])
        _fmt("Commentaries",       report["commentaries"])
        _fmt("Similar Concepts",   report["similar_concepts"])
        _fmt("Synonyms",           report["synonyms"])
        _fmt("Antonyms",           report["antonyms"])
        _fmt("Historical Context", report["historical_context"])

        root = report.get("philosophical_root")
        if root:
            path_str = " → ".join(root["path"])
            lines.append(f"  Phil. Root Path  : {path_str}")

        return "\n".join(lines)
