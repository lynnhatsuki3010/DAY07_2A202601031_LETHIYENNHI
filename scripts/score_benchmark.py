"""Score each member's strategy against the 5 benchmark queries using
docs/SCORING.md's rule: 2 = relevant chunk in top-3 AND agent answer correct,
1 = relevant chunk in top-3 but not top-1 / answer incomplete, 0 = no relevant
chunk in top-3. Relevance is checked as an exact substring match against a
known-true phrase pulled from the source doc (not guessed), so scoring is
reproducible rather than eyeballed from truncated previews.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import build_knowledge_base
from src import KnowledgeBaseAgent, LocalEmbedder
from scripts.member_strategies import MEMBERS, QUERIES, extractive_llm, DATA_DIR

# Exact phrases that must appear in a chunk for it to count as "the relevant chunk".
RELEVANCE_PHRASE = [
    "50 hours of study",
    "twice/year",
    "borrow up to 3 items",
    "required to reside in the VinUni dormitory",
    "minimum scholarship maintenance conditions",
]


def main() -> None:
    embedding_fn = LocalEmbedder()
    all_scores: dict[str, list[int]] = {}

    for member, (label, chunker) in MEMBERS.items():
        store = build_knowledge_base(DATA_DIR, embedding_fn, chunker=chunker, collection_name=f"score_{member}")
        agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
        scores = []

        print(f"\n{'=' * 90}\n{member} -- {label}\n{'=' * 90}")

        for i, item in enumerate(QUERIES, start=1):
            phrase = RELEVANCE_PHRASE[i - 1]
            if item["filter"]:
                results = store.search_with_filter(item["q"], top_k=3, metadata_filter=item["filter"])
            else:
                results = store.search(item["q"], top_k=3)

            rank_hit = next((r + 1 for r, res in enumerate(results) if phrase.lower() in res["content"].lower()), None)
            if item["filter"]:
                context = "\n\n".join(r["content"] for r in results)
                answer = extractive_llm(f"Context:\n{context}\n\nQuestion: {item['q']}\nAnswer:")
            else:
                answer = agent.answer(item["q"], top_k=3)
            answer_ok = phrase.lower() in answer.lower()

            if rank_hit == 1 and answer_ok:
                score = 2
            elif rank_hit is not None:
                score = 1
            else:
                score = 0
            scores.append(score)

            print(f"Q{i} [{score}/2] relevant-chunk-rank={rank_hit} answer='{answer[:80]}'")

        all_scores[member] = scores
        print(f"Total: {sum(scores)}/10")

    print(f"\n{'=' * 90}\nSUMMARY\n{'=' * 90}")
    print(f"{'Member':<20}" + "".join(f"Q{i:<4}" for i in range(1, 6)) + "Total")
    for member, scores in all_scores.items():
        print(f"{member:<20}" + "".join(f"{s:<5}" for s in scores) + f"{sum(scores)}")


if __name__ == "__main__":
    main()
