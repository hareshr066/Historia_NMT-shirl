import argparse
import sys
import os
import json

# Force UTF-8 output on Windows (avoids cp1252 encode errors in terminal)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Prevent duplicate OpenMP library initialization deadlock
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from backend.core.corpus_builder import CorpusBuilder

BANNER = """
==============================================================
  ChronoIKS Corpus v2  --  Research Dataset Builder
  Classical Tamil <-> English | IKS-Aware | QLoRA-Ready
==============================================================
"""

SEPARATOR_WIDE  = "=" * 60
SEPARATOR_MED   = "-" * 45
SEPARATOR_SLIM  = "-" * 35


def print_banner():
    print(BANNER)


def handle_dataset_cmd(args):
    builder = CorpusBuilder()

    # ─── BUILD ────────────────────────────────────────────────
    if args.dataset_action == "build":
        print_banner()
        print("  [*] Initialising ChronoIKS Corpus v2 pipeline...")
        print(SEPARATOR_WIDE)
        success = builder.build_corpus()
        if success:
            print()
            print("  [+] Build completed successfully!")
            print()
            print("  Output files:")
            print("    ├── datasets/raw/              – Raw source JSON files (14 works)")
            print("    ├── datasets/processed/        – Validated + annotated corpus")
            print("    ├── datasets/clean/            – Clean corpus (no system fields)")
            print("    ├── datasets/augmented/        – IKS-tagged augmented corpus")
            print("    ├── datasets/train/            – 80% train split (JSONL)")
            print("    ├── datasets/validation/       – 10% validation split (JSONL)")
            print("    ├── datasets/test/             – 10% test split (JSONL)")
            print("    ├── datasets/metadata/         – dataset_version.json")
            print("    ├── results/dataset_report.md  – Markdown quality report")
            print("    ├── results/dataset_statistics.json")
            print("    └── results/dataset_quality.csv")
        else:
            print()
            print("  [-] Dataset build FAILED.")
            print("      Check 'results/dataset_build.log' for details.")
            sys.exit(1)

    # ─── VALIDATE ─────────────────────────────────────────────
    elif args.dataset_action == "validate":
        print_banner()
        print("  [*] Running corpus validation checks...")
        print(SEPARATOR_WIDE)
        valid = builder.validate_corpus()
        if valid:
            print()
            print("  [+] All checks PASSED. Dataset is research-grade and training-ready.")
        else:
            print()
            print("  [-] Validation FAILED. Review warnings above and rebuild if necessary.")
            sys.exit(1)

    # ─── STATS ────────────────────────────────────────────────
    elif args.dataset_action == "stats":
        stats = builder.get_stats()
        if not stats:
            print("  [-] No statistics found. Run  python chronoiks.py dataset build  first.")
            sys.exit(1)

        print_banner()

        # Load version info if available
        ver_path = "dataset_version.json"
        ver_info = {}
        if os.path.exists(ver_path):
            with open(ver_path, "r", encoding="utf-8") as f:
                ver_info = json.load(f)

        print(f"  Dataset Version    : {ver_info.get('Dataset Version', 'v2.0.0')}")
        print(f"  Build Timestamp    : {stats['build_timestamp']}")
        print(f"  Git Hash           : {ver_info.get('Git Hash', 'unknown')[:12]}")
        print(f"  Dataset Hash       : {ver_info.get('Dataset Hash', 'unknown')[:12]}...")
        print()

        # Core counts
        print(f"  {'Total Samples':<28}: {stats['total_samples']}")
        print(f"  {'Train / Val / Test':<28}: {stats['train_samples']} / {stats['val_samples']} / {stats['test_samples']}")
        print(f"  {'Duplicates Removed':<28}: {stats.get('duplicates_removed', 0)}")
        print(f"  {'Unique IKS Concepts':<28}: {stats['unique_concepts_count']}")
        print(f"  {'Unique Authors':<28}: {stats.get('unique_authors_count', 'N/A')}")
        print(f"  {'Vocabulary Size':<28}: {ver_info.get('Vocabulary Size', stats.get('vocabulary_statistics', {}).get('total_vocabulary_words', 'N/A'))}")
        print(f"  {'Avg Tamil Length':<28}: {stats['average_tamil_length']} chars")
        print(f"  {'Avg English Length':<28}: {stats['average_english_length']} chars")
        print(f"  {'Concept Coverage':<28}: {stats.get('concept_annotation_coverage_pct', 'N/A')}%")
        print()

        # Distribution by work
        print(f"  Distribution by Classical Work:")
        print("  " + SEPARATOR_WIDE)
        print(f"  {'Work Name':<25} | {'Count':<8} | {'Percentage':>10}")
        print("  " + SEPARATOR_WIDE)
        for w, c in sorted(stats["work_distribution"].items(), key=lambda x: x[1], reverse=True):
            pct = (c / stats["total_samples"]) * 100
            print(f"  {w:<25} | {c:<8} | {pct:>9.1f}%")
        print("  " + SEPARATOR_WIDE)
        print()

        # Quality distribution
        q_dist = stats.get("quality_distribution", {})
        if q_dist:
            print(f"  Quality Score Distribution:")
            print("  " + SEPARATOR_MED)
            print(f"  {'Range':<15} | {'Count':<8} | {'Percentage':>10}")
            print("  " + SEPARATOR_MED)
            for q_range, q_count in q_dist.items():
                pct = (q_count / stats["total_samples"]) * 100
                print(f"  {q_range:<15} | {q_count:<8} | {pct:>9.1f}%")
            print("  " + SEPARATOR_MED)
            print()

        # Top concepts
        print(f"  Top Annotated IKS Concepts:")
        print("  " + SEPARATOR_MED)
        print(f"  {'Concept':<20} | {'Occurrences':<10}")
        print("  " + SEPARATOR_MED)
        for cp, oc in sorted(stats["concept_distribution"].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {cp:<20} | {oc:<10}")
        print("  " + SEPARATOR_MED)

    # ─── EXPORT ───────────────────────────────────────────────
    elif args.dataset_action == "export":
        print_banner()
        formats = [args.format] if args.format else ["csv", "jsonl", "parquet", "hf"]
        print(f"  [*] Exporting corpus to formats: {', '.join(f.upper() for f in formats)}")
        print(SEPARATOR_WIDE)
        all_ok = True
        for fmt in formats:
            success = builder.export_corpus(fmt)
            if success:
                print(f"  [+] {fmt.upper():<10} → datasets/exports/")
            else:
                print(f"  [-] {fmt.upper():<10} FAILED")
                all_ok = False
        print()
        if all_ok:
            print("  [+] All exports completed. Check 'datasets/exports/'.")
        else:
            print("  [-] Some exports failed. See log for details.")
            sys.exit(1)

    # ─── VERSION ──────────────────────────────────────────────
    elif args.dataset_action == "version":
        ver_path = "dataset_version.json"
        if not os.path.exists(ver_path):
            print("  [-] dataset_version.json not found. Run  python chronoiks.py dataset build  first.")
            sys.exit(1)

        with open(ver_path, "r", encoding="utf-8") as f:
            ver_info = json.load(f)

        print_banner()
        print("  ChronoIKS Corpus v2 — Version Information")
        print(SEPARATOR_WIDE)
        for key, val in ver_info.items():
            if key == "Dataset Hash":
                print(f"  {key:<28}: {str(val)[:32]}...")
            else:
                print(f"  {key:<28}: {val}")
        print(SEPARATOR_WIDE)

    else:
        print(f"  [-] Unknown dataset action: {args.dataset_action}")
        sys.exit(1)


# ╔══════════════════════════════════════════════════════════╗
# ║              GRAPH COMMAND HANDLER                       ║
# ╚══════════════════════════════════════════════════════════╝

def handle_graph_cmd(args):
    import json
    from backend.graph.loader import load_or_build
    from backend.graph.builder import KnowledgeGraphBuilder

    # ─── BUILD ────────────────────────────────────────────────
    if args.graph_action == "build":
        print_banner()
        print("  [*] Building ChronoIKS Knowledge Graph v1...")
        print(SEPARATOR_WIDE)
        builder = KnowledgeGraphBuilder()
        G = builder.build()
        n, e = G.number_of_nodes(), G.number_of_edges()
        print()
        print(f"  [+] Knowledge Graph built successfully!")
        print(f"      Nodes : {n}")
        print(f"      Edges : {e}")
        print()
        print("  Output files:")
        print("    ├── results/knowledge_graph.graphml")
        print("    └── results/knowledge_graph.json")

    # ─── STATS ────────────────────────────────────────────────
    elif args.graph_action == "stats":
        import networkx as nx
        stats_path = "results/graph_statistics.json"
        G = load_or_build()
        n = G.number_of_nodes()
        e = G.number_of_edges()
        density   = round(nx.density(G), 6)
        uG        = G.to_undirected()
        components = nx.number_connected_components(uG)
        avg_deg   = round(sum(d for _, d in G.degree()) / n, 2) if n else 0

        # Most connected nodes
        top_nodes = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10]
        top_list  = [(G.nodes[n].get("name", n), deg) for n, deg in top_nodes]

        # Node type distribution
        type_dist = {}
        for _, data in G.nodes(data=True):
            t = data.get("node_type", "?")
            type_dist[t] = type_dist.get(t, 0) + 1

        # Edge relationship distribution
        rel_dist = {}
        for _, _, data in G.edges(data=True):
            r = data.get("relationship", "?")
            rel_dist[r] = rel_dist.get(r, 0) + 1

        stats = {
            "nodes": n, "edges": e, "density": density,
            "connected_components": components, "avg_degree": avg_deg,
            "node_type_distribution": type_dist,
            "relationship_distribution": rel_dist,
            "most_connected": top_list,
        }
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)

        print_banner()
        print("  ChronoIKS Knowledge Graph — Statistics")
        print(SEPARATOR_WIDE)
        print(f"  {'Nodes':<30}: {n}")
        print(f"  {'Edges':<30}: {e}")
        print(f"  {'Graph Density':<30}: {density}")
        print(f"  {'Connected Components':<30}: {components}")
        print(f"  {'Average Degree':<30}: {avg_deg}")
        print()
        print("  Node Type Distribution:")
        print("  " + SEPARATOR_MED)
        for t, c in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"  {t:<22} : {c}")
        print()
        print("  Relationship Distribution:")
        print("  " + SEPARATOR_MED)
        for r, c in sorted(rel_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"  {r:<28} : {c}")
        print()
        print("  Most Connected Concepts:")
        print("  " + SEPARATOR_MED)
        for name, deg in top_list:
            print(f"  {name:<28} : degree {deg}")
        print(SEPARATOR_WIDE)
        print(f"  Saved: {stats_path}")

    # ─── SEARCH ───────────────────────────────────────────────
    elif args.graph_action == "search":
        if not args.query:
            print("  [-] Provide a search query: python chronoiks.py graph search \"Aram\"")
            sys.exit(1)
        from backend.graph.reasoner import KnowledgeGraphReasoner
        print_banner()
        print(f"  [*] Reasoning over Knowledge Graph for: '{args.query}'")
        print(SEPARATOR_WIDE)
        G = load_or_build()
        reasoner = KnowledgeGraphReasoner(G)
        report   = reasoner.reason(args.query)
        formatted = reasoner.format_report(report)
        print(formatted)
        print()
        print(SEPARATOR_WIDE)

    # ─── VISUALIZE ────────────────────────────────────────────
    elif args.graph_action == "visualize":
        from backend.graph.visualizer import KnowledgeGraphVisualizer
        print_banner()
        print("  [*] Generating Knowledge Graph visualizations...")
        print(SEPARATOR_WIDE)
        G = load_or_build()
        viz = KnowledgeGraphVisualizer(G)
        paths = viz.export_all()
        print()
        for fmt, path in paths.items():
            print(f"  [+] {fmt.upper():<10} -> {path}")
        print()
        print("  [+] Open results/knowledge_graph.html in a browser for interactive view.")

    # ─── EXPORT ───────────────────────────────────────────────
    elif args.graph_action == "export":
        print_banner()
        print("  [*] Exporting Knowledge Graph (GraphML + JSON)...")
        print(SEPARATOR_WIDE)
        builder = KnowledgeGraphBuilder()
        G = builder.load()
        if G is None:
            print("  [-] Graph not built. Run: python chronoiks.py graph build")
            sys.exit(1)
        builder.G = G
        builder._save()
        print("  [+] GraphML -> results/knowledge_graph.graphml")
        print("  [+] JSON    -> results/knowledge_graph.json")

    else:
        print(f"  [-] Unknown graph action: {args.graph_action}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="chronoiks",
        description="ChronoIKS — Classical Tamil NMT + Knowledge Graph CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Dataset Commands:
  python chronoiks.py dataset build        Build the full v2 corpus pipeline
  python chronoiks.py dataset validate     Validate splits and schema
  python chronoiks.py dataset stats        Print corpus statistics
  python chronoiks.py dataset export       Export to all formats
  python chronoiks.py dataset version      Print dataset version metadata

Knowledge Graph Commands:
  python chronoiks.py graph build          Build the Knowledge Graph
  python chronoiks.py graph stats          Print graph statistics
  python chronoiks.py graph search "Aram"  Reason over a concept
  python chronoiks.py graph visualize      Generate HTML + PNG visualizations
  python chronoiks.py graph export         Export GraphML + JSON
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # dataset subcommand
    dataset_parser = subparsers.add_parser(
        "dataset",
        help="Corpus dataset build, validate, export and version commands"
    )
    dataset_parser.add_argument(
        "dataset_action",
        choices=["build", "validate", "stats", "export", "version"],
        help="Pipeline action to perform"
    )
    dataset_parser.add_argument(
        "--format",
        choices=["csv", "jsonl", "parquet", "hf"],
        default=None,
        help="Export format (default: export all formats)"
    )

    # graph subcommand
    graph_parser = subparsers.add_parser(
        "graph",
        help="Knowledge Graph build, search, stats, visualize and export commands"
    )
    graph_parser.add_argument(
        "graph_action",
        choices=["build", "stats", "search", "visualize", "export"],
        help="Graph action to perform"
    )
    graph_parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Concept to search/reason over (required for 'search' action)"
    )

    args = parser.parse_args()

    if args.command == "dataset":
        handle_dataset_cmd(args)
    elif args.command == "graph":
        handle_graph_cmd(args)


if __name__ == "__main__":
    main()
