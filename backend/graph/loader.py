"""
backend/graph/loader.py
Convenience loader — returns a ready-to-use graph, building it if absent.
"""
import logging
import networkx as nx
from backend.graph.builder import KnowledgeGraphBuilder

logger = logging.getLogger("KGLoader")


def load_or_build(force_rebuild: bool = False) -> nx.DiGraph:
    """Load the persisted graph; rebuild from scratch if not found or forced."""
    builder = KnowledgeGraphBuilder()
    if not force_rebuild:
        G = builder.load()
        if G is not None:
            return G
    logger.info("Building Knowledge Graph from scratch...")
    return builder.build()
