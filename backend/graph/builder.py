"""
backend/graph/builder.py
ChronoIKS Knowledge Graph Builder v1
Constructs a NetworkX DiGraph from the IKS Knowledge Base and corpus data.
Neo4j-ready: all node/edge structures mirror Cypher property conventions.
"""
import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Optional
import networkx as nx

logger = logging.getLogger("KGBuilder")

# ── Node type constants ────────────────────────────────────────────────────────
NODE_CONCEPT      = "Concept"
NODE_AUTHOR       = "Author"
NODE_WORK         = "LiteraryWork"
NODE_ERA          = "Era"
NODE_COMMENTARY   = "Commentary"
NODE_TRANSLATOR   = "Translator"
NODE_THEME        = "Theme"
NODE_THINAI       = "Thinai"
NODE_PHILOSOPHY   = "Philosophy"
NODE_DEITY        = "Deity"
NODE_LOCATION     = "Location"
NODE_KINGDOM      = "Kingdom"
NODE_EMOTION      = "Emotion"
NODE_GRAMMAR      = "GrammarRule"

# ── Relationship type constants ────────────────────────────────────────────────
REL_RELATED_TO    = "RELATED_TO"
REL_SUPPORT       = "SUPPORT"
REL_DEFINED_IN    = "DEFINED_IN"
REL_MENTIONED_IN  = "MENTIONED_IN"
REL_COMMENTED_BY  = "COMMENTED_BY"
REL_BELONGS_ERA   = "BELONGS_TO_ERA"
REL_WRITTEN_BY    = "WRITTEN_BY"
REL_HAS_TRANS     = "HAS_TRANSLATION"
REL_HAS_MEANING   = "HAS_MEANING"
REL_HAS_THEME     = "HAS_THEME"
REL_PART_OF       = "PART_OF"
REL_SIMILAR_TO    = "SIMILAR_TO"
REL_INFLUENCED_BY = "INFLUENCED_BY"
REL_SYNONYM_OF    = "SYNONYM_OF"
REL_ANTONYM_OF    = "ANTONYM_OF"

# ── Static enrichment data ─────────────────────────────────────────────────────
THINAI_MAP = {
    "kurinji":  {"emotion": "Union/Secret Love",    "location": "Mountain",      "season": "Cold/Night"},
    "mullai":   {"emotion": "Patient Waiting",       "location": "Forest",        "season": "Rainy/Evening"},
    "marutham": {"emotion": "Lover's Quarrel",       "location": "Agricultural",  "season": "All Seasons"},
    "neythal":  {"emotion": "Separation/Grief",      "location": "Coastal",       "season": "Evening/Dusk"},
    "palai":    {"emotion": "Journey/Separation",    "location": "Arid Desert",   "season": "Summer"},
}

PHILOSOPHY_MAP = {
    "Mupporul":   ["Aram", "Porul", "Inbam"],
    "Tinai":      ["Kurinji", "Mullai", "Marutham", "Neythal", "Palai"],
    "Akam-Puram": ["Akam", "Puram"],
    "Ahimsa":     ["Kollamai", "Arul", "Thavam"],
    "Dharma":     ["Aram", "Ozhukkam", "Sengol"],
}

DEITY_MAP = {
    "Murugan":   ["Kurinji", "Thirukkural"],
    "Thirumal":  ["Marutham", "Paripadal"],
    "Indiran":   ["Puram", "Purananuru"],
    "Korravai":  ["Palai", "Puram"],
}

ANTONYM_MAP = {
    "Aram":     ["Pavam"],
    "Anbu":     ["Venkopam"],
    "Arul":     ["Kolai"],
    "Viram":    ["Peedu"],
    "Vaimai":   ["Poi"],
    "Kollamai": ["Kolai"],
}

SYNONYM_MAP = {
    "Aram":    ["Dharma", "Aaram"],
    "Anbu":    ["Kadhal", "Prema"],
    "Arul":    ["Karuna", "Grace"],
    "Viram":   ["Veeram", "Souram"],
    "Porul":   ["Artha", "Selvam"],
    "Inbam":   ["Kamam", "Anandham"],
}

KINGDOM_WORKS_MAP = {
    "Chera Kingdom":  ["Pathitrupathu", "Purananuru"],
    "Chola Kingdom":  ["Purananuru", "Pattinappaalai", "Maduraikanchi"],
    "Pandya Kingdom": ["Purananuru", "Maduraikanchi", "Silappathikaram"],
    "Madurai City":   ["Maduraikanchi", "Silappathikaram", "Manimekalai"],
    "Puhar City":     ["Silappathikaram", "Pattinappaalai"],
}

INFLUENCED_BY_MAP = {
    "Manimekalai":    ["Silappathikaram"],
    "Silappathikaram":["Tolkappiyam", "Thirukkural"],
    "Thirukkural":    ["Tolkappiyam"],
    "Purananuru":     ["Tolkappiyam"],
}


class KnowledgeGraphBuilder:
    """
    Builds and persists the ChronoIKS Knowledge Graph using NetworkX.
    All nodes/edges follow Neo4j-compatible property conventions for future migration.
    """

    GRAPH_PATH = "results/knowledge_graph.graphml"
    JSON_PATH  = "results/knowledge_graph.json"

    def __init__(self, kb_path="knowledge_base/iks_kb.json",
                 corpus_path="datasets/processed/processed_corpus.json"):
        self.kb_path     = kb_path
        self.corpus_path = corpus_path
        self.G           = nx.DiGraph()
        os.makedirs("results", exist_ok=True)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _nid(self, node_type: str, name: str) -> str:
        """Deterministic node ID: TYPE::slug"""
        slug = name.strip().lower().replace(" ", "_").replace("/", "_")
        return f"{node_type}::{slug}"

    def _add_node(self, node_type: str, name: str, **props):
        nid = self._nid(node_type, name)
        if not self.G.has_node(nid):
            self.G.add_node(nid, node_type=node_type, name=name, **props)
        return nid

    def _add_edge(self, src: str, rel: str, dst: str, **props):
        if src and dst and src != dst:
            self.G.add_edge(src, dst, relationship=rel, **props)

    # ── Stage 1: Knowledge Base nodes ─────────────────────────────────────────

    def _load_kb(self):
        if not os.path.exists(self.kb_path):
            logger.warning(f"KB file not found: {self.kb_path}")
            return []
        with open(self.kb_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_concept_nodes(self, kb: list):
        logger.info(f"Building concept nodes from {len(kb)} KB entries...")
        for entry in kb:
            concept_name = entry.get("concept", "")
            if not concept_name:
                continue

            # Determine node type
            cid = entry.get("concept_id", "").lower()
            if cid in THINAI_MAP:
                ntype = NODE_THINAI
            elif cid in ("akam", "puram", "tinai"):
                ntype = NODE_PHILOSOPHY
            elif cid in ("arasan", "sengol", "arasu"):
                ntype = NODE_CONCEPT
            else:
                ntype = NODE_CONCEPT

            cnode = self._add_node(
                ntype, concept_name,
                tamil        = entry.get("tamil", ""),
                romanization = entry.get("romanization", ""),
                language     = entry.get("language", "Tamil"),
                english      = entry.get("english", ""),
                definition   = entry.get("definition", ""),
                confidence   = entry.get("confidence", 1.0),
                source_ref   = entry.get("source_reference", ""),
            )

            # Era node + edge
            era_str = entry.get("era", "").strip()
            if era_str:
                enode = self._add_node(NODE_ERA, era_str, period=era_str)
                self._add_edge(cnode, REL_BELONGS_ERA, enode)

            # Commentary nodes + edges
            commentary_raw = entry.get("commentary_reference", "")
            for commentator in [c.strip() for c in commentary_raw.split(",") if c.strip()]:
                com_node = self._add_node(NODE_COMMENTARY, commentator,
                                          commentator=commentator)
                self._add_edge(cnode, REL_COMMENTED_BY, com_node)

            # Source works + DEFINED_IN edges
            source_raw = entry.get("source_reference", "")
            for work_hint in ["Thirukkural", "Purananuru", "Tolkappiyam",
                               "Silappathikaram", "Manimekalai", "Kurunthokai",
                               "Kalithogai", "Ainkurunuru", "Akananuru",
                               "Natrinai", "Pathitrupathu", "Pattinappaalai",
                               "Maduraikanchi", "Paripadal"]:
                if work_hint.lower() in source_raw.lower():
                    wnode = self._add_node(NODE_WORK, work_hint)
                    self._add_edge(cnode, REL_DEFINED_IN, wnode)

            # Related concept edges (RELATED_TO)
            for rel_name in entry.get("related_concepts", []):
                rel_node = self._add_node(NODE_CONCEPT, rel_name)
                self._add_edge(cnode, REL_RELATED_TO, rel_node,
                                weight=0.8, inferred=False)

            # Synonym edges
            synonyms = SYNONYM_MAP.get(concept_name, [])
            for syn in synonyms:
                snode = self._add_node(NODE_CONCEPT, syn)
                self._add_edge(cnode, REL_SYNONYM_OF, snode)

            # Antonym edges
            antonyms = ANTONYM_MAP.get(concept_name, [])
            for ant in antonyms:
                anode = self._add_node(NODE_CONCEPT, ant)
                self._add_edge(cnode, REL_ANTONYM_OF, anode)

    # ── Stage 2: Literary Work metadata nodes ─────────────────────────────────

    WORK_META = {
        "Thirukkural":     {"author": "Tiruvalluvar",             "translator": "G.U. Pope",                  "era": "Post-Sangam (c. 1st–5th century CE)",  "theme": "Ethics/Virtue", "literary_type": "Didactic"},
        "Tolkappiyam":     {"author": "Tolkappiyar",              "translator": "P.S. Subrahmanya Sastri",    "era": "Pre-Sangam (c. 300 BCE)",               "theme": "Grammar/Linguistics", "literary_type": "Grammatical"},
        "Purananuru":      {"author": "Various Sangam Poets",     "translator": "A.K. Ramanujan",             "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "Heroism/War/Virtue", "literary_type": "Heroic/Puram"},
        "Akananuru":       {"author": "Various Sangam Poets",     "translator": "A.K. Ramanujan",             "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "Love/Landscape", "literary_type": "Love/Akam"},
        "Kurunthogai":     {"author": "Various Sangam Poets",     "translator": "A.K. Ramanujan",             "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "Love/Akam", "literary_type": "Love/Akam"},
        "Natrinai":        {"author": "Various Sangam Poets",     "translator": "A.K. Ramanujan",             "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "Love/Landscape", "literary_type": "Love/Akam"},
        "Pathitrupathu":   {"author": "Various Sangam Poets",     "translator": "George L. Hart",             "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "Royalty/Heroism", "literary_type": "Heroic/Puram"},
        "Paripadal":       {"author": "Kaduvan Ilaveyinanar",     "translator": "A. Dakshinamurthy",          "era": "Sangam (c. 1st–3rd century CE)",         "theme": "Devotion/Music", "literary_type": "Devotional"},
        "Kalithogai":      {"author": "Kapilar / Various",        "translator": "A.K. Ramanujan",             "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "Love/Akam", "literary_type": "Love/Akam"},
        "Ainkurunuru":     {"author": "Various Sangam Poets",     "translator": "A.K. Ramanujan",             "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "Love/Landscape", "literary_type": "Love/Akam"},
        "Pattinappaalai":  {"author": "Kadiyalur Uruthirankannanar","translator":"J.V. Chelliah",             "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "City/Love", "literary_type": "Love/Akam"},
        "Maduraikanchi":   {"author": "Mangudi Maruthanar",       "translator": "J.V. Chelliah",              "era": "Sangam (c. 300 BCE – 300 CE)",          "theme": "Royalty/City", "literary_type": "Heroic/Puram"},
        "Silappathikaram": {"author": "Ilankovatikal",            "translator": "R. Parthasarathy",           "era": "Post-Sangam (c. 5th century CE)",        "theme": "Justice/Epic", "literary_type": "Epic/Narrative"},
        "Manimekalai":     {"author": "Cittalai Cattanar",        "translator": "Alain Danielou",             "era": "Post-Sangam (c. 5th–6th century CE)",   "theme": "Buddhism/Epic", "literary_type": "Epic/Narrative"},
    }

    def _build_work_nodes(self):
        logger.info("Building literary work, author, translator, and theme nodes...")
        for work_name, meta in self.WORK_META.items():
            wnode = self._add_node(NODE_WORK, work_name,
                                   literary_type=meta["literary_type"],
                                   era=meta["era"])

            # Author
            anode = self._add_node(NODE_AUTHOR, meta["author"],
                                   period=meta["era"])
            self._add_edge(wnode, REL_WRITTEN_BY, anode)

            # Translator
            tnode = self._add_node(NODE_TRANSLATOR, meta["translator"])
            self._add_edge(wnode, REL_HAS_TRANS, tnode)

            # Era
            enode = self._add_node(NODE_ERA, meta["era"], period=meta["era"])
            self._add_edge(wnode, REL_BELONGS_ERA, enode)

            # Theme
            thnode = self._add_node(NODE_THEME, meta["theme"])
            self._add_edge(wnode, REL_HAS_THEME, thnode)

        # Work influence edges
        for influenced, sources in INFLUENCED_BY_MAP.items():
            inode = self._nid(NODE_WORK, influenced)
            for src in sources:
                snode = self._nid(NODE_WORK, src)
                self._add_edge(inode, REL_INFLUENCED_BY, snode)

        # Kingdom → Work edges
        for kingdom, works in KINGDOM_WORKS_MAP.items():
            knode = self._add_node(NODE_KINGDOM, kingdom)
            for w in works:
                wnode = self._nid(NODE_WORK, w)
                if self.G.has_node(wnode):
                    self._add_edge(wnode, REL_PART_OF, knode)

    # ── Stage 3: Thinai nodes ─────────────────────────────────────────────────

    def _build_thinai_nodes(self):
        logger.info("Building Thinai landscape + Emotion + Location nodes...")
        for thinai_name, meta in THINAI_MAP.items():
            cap = thinai_name.capitalize()
            tnode = self._add_node(NODE_THINAI, cap,
                                   emotion=meta["emotion"],
                                   location=meta["location"],
                                   season=meta["season"])

            # Emotion node
            em_node = self._add_node(NODE_EMOTION, meta["emotion"])
            self._add_edge(tnode, REL_HAS_MEANING, em_node)

            # Location node
            loc_node = self._add_node(NODE_LOCATION, meta["location"])
            self._add_edge(tnode, REL_PART_OF, loc_node)

            # Link to Tinai concept
            tinai_concept = self._nid(NODE_CONCEPT, "Tinai")
            if self.G.has_node(tinai_concept):
                self._add_edge(tnode, REL_PART_OF, tinai_concept)

    # ── Stage 4: Philosophy clusters ─────────────────────────────────────────

    def _build_philosophy_nodes(self):
        logger.info("Building Philosophy cluster nodes...")
        for phil_name, members in PHILOSOPHY_MAP.items():
            pnode = self._add_node(NODE_PHILOSOPHY, phil_name)
            for member in members:
                # Try to find existing concept node
                cnode_id = self._nid(NODE_CONCEPT, member)
                tnode_id = self._nid(NODE_THINAI, member)
                target = cnode_id if self.G.has_node(cnode_id) else (
                         tnode_id if self.G.has_node(tnode_id) else None)
                if target:
                    self._add_edge(target, REL_PART_OF, pnode)

    # ── Stage 5: Deity nodes ──────────────────────────────────────────────────

    def _build_deity_nodes(self):
        logger.info("Building Deity nodes...")
        for deity_name, works_or_concepts in DEITY_MAP.items():
            dnode = self._add_node(NODE_DEITY, deity_name)
            for w in works_or_concepts:
                wnode = self._nid(NODE_WORK, w)
                cnode = self._nid(NODE_CONCEPT, w)
                if self.G.has_node(wnode):
                    self._add_edge(dnode, REL_MENTIONED_IN, wnode)
                elif self.G.has_node(cnode):
                    self._add_edge(dnode, REL_RELATED_TO, cnode)

    # ── Stage 6: Grammar Rule nodes (Tolkappiyam) ─────────────────────────────

    GRAMMAR_RULES = [
        {"name": "Eluttatikaram", "desc": "Phonology — letters and sounds"},
        {"name": "Collatikaram",  "desc": "Morphology — words and forms"},
        {"name": "Porulatikaram", "desc": "Poetics — Akam/Puram/Tinai classification"},
    ]

    def _build_grammar_nodes(self):
        logger.info("Building Grammar Rule nodes for Tolkappiyam...")
        tol_node = self._nid(NODE_WORK, "Tolkappiyam")
        for rule in self.GRAMMAR_RULES:
            gnode = self._add_node(NODE_GRAMMAR, rule["name"],
                                   description=rule["desc"])
            if self.G.has_node(tol_node):
                self._add_edge(gnode, REL_DEFINED_IN, tol_node)

    # ── Stage 7: Corpus verse MENTIONED_IN edges ──────────────────────────────

    def _build_corpus_edges(self):
        if not os.path.exists(self.corpus_path):
            logger.warning(f"Corpus not found: {self.corpus_path} — skipping verse edges.")
            return
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        logger.info(f"Adding MENTIONED_IN edges from {len(records)} corpus verses...")
        for r in records:
            work = r.get("work_name", "")
            wnode = self._nid(NODE_WORK, work) if work else None
            for c in r.get("iks_concepts", []):
                c_name = c.get("name", "") if isinstance(c, dict) else str(c)
                cnode = self._nid(NODE_CONCEPT, c_name)
                if not self.G.has_node(cnode):
                    cnode = self._nid(NODE_THINAI, c_name)
                if self.G.has_node(cnode) and wnode and self.G.has_node(wnode):
                    self._add_edge(cnode, REL_MENTIONED_IN, wnode,
                                   verse_id=r.get("id", ""),
                                   confidence=c.get("confidence", 0.9) if isinstance(c, dict) else 0.9)

    # ── Main build entry point ────────────────────────────────────────────────

    def build(self) -> nx.DiGraph:
        logger.info("=== ChronoIKS Knowledge Graph Builder v1 ===")
        kb = self._load_kb()
        self._build_concept_nodes(kb)
        self._build_work_nodes()
        self._build_thinai_nodes()
        self._build_philosophy_nodes()
        self._build_deity_nodes()
        self._build_grammar_nodes()
        self._build_corpus_edges()
        logger.info(f"Graph built: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges.")
        self._save()
        return self.G

    def _save(self):
        # GraphML (Neo4j-importable)
        nx.write_graphml(self.G, self.GRAPH_PATH)
        logger.info(f"Saved GraphML: {self.GRAPH_PATH}")

        # JSON (portable)
        data = {
            "metadata": {
                "created": datetime.utcnow().isoformat() + "Z",
                "nodes":   self.G.number_of_nodes(),
                "edges":   self.G.number_of_edges(),
                "version": "v1.0.0",
            },
            "nodes": [{"id": n, **self.G.nodes[n]} for n in self.G.nodes()],
            "edges": [{"source": u, "target": v, **self.G.edges[u, v]}
                      for u, v in self.G.edges()],
        }
        with open(self.JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON:    {self.JSON_PATH}")

    def load(self) -> Optional[nx.DiGraph]:
        if not os.path.exists(self.GRAPH_PATH):
            return None
        self.G = nx.read_graphml(self.GRAPH_PATH)
        logger.info(f"Loaded graph: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges.")
        return self.G
