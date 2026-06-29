"""
backend/graph/query.py
ChronoIKS Knowledge Graph Query Engine
Supports: shortest path, neighbour search, concept expansion,
          relationship search, subgraph extraction.
"""
import logging
from typing import Optional
import networkx as nx
from backend.graph.builder import KnowledgeGraphBuilder, NODE_CONCEPT, NODE_THINAI

logger = logging.getLogger("KGQuery")


class KnowledgeGraphQuery:
    def __init__(self, G: Optional[nx.DiGraph] = None):
        if G is None:
            builder = KnowledgeGraphBuilder()
            G = builder.load()
            if G is None:
                raise RuntimeError("Graph not built. Run: python chronoiks.py graph build")
        self.G = G

    # ── Node lookup ────────────────────────────────────────────────────────────

    def _resolve_node(self, name: str) -> Optional[str]:
        """Case-insensitive node lookup by name or Tamil text."""
        name_lower = name.strip().lower()
        for nid, data in self.G.nodes(data=True):
            if data.get("name", "").lower() == name_lower:
                return nid
            if data.get("tamil", "").strip() == name.strip():
                return nid
            if data.get("romanization", "").lower() == name_lower:
                return nid
        return None

    # ── 1. Neighbour search ────────────────────────────────────────────────────

    def get_neighbours(self, concept: str, depth: int = 1) -> dict:
        """Return all neighbour nodes within `depth` hops."""
        nid = self._resolve_node(concept)
        if not nid:
            return {"error": f"Node not found: '{concept}'"}

        result = {"query": concept, "node_id": nid, "depth": depth, "neighbours": []}
        visited = {nid}

        frontier = [nid]
        for d in range(depth):
            next_frontier = []
            for node in frontier:
                for successor in list(self.G.successors(node)) + list(self.G.predecessors(node)):
                    if successor not in visited:
                        visited.add(successor)
                        next_frontier.append(successor)
                        edge_data = (self.G.edges.get((node, successor))
                                     or self.G.edges.get((successor, node)) or {})
                        result["neighbours"].append({
                            "node_id":      successor,
                            "name":         self.G.nodes[successor].get("name", successor),
                            "node_type":    self.G.nodes[successor].get("node_type", "?"),
                            "relationship": edge_data.get("relationship", "CONNECTED"),
                            "hop":          d + 1,
                        })
            frontier = next_frontier
        return result

    # ── 2. Shortest path ──────────────────────────────────────────────────────

    def shortest_path(self, source: str, target: str) -> dict:
        """Return the shortest directed path between two concepts."""
        snid = self._resolve_node(source)
        tnid = self._resolve_node(target)
        if not snid:
            return {"error": f"Source not found: '{source}'"}
        if not tnid:
            return {"error": f"Target not found: '{target}'"}
        try:
            path = nx.shortest_path(self.G.to_undirected(), snid, tnid)
            path_info = []
            for i, nid in enumerate(path):
                rel = "START"
                if i > 0:
                    prev = path[i - 1]
                    rel = (self.G.edges.get((prev, nid))
                           or self.G.edges.get((nid, prev)) or {}).get("relationship", "CONNECTED")
                path_info.append({
                    "node_id":   nid,
                    "name":      self.G.nodes[nid].get("name", nid),
                    "node_type": self.G.nodes[nid].get("node_type", "?"),
                    "via":       rel,
                })
            return {"source": source, "target": target,
                    "path_length": len(path) - 1, "path": path_info}
        except nx.NetworkXNoPath:
            return {"error": f"No path between '{source}' and '{target}'"}
        except nx.NodeNotFound:
            return {"error": "One or more nodes not in graph"}

    # ── 3. Concept expansion ──────────────────────────────────────────────────

    def expand_concept(self, concept: str) -> dict:
        """Full semantic expansion: relationships, context, eras, works, themes."""
        nid = self._resolve_node(concept)
        if not nid:
            return {"error": f"Node not found: '{concept}'"}

        node_data = dict(self.G.nodes[nid])
        result = {
            "concept":         concept,
            "node_id":         nid,
            "node_type":       node_data.get("node_type"),
            "tamil":           node_data.get("tamil", ""),
            "english":         node_data.get("english", ""),
            "definition":      node_data.get("definition", ""),
            "related_concepts":[],
            "historical_context":[],
            "commentaries":    [],
            "source_works":    [],
            "themes":          [],
            "eras":            [],
            "similar_concepts":[],
            "synonyms":        [],
            "antonyms":        [],
            "philosophies":    [],
        }

        for succ in self.G.successors(nid):
            rel  = self.G.edges[nid, succ].get("relationship", "")
            data = self.G.nodes[succ]
            entry = {"name": data.get("name", succ), "node_type": data.get("node_type", "?")}

            if rel == "RELATED_TO":       result["related_concepts"].append(entry)
            elif rel == "COMMENTED_BY":   result["commentaries"].append(entry)
            elif rel == "DEFINED_IN":     result["source_works"].append(entry)
            elif rel == "BELONGS_TO_ERA": result["eras"].append(entry)
            elif rel == "HAS_THEME":      result["themes"].append(entry)
            elif rel == "SIMILAR_TO":     result["similar_concepts"].append(entry)
            elif rel == "SYNONYM_OF":     result["synonyms"].append(entry)
            elif rel == "ANTONYM_OF":     result["antonyms"].append(entry)
            elif rel == "PART_OF":        result["philosophies"].append(entry)

        # Predecessors for MENTIONED_IN and INFLUENCED_BY (reverse edges)
        for pred in self.G.predecessors(nid):
            rel = self.G.edges[pred, nid].get("relationship", "")
            data = self.G.nodes[pred]
            if rel == "MENTIONED_IN":
                result["source_works"].append({"name": data.get("name"), "node_type": data.get("node_type")})
            elif rel == "INFLUENCED_BY":
                result["historical_context"].append({"name": data.get("name"), "node_type": data.get("node_type")})

        # Deduplicate
        for key in result:
            if isinstance(result[key], list):
                seen = set()
                deduped = []
                for item in result[key]:
                    k = item.get("name", "")
                    if k not in seen:
                        seen.add(k)
                        deduped.append(item)
                result[key] = deduped
        return result

    # ── 4. Relationship search ────────────────────────────────────────────────

    def find_by_relationship(self, rel_type: str) -> list:
        """Return all edges with a given relationship type."""
        results = []
        for u, v, data in self.G.edges(data=True):
            if data.get("relationship", "").upper() == rel_type.upper():
                results.append({
                    "source":      self.G.nodes[u].get("name", u),
                    "source_type": self.G.nodes[u].get("node_type", "?"),
                    "relationship": rel_type,
                    "target":      self.G.nodes[v].get("name", v),
                    "target_type": self.G.nodes[v].get("node_type", "?"),
                })
        return results

    # ── 5. Subgraph extraction ────────────────────────────────────────────────

    def extract_subgraph(self, concept: str, depth: int = 2) -> nx.DiGraph:
        """Extract ego subgraph around a concept node."""
        nid = self._resolve_node(concept)
        if not nid:
            return nx.DiGraph()
        undirected = self.G.to_undirected()
        nodes_in_range = nx.single_source_shortest_path_length(
            undirected, nid, cutoff=depth).keys()
        return self.G.subgraph(nodes_in_range).copy()
