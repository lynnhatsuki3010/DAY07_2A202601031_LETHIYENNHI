from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)

        context_parts = [
            result["content"] for result in results if result.get("content")
        ]

        context = "\n\n".join(context_parts)

        prompt = f"""Bạn là trợ lý trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.

                Ngữ cảnh:
                    {context}

                Câu hỏi:
                    {question}

                Hãy trả lời dựa trên thông tin trong ngữ cảnh. Nếu ngữ cảnh không đủ thông tin, hãy nói rõ rằng không tìm thấy thông tin phù hợp.
                """

        return self.llm_fn(prompt)
