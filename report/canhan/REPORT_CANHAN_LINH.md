# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Khánh Linh
**Nhóm:** A3
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine đo góc giữa hai vector embedding thay vì độ dài của chúng: giá trị càng gần 1 nghĩa là hai vector càng "cùng hướng" trong không gian embedding, tức hai đoạn văn bản mang ý nghĩa/ngữ cảnh gần nhau — dù cách diễn đạt (từ ngữ, độ dài câu) có thể khác nhau. Giá trị gần 0 nghĩa là hai vector gần như vuông góc, tức nội dung không liên quan; giá trị âm (hiếm với embedding text) nghĩa là ý nghĩa trái ngược.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Sinh viên đăng ký học phần trong cổng học vụ theo lịch của từng học kỳ."
- Câu B: "Khi gặp lỗi trùng lịch, sinh viên điều chỉnh lớp học phần trước thời hạn điều chỉnh được công bố."
- Tại sao tương đồng: Cả hai câu đều lấy từ cùng tài liệu `course-registration.md`, cùng nói về quy trình đăng ký/điều chỉnh học phần, dùng chung các thực thể (sinh viên, học phần, lịch) nên embedding của chúng nằm gần nhau trong không gian vector.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Sinh viên đăng ký học phần trong cổng học vụ theo lịch của từng học kỳ."
- Câu B: "Thư viện cung cấp mượn tài liệu và không gian học tập cho sinh viên, giảng viên và nhân viên."
- Tại sao khác: Hai câu thuộc hai chủ đề khác nhau (đăng ký học phần vs. dịch vụ thư viện) — dù cùng nhắc đến "sinh viên", phần lớn ngữ nghĩa còn lại (đăng ký/lịch học phần vs. mượn tài liệu/không gian học tập) không liên quan, nên vector của chúng lệch hướng nhiều hơn.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity chuẩn hoá theo độ dài vector (chỉ quan tâm hướng), nên không bị ảnh hưởng bởi việc một đoạn văn dài hơn thường tạo ra vector có độ lớn (magnitude) khác — hai đoạn văn nói cùng một ý nhưng độ dài khác nhau vẫn cho điểm tương tự cao. Khoảng cách Euclid lại nhạy với độ lớn vector nên dễ đánh giá sai mức độ liên quan khi so sánh các đoạn văn bản có độ dài chênh lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> **Trình bày phép tính:** Theo cách `FixedSizeChunker` trong `src/chunking.py` cắt chunk, mỗi chunk mới bắt đầu cách chunk trước `step = chunk_size - overlap` ký tự.
>
> - step = 500 − 50 = 450
> - Số chunk = ceil((L − chunk_size) / step) + 1 = ceil((10000 − 500) / 450) + 1 = ceil(9500 / 450) + 1 = ceil(21.11) + 1 = 22 + 1
>
> **Đáp án:** 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Với overlap = 100 thì step = 500 − 100 = 400, số chunk = ceil(9500 / 400) + 1 = 24 + 1 = **25 chunks** (tăng thêm 2 chunk so với overlap = 50). Overlap lớn hơn giúp các câu/ý nằm vắt ngang ranh giới chunk vẫn xuất hiện trọn vẹn trong ít nhất một chunk, giảm nguy cơ mất ngữ cảnh khi truy xuất — đánh đổi bằng việc lưu trữ và tính toán nhiều chunk (dữ liệu trùng lặp) hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng một regex duy nhất `re.split(r"(?<=[.!?])\s+", text.strip())`: lookbehind `(?<=[.!?])` giữ dấu câu (`.`, `!`, `?`) ở lại cuối câu trước rồi tách tại khoảng trắng/`\n` ngay sau đó, nên bao trùm luôn cả ba mẫu `". "`, `"! "`, `"? "` lẫn `".\n"` mà đề bài yêu cầu, không cần viết riêng từng trường hợp. Sau khi tách, lọc bỏ các phần tử rỗng/toàn khoảng trắng rồi gom từng nhóm `max_sentences_per_chunk` câu liên tiếp bằng slicing theo bước nhảy, nối lại bằng dấu cách. Edge case: text rỗng trả về `[]` ngay từ đầu; câu cuối cùng dù không có dấu kết thúc vẫn được giữ nguyên vì regex chỉ tách sau dấu câu, không bắt buộc phải có.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> `chunk()` chỉ gọi `_split(text, self.separators)`. Base case của đệ quy: nếu đoạn text hiện tại đã `<= chunk_size` thì trả về nguyên `[current_text]`; nếu đã thử hết separator (`remaining_separators` rỗng) thì cắt cứng theo `chunk_size` làm phương án cuối cùng. Với separator ưu tiên cao nhất còn lại, tách text thành các phần — phần nào vẫn còn quá dài thì gọi đệ quy `_split` tiếp với separator kế tiếp trong danh sách; sau đó gộp các phần nhỏ liền kề lại với nhau bằng một buffer cho tới khi gần chạm `chunk_size`, tránh sinh ra quá nhiều chunk vụn nhỏ hơn nhiều so với `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> `add_documents` gọi `_make_record` cho từng `Document`: copy `metadata`, gán mặc định `doc_id = doc.id` nếu chưa có, nhúng `content` qua `embedding_fn`, rồi append dict `{id, content, metadata, embedding}` vào `self._store` (list in-memory) — hoặc gọi `collection.add(...)` nếu phát hiện ChromaDB khả dụng. `search` nhúng câu query, dùng `_search_records` để tính độ tương tự bằng **tích vô hướng (dot product)** giữa vector query và từng vector đã lưu (không chuẩn hóa lại vì các embedding đầu vào đã được normalize sẵn), sắp xếp giảm dần theo `score` rồi cắt lấy `top_k` phần tử đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> `search_with_filter` lọc **trước, tìm kiếm sau**: duyệt `self._store`, chỉ giữ lại record có `metadata` khớp toàn bộ cặp key-value trong `metadata_filter` (dùng `all(...)`), rồi mới chạy `_search_records` trên tập con đã lọc để tính điểm và xếp hạng — nhờ vậy loại được nhiễu không đúng đối tượng (ví dụ khác `audience`/`department`) trước khi so sánh độ tương tự. `delete_document(doc_id)` xóa toàn bộ chunk của một tài liệu bằng cách lọc lại `self._store`, chỉ giữ record có `metadata["doc_id"] != doc_id`; trả `True` nếu kích thước store giảm sau khi lọc, `False` nếu không có chunk nào khớp `doc_id`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> `answer()` gọi `self.store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất, nối `content` của chúng lại bằng `"\n\n"` thành khối `context`. Prompt dựng theo mẫu cố định: chỉ dẫn LLM trả lời dựa trên context được cung cấp (và nói rõ nếu context không đủ thông tin), chèn `context` + `question` vào cuối, rồi gọi `self.llm_fn(prompt)` để sinh câu trả lời — đúng luồng RAG retrieve → augment → generate.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
========================================= test session starts ==========================================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0 -- D:\MyVin\K3-Day07-Data-Foundations\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\MyVin\K3-Day07-Data-Foundations
collected 42 items                                                                                    

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED             [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                      [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED               [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                     [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED     [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED           [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED            [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED          [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                            [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED            [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                       [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                   [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                             [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED    [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED        [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED  [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED        [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                            [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED              [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                      [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED           [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED             [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED              [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                       [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                      [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                 [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED             [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED        [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED            [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                  [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED            [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED       [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED      [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED     [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]ASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

========================================== 42 passed in 0.23s ======================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **Lưu ý:** tính bằng `MockEmbedder` (chưa cài `requirements-local.txt` tại thời điểm làm phần này) — dùng để có số liệu thật ngay, nhưng như README cảnh báo, mock sinh vector gần-ngẫu-nhiên theo chuỗi ký tự nên **không phản ánh ngữ nghĩa thật**. Sẽ chạy lại với `EMBEDDING_PROVIDER=local` và cập nhật bảng trước khi nộp chính thức.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (mock) | Đúng? |
| --- | --- | --- | --- | --- | --- |
| 1 | "Sinh viên có thể mượn tối đa 3 tài liệu từ thư viện." | "Mỗi sinh viên được mượn không quá 3 đầu sách cùng lúc." (diễn giải lại cùng ý) | cao | 0.1812 | Không — điểm gần 0, không thể hiện là "cao" |
| 2 | "Học phí được đóng hai lần mỗi năm học." | "Sinh viên nộp học phí theo từng học kỳ, hai lần trong năm." (diễn giải lại cùng ý) | cao | 0.0900 | Không — thấp hơn cả cặp 4 (dự đoán thấp) |
| 3 | "Thư viện cho mượn sách trong hai tuần." | "Sinh viên năm nhất bắt buộc ở trong ký túc xá." (khác chủ đề) | thấp | -0.0997 | Đúng theo hướng — điểm âm, thấp nhất trong 5 cặp |
| 4 | "Học bổng được duy trì nếu đạt điều kiện học lực tối thiểu." | "Sinh viên đăng ký học phần trước hạn điều chỉnh lịch học." (khác chủ đề) | thấp | 0.1016 | Không — cao hơn cả cặp 2 (dự đoán cao) |
| 5 | "One academic credit is equivalent to 50 hours of study." | "Credits are understood as subjects that have determined a specific number of academic credits for tuition calculation." (cùng từ "credit"/"academic" nhưng 2 nghĩa khác nhau — tín chỉ học thuật vs. đơn vị tính phí) | khó đoán, nghiêng cao vì trùng từ vựng | 0.1036 | Không tương ứng — không hề cao dù trùng nhiều từ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất là cặp 1 và 2 — hai câu diễn giải lại (paraphrase) cùng một ý, đáng lẽ phải có độ tương tự rất cao (gần 1.0) với một embedder thật — nhưng mock chỉ cho 0.18 và 0.09, thậm chí *thấp hơn* một cặp bị dự đoán "thấp" (cặp 4 = 0.1016). Điều này minh chứng rõ ràng cho cảnh báo trong README: `MockEmbedder` băm (hash) toàn bộ chuỗi ký tự thành vector giả-ngẫu-nhiên, hoàn toàn không "hiểu" từ vựng hay cấu trúc câu, nên hai câu paraphrase với mock trông chẳng khác gì hai câu ngẫu nhiên không liên quan. Cặp 5 (từ "credit" mang 2 nghĩa khác nhau) cũng không hề cho điểm cao dù trùng nhiều từ — vì mock nhạy với *toàn chuỗi ký tự*, không phải từ khoá riêng lẻ. Kết luận: độ tương tự cosine chỉ có ý nghĩa khi vector embedding thực sự mã hoá ngữ nghĩa (như `LocalEmbedder`/`OpenAIEmbedder`); với mock, con số này chỉ đo "sự trùng khớp ngẫu nhiên của chuỗi ký tự" chứ không phải ý nghĩa văn bản — đúng như mục đích thiết kế của nó (chỉ để unit test có tính xác định, không dùng để so sánh chiến lược retrieval).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chiến lược cá nhân: `SentenceChunker(max_sentences_per_chunk=4)` (built-in — giữ trọn câu, mỗi câu luật thường là một điều kiện hoàn chỉnh). Corpus: 7 tài liệu K3 thật (`data/k3_university/`), `EMBEDDING_PROVIDER=local`. Chạy bằng `scripts/member_strategies.py` (thành viên "Pham Khanh Linh"), chấm bằng `scripts/score_benchmark.py`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 | Định nghĩa credit theo giờ học? | `k3-academic-regulations-undergrad` — "Credits — A credit is a unit that is used to determine the amount of academic work..." | 0.7768 | Có, rank-1 → **2đ** | Đúng, đủ chi tiết (trích cả câu "50 hours of study") |
| 2 | Sinh viên đóng học phí mấy lần/năm? | `k3-financial-regulations-tariff` — "Listed tuition fees and scholarship policy — Listed tuition fee: 932,400,000 VND/y..." | 0.6703 | Có, rank-2 → **1đ** | Trích số tiền học phí, không nêu tần suất — sai |
| 3 | Sinh viên đại học mượn tối đa bao nhiêu tài liệu, trong bao lâu? | `k3-library-borrow-request-undergrad` — dạng bảng "Policy / Borrowed items / Borrowing time / Renewal / Undergraduate student / 3 / 2 weeks..." | 0.6610 | **Không** trong top-3 → **0đ** (chunk dạng bảng không khớp cụm từ chấm điểm dù đúng nội dung) | Trích được nội dung bảng nhưng không tính relevant theo cách chấm |
| 4 | Sinh viên năm nhất có bắt buộc ở ký túc xá không? | `k3-residential-life-guideline` — "III. General Policy Principles — 1. Community Principles — All first-year students are required..." | 0.7288 | Có, rank-1 → **2đ** | Đúng, đủ chi tiết |
| 5 | Sinh viên cần làm gì để giữ học bổng suốt thời gian học? | `k3-financial-regulations-tariff` — "The Talent Scholarship is applicable for the entire duration..." | 0.6540 | Có, rank-2 → **1đ** | Lệch sang "Talent Scholarship" khác, không phải điều kiện duy trì chung |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 — Tổng điểm theo `docs/SCORING.md`: **6/10** (Q1=2, Q2=1, Q3=0, Q4=2, Q5=1).

Câu 3 là điểm yếu cấu trúc thật của `SentenceChunker` trên tài liệu có bảng: khi văn bản nguồn dùng định dạng bảng (Policy/Borrowed items/...), tách theo dấu câu `.!?` không hoạt động tốt vì bảng không có nhiều dấu câu, nội dung dồn vào 1 chunk "phẳng" khó khớp cách chấm bằng cụm từ chính xác — dù thông tin vẫn đúng và đủ.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Chiến lược `RecursiveChunker` (built-in) của Lê Thị Yến Nhi đạt điểm cao hơn hẳn (8/10 so với 6/10 của tôi) dù cũng không cần viết code tùy chỉnh — cho thấy `SentenceChunker` gom cố định N câu/chunk không tối ưu bằng cách tách theo ranh giới đoạn văn tự nhiên (`\n\n`/`\n`) của Recursive, nhất là với văn bản có bảng. Học được là chọn built-in "đơn giản" không đồng nghĩa kém — quan trọng là chunker có khớp với *cấu trúc thật* của nguồn hay không.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                    |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                   |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                   |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                    |
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 *(điểm thật, xem Phần 5)* |
| **Tổng phần cá nhân**                      | **56 / 60**         |
