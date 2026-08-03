"""Group Phase 2 — each member's chunking strategy, run against the real K3
knowledge base with the local multilingual embedder (EMBEDDING_PROVIDER=local
semantics, called directly here rather than via env var).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import build_knowledge_base
from src import (
    FixedSizeChunker,
    KnowledgeBaseAgent,
    LocalEmbedder,
    RecursiveChunker,
    SentenceChunker,
)

DATA_DIR = "data/k3_university"


class HeadingSectionChunker:
    """Split VinUni policy text on its own heading markers: 'Article N.',
    Roman-numeral section headers ('I. PURPOSES'), and lettered top-level
    sections ('A.    FINANCIAL...'). K3-required: at least one member must
    chunk a university handbook/regulation by heading/section."""

    HEADING_PATTERN = re.compile(
        r"^(Article\s+\d+\.|[IVXLC]{1,5}\.\s+[A-Z]|[A-Z]\.\s{1,4}[A-Z]{2,})"
    )

    def chunk(self, text: str) -> list[str]:
        lines = text.split("\n")
        chunks: list[str] = []
        current: list[str] = []
        for line in lines:
            if self.HEADING_PATTERN.match(line.strip()) and current:
                piece = "\n".join(current).strip()
                if piece:
                    chunks.append(piece)
                current = [line]
            else:
                current.append(line)
        if current:
            piece = "\n".join(current).strip()
            if piece:
                chunks.append(piece)

        if len(chunks) <= 1:
            return RecursiveChunker(chunk_size=500).chunk(text)
        return chunks


class ClauseChunker:
    """Split on numbered clause markers like '1.1', '2.3' — the fine-grained
    rule numbering used in the financial/library regulations. Falls back to
    RecursiveChunker for documents that have no such clauses (e.g. the
    scholarship page)."""

    CLAUSE_PATTERN = re.compile(r"^\d+\.\d+(\.\d+)?\s")

    def chunk(self, text: str) -> list[str]:
        lines = text.split("\n")
        chunks: list[str] = []
        current: list[str] = []
        for line in lines:
            if self.CLAUSE_PATTERN.match(line.strip()) and current:
                piece = "\n".join(current).strip()
                if piece:
                    chunks.append(piece)
                current = [line]
            else:
                current.append(line)
        if current:
            piece = "\n".join(current).strip()
            if piece:
                chunks.append(piece)

        if len(chunks) <= 1:
            return RecursiveChunker(chunk_size=500).chunk(text)
        return chunks


MEMBERS = {
    "Le Thi Yen Nhi": ("RecursiveChunker (built-in, chunk_size=400)", RecursiveChunker(chunk_size=400)),
    "Pham Khanh Linh": ("SentenceChunker (built-in, max_sentences_per_chunk=4)", SentenceChunker(max_sentences_per_chunk=4)),
    "Nguyen Thanh Phuc": ("FixedSizeChunker (built-in, chunk_size=400, overlap=80)", FixedSizeChunker(chunk_size=400, overlap=80)),
    "Vu Huy Hoang": ("HeadingSectionChunker (custom)", HeadingSectionChunker()),
    "Nguyen Van Phong": ("ClauseChunker (custom)", ClauseChunker()),
}

QUERIES = [
    {
        "q": "What is the definition of an academic credit in terms of study hours for undergraduate students?",
        "gold": "1 credit is equivalent to 50 hours of study (contact hours, tutorials, self-managed study, experiential learning, assessments and exams).",
        "filter": None,
    },
    {
        "q": "How many times per year do students pay tuition fees?",
        "gold": "Twice a year, at the beginning of each main semester, per VinUni's annual announced schedule.",
        "filter": None,
    },
    {
        "q": "How many items can an undergraduate student borrow from the library at once, and for how long?",
        "gold": "Up to 3 items for two weeks per item; may be renewed once for one more week if not overdue and not requested by another patron.",
        "filter": {"audience": "student"},
    },
    {
        "q": "Are first-year students required to live in the VinUni dormitory?",
        "gold": "Yes, all first-year students are required to reside in the VinUni dormitory (special accommodations may be approved case by case).",
        "filter": None,
    },
    {
        "q": "What must a student do to keep their scholarship for the whole duration of study?",
        "gold": "Meet the minimum scholarship maintenance conditions set by the university (academic performance, extracurricular development, per the Detailed Regulations); the scholarship then applies for the entire study duration.",
        "filter": None,
    },
]


def extractive_llm(prompt: str) -> str:
    """Stand-in for a real LLM call (no paid API key wired up for this
    exercise) — extractive: returns sentences from the retrieved context up
    to a ~400-char budget, so grounding stays traceable to the corpus.

    Newlines are flattened to spaces before sentence-splitting so a bare
    heading line ("Article 11. Study Load\n\nThe study load is...") doesn't
    get treated as a standalone blank-line "paragraph" and truncate the
    answer to just the heading — the original bug found during Phase 2
    benchmarking (see REPORT_NHOM.md Phan 4). The sentence count was also
    bumped from a hard 2 up to a character budget: with only 2 sentences,
    answers correctly grounded in the right (rank-1) chunk still scored as
    "incomplete" whenever the fact-bearing sentence was 3rd/4th in the
    chunk — an artifact of the stand-in being stingier than a real LLM
    would be, not a retrieval problem."""
    context = prompt.split("Context:\n", 1)[-1].split("\n\nQuestion:")[0].strip()
    flat = re.sub(r"\s+", " ", context).strip()
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", flat) if len(s) > 3]

    picked: list[str] = []
    budget = 0
    for sentence in sentences:
        if picked and budget + len(sentence) > 400:
            break
        picked.append(sentence)
        budget += len(sentence)
    return " ".join(picked).strip()


def main() -> None:
    embedding_fn = LocalEmbedder()

    for member, (label, chunker) in MEMBERS.items():
        store = build_knowledge_base(DATA_DIR, embedding_fn, chunker=chunker, collection_name=member)
        agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)

        print(f"\n{'=' * 90}\n{member} -- {label} -- collection size: {store.get_collection_size()} chunks\n{'=' * 90}")

        for i, item in enumerate(QUERIES, start=1):
            if item["filter"]:
                results = store.search_with_filter(item["q"], top_k=3, metadata_filter=item["filter"])
            else:
                results = store.search(item["q"], top_k=3)

            answer = agent.answer(item["q"], top_k=3) if not item["filter"] else extractive_llm(
                "Context:\n" + "\n\n".join(r["content"] for r in results) + f"\n\nQuestion: {item['q']}\nAnswer:"
            )

            print(f"\nQ{i}: {item['q']}")
            if item["filter"]:
                print(f"  (metadata_filter={item['filter']})")
            for rank, r in enumerate(results, start=1):
                doc_id = r["metadata"].get("doc_id", "?")
                snippet = r["content"][:100].replace("\n", " ")
                print(f"  top-{rank} [{doc_id}] score={r['score']:.4f} :: {snippet}...")
            print(f"  agent answer: {answer[:200]}")


if __name__ == "__main__":
    main()
