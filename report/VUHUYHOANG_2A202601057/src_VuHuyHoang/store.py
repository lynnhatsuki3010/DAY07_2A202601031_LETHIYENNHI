from __future__ import annotations

from typing import Any, Callable
import uuid 

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document

class EmbeddingStore:
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

        try:
            import chromadb
            client = chromadb.Client()
            try:
                client.delete_collection(name=self._collection_name)
            except Exception:
                pass
                
            self._collection = client.create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        text = getattr(doc, "text", getattr(doc, "content", ""))
        metadata = getattr(doc, "metadata", {})
        
        doc_id = getattr(doc, "id", None)
        if not doc_id:
            doc_id = str(uuid.uuid4())

        embedding = self._embedding_fn(text)

        return {
            "id": str(doc_id),
            "text": text,
            "metadata": metadata,
            "embedding": embedding
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        scored_records = []

        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored_records.append((score, record))

        scored_records.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, record in scored_records[:top_k]:
            results.append({
                "id": record["id"],
                "content": record["text"],
                "metadata": record["metadata"],
                "score": score
            })
        return results

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma and self._collection is not None:
            # FIX: Tạo ID ngẫu nhiên cho ChromaDB để không bị lỗi trùng ID,
            # giữ ID gốc của người dùng vào metadata để tìm kiếm và trả về đúng yêu cầu.
            ids = []
            for r in records:
                if "doc_id" not in r["metadata"]:
                    r["metadata"]["doc_id"] = r["id"]
                ids.append(str(uuid.uuid4()))

            documents = [r["text"] for r in records]
            embeddings = [r["embedding"] for r in records]
            metadatas = [r["metadata"] if r["metadata"] else None for r in records]

            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            formatted_results = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    dist = results["distances"][0][i] if results.get("distances") else 0.0
                    meta = results["metadatas"][0][i] or {}
                    # Khôi phục lại ID gốc từ metadata
                    orig_id = meta.get("doc_id", results["ids"][0][i])
                    
                    formatted_results.append({
                        "id": orig_id,
                        "content": results["documents"][0][i],
                        "metadata": meta,
                        "score": -dist 
                    })
            
            formatted_results.sort(key=lambda x: x["score"], reverse=True)
            return formatted_results
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        in_memory_filter = metadata_filter or {}

        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            where_clause = metadata_filter if metadata_filter else None
            
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            formatted_results = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    dist = results["distances"][0][i] if results.get("distances") else 0.0
                    meta = results["metadatas"][0][i] or {}
                    orig_id = meta.get("doc_id", results["ids"][0][i])

                    formatted_results.append({
                        "id": orig_id,
                        "content": results["documents"][0][i],
                        "metadata": meta,
                        "score": -dist
                    })
            formatted_results.sort(key=lambda x: x["score"], reverse=True)
            return formatted_results
        else:
            filtered_records = []
            for record in self._store:
                match = True
                record_meta = record.get("metadata", {})
                for k, v in in_memory_filter.items():
                    if record_meta.get(k) != v:
                        match = False
                        break
                if match:
                    filtered_records.append(record)

            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        if self._use_chroma and self._collection is not None:
            initial_count = self._collection.count()
            try:
                self._collection.delete(ids=[doc_id])
            except Exception:
                pass
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass
            return self._collection.count() < initial_count
        else:
            initial_len = len(self._store)
            self._store = [
                record for record in self._store
                if record["id"] != doc_id and record.get("metadata", {}).get("doc_id") != doc_id
            ]
            return len(self._store) < initial_len