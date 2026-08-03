"""Interactive live demo for class presentation.

Loads the real K3 knowledge base (RecursiveChunker + LocalEmbedder) once,
then lets you type any question live and see top-3 retrieved chunks + the
agent's answer — for handling audience Q&A on the spot instead of only
showing pre-baked benchmark results.

Run:
    python scripts/live_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import build_knowledge_base
from src import KnowledgeBaseAgent, LocalEmbedder, RecursiveChunker
from scripts.member_strategies import extractive_llm

DATA_DIR = "data/k3_university"


def main() -> None:
    print("Loading LocalEmbedder + building knowledge base (RecursiveChunker, chunk_size=400)...")
    embedding_fn = LocalEmbedder()
    store = build_knowledge_base(DATA_DIR, embedding_fn, chunker=RecursiveChunker(chunk_size=400))
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
    print(f"Ready — {store.get_collection_size()} chunks loaded from {DATA_DIR}.\n")
    print("Type a question (English works best; local embedder is multilingual so Vietnamese also works).")
    print("Type 'audience:student <question>' to demo metadata_filter. Ctrl+C to quit.\n")

    while True:
        try:
            question = input("Q> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not question:
            continue

        if question.lower().startswith("audience:student "):
            real_q = question[len("audience:student "):].strip()
            results = store.search_with_filter(real_q, top_k=3, metadata_filter={"audience": "student"})
            context = "\n\n".join(r["content"] for r in results)
            answer = extractive_llm(f"Context:\n{context}\n\nQuestion: {real_q}\nAnswer:")
        else:
            results = store.search(question, top_k=3)
            answer = agent.answer(question, top_k=3)

        print()
        for rank, r in enumerate(results, start=1):
            doc_id = r["metadata"].get("doc_id", "?")
            audience = r["metadata"].get("audience", "?")
            snippet = r["content"][:120].replace("\n", " ")
            print(f"  top-{rank} [{doc_id} | audience={audience}] score={r['score']:.4f} :: {snippet}...")
        print(f"\n  ANSWER: {answer}\n")


if __name__ == "__main__":
    main()
