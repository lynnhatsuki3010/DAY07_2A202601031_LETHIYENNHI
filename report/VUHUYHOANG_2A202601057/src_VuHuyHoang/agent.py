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
        # Lưu lại store (cơ sở dữ liệu vector) và llm_fn (hàm gọi mô hình AI)
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Lấy ra top-k đoạn văn bản liên quan nhất từ EmbeddingStore
        retrieved_records = self.store.search(question, top_k=top_k)
        
        # Trích xuất nội dung text từ các bản ghi tìm được
        # (Theo cấu trúc dictionary ở bài trước, text được lưu trong key "text")
        context_chunks = [record.get("text", "") for record in retrieved_records]
        
        # Ghép các đoạn text lại với nhau, cách nhau bởi 2 dấu xuống dòng
        context_string = "\n\n".join(context_chunks)

        # 2. Xây dựng câu lệnh (prompt) chứa ngữ cảnh và câu hỏi
        prompt = (
            "Dựa vào phần thông tin ngữ cảnh dưới đây, hãy trả lời câu hỏi.\n"
            "Nếu thông tin không có trong ngữ cảnh, hãy nói rằng bạn không biết.\n\n"
            "--- NGỮ CẢNH ---\n"
            f"{context_string}\n"
            "-----------------\n\n"
            f"Câu hỏi: {question}\n\n"
            "Trả lời:"
        )

        # 3. Gọi LLM để sinh ra câu trả lời dựa trên prompt vừa tạo
        response = self.llm_fn(prompt)
        
        return response