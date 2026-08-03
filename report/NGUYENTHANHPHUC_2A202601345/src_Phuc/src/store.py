from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # [DONE]: initialize chromadb client + collection
            client = chromadb.Client()
            self._collection = client.get_or_create_collection(
                name=self._collection_name
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # [DONE]: build a normalized stored record for one document
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)

        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        # [DONE]: run in-memory similarity search over provided records
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        scored_records = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])

            result = dict(record)
            result["score"] = score
            scored_records.append(result)

        scored_records.sort(key=lambda record: record["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if not self._use_chroma:
            self._store.extend(records)
            return

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for record in records:
            ids.append(f"{record['id']}_{self._next_index}")
            self._next_index += 1
            documents.append(record["content"])
            embeddings.append(record["embedding"])
            metadatas.append(record["metadata"] or {"doc_id": record["id"]})

        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0:
            return []

        if not self._use_chroma:
            return self._search_records(query, self._store, top_k)

        result = self._collection.query(
            query_embeddings=[self._embedding_fn(query)],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        return self._chroma_results(result)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if top_k <= 0:
            return []

        if not metadata_filter:
            return self.search(query, top_k)

        if not self._use_chroma:
            filtered = [
                record
                for record in self._store
                if all(
                    record["metadata"].get(key) == value
                    for key, value in metadata_filter.items()
                )
            ]
            return self._search_records(query, filtered, top_k)

        result = self._collection.query(
            query_embeddings=[self._embedding_fn(query)],
            n_results=top_k,
            where=metadata_filter,
            include=["documents", "metadatas", "distances"],
        )
        return self._chroma_results(result)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if not self._use_chroma:
            original_size = len(self._store)
            self._store = [
                record
                for record in self._store
                if record["metadata"].get("doc_id") != doc_id
            ]
            return len(self._store) < original_size

        existing = self._collection.get(where={"doc_id": doc_id})
        ids = existing.get("ids", [])
        if not ids:
            return False
        self._collection.delete(ids=ids)
        return True

    @staticmethod
    def _chroma_results(result: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert Chroma's nested query response to this store's result shape."""
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        results = []
        for index, content in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 0.0
            results.append(
                {
                    "id": metadata.get("doc_id", str(index)),
                    "content": content,
                    "metadata": metadata,
                    # Chroma returns distance; higher score remains better.
                    "score": 1.0 - float(distance),
                }
            )
        return results
