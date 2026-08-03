"""Group Phase 2 — baseline: run ChunkingStrategyComparator on 2-3 real K3 docs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import parse_front_matter
from src import ChunkingStrategyComparator

DOCS = [
    "data/k3_university/k3-academic-regulations-undergrad.md",
    "data/k3_university/k3-library-access-services-policy.md",
    "data/k3_university/k3-residential-life-guideline.md",
]

CHUNK_SIZE = 500

comparator = ChunkingStrategyComparator()

for path in DOCS:
    text = Path(path).read_text(encoding="utf-8")
    _, content = parse_front_matter(text)
    result = comparator.compare(content, chunk_size=CHUNK_SIZE)

    print(f"\n=== {Path(path).name} ({len(content)} chars) ===")
    print(f"{'strategy':<14}{'count':>8}{'avg_length':>14}")
    for strategy_name in ("fixed_size", "by_sentences", "recursive"):
        stats = result[strategy_name]
        print(f"{strategy_name:<14}{stats['count']:>8}{stats['avg_length']:>14.1f}")
