# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Phong
**Nhóm:** A3
**Ngày:** 3/8/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Hai đoạn văn bản có vector embedding hướng gần nhau trong không gian nhiều chiều, tức nội dung/ngữ nghĩa tương đồng, bất kể độ dài câu khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Sinh viên đăng ký học phần qua cổng thông tin đào tạo."
- Câu B: "Việc đăng ký môn học được thực hiện trực tuyến qua hệ thống."
- Tại sao tương đồng: cùng diễn đạt một hành động (đăng ký môn học qua hệ thống online), chỉ khác cách dùng từ.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Thư viện trường mở cửa từ 7h đến 21h."
- Câu B: "Học bổng khuyến khích học tập yêu cầu điểm trung bình tối thiểu 3.2."
- Tại sao khác: hai chủ đề không liên quan (giờ mở cửa thư viện vs điều kiện học bổng), không chia sẻ khái niệm ngữ nghĩa nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine chỉ đo góc/hướng giữa hai vector, không bị ảnh hưởng bởi độ lớn (magnitude) — câu dài/ngắn khác nhau vẫn cho điểm đúng nếu nghĩa giống nhau. Euclidean đo khoảng cách tuyệt đối nên nhạy với magnitude, dễ đánh giá sai khi độ dài văn bản chênh lệch dù ngữ nghĩa gần.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Trình bày phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks — tăng từ 23 lên 25 vì bước nhảy (chunk_size - overlap) nhỏ lại nên cần nhiều chunk hơn để phủ hết văn bản. Muốn overlap lớn hơn để tránh cắt đứt câu/ý ngay ranh giới chunk, giữ ngữ cảnh liền mạch, tăng khả năng truy xuất đúng khi thông tin cần thiết nằm vắt qua ranh giới hai chunk — đánh đổi là nhiều chunk hơn, tốn chi phí embedding/lưu trữ hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng `re.split(r'(?<=[.!?])\s+', text.strip())` để tách câu ngay sau dấu `.`/`!`/`?` theo sau bởi khoảng trắng, lọc bỏ chuỗi rỗng sau split. Gom từng `max_sentences_per_chunk` câu liên tiếp bằng `" ".join(...)` rồi `strip()` thành 1 chunk. Edge case: văn bản không có dấu câu → regex không tách được, toàn bộ text thành 1 "câu" duy nhất, chunk trả về đúng 1 phần tử.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> `_split` đệ quy: thử tách `current_text` bằng separator đầu tiên trong danh sách còn lại (`\n\n → \n → ". " → " " → ""`); phần nào vẫn dài hơn `chunk_size` thì đệ quy tiếp với separator kế tiếp, phần đủ ngắn thì giữ nguyên. Base case dừng đệ quy: `len(current_text) <= chunk_size`, hoặc hết separator (`remaining_separators` rỗng) thì fallback cắt cứng theo `chunk_size` giống `FixedSizeChunker` không overlap — đảm bảo luôn trả về chunk hợp lệ kể cả khi `separators=[]`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Không cài `chromadb` nên dùng nhánh in-memory: mỗi `Document` qua `_make_record` được embed bằng `embedding_fn` rồi lưu dict `{id, content, metadata, embedding}` vào list `self._store`. `search` embed câu truy vấn, dùng `_dot(query_vec, embedding)` (dot product, vector đã chuẩn hoá nên tương đương cosine) tính điểm cho từng record, sort giảm dần theo score, trả `top_k` đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Lọc trước, tìm sau: duyệt `self._store`, chỉ giữ record có `metadata` khớp toàn bộ cặp key/value trong `metadata_filter`, rồi mới chạy similarity search (`_search_records`) trên tập đã lọc — tránh tính điểm cho record không liên quan. `delete_document` giữ lại các record có `metadata['doc_id'] != doc_id`, gán lại `self._store`, trả `True` nếu kích thước giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Gọi `store.search(question, top_k)` lấy các chunk liên quan, nối nội dung chunk bằng `"\n"` thành `context`. Dựng prompt dạng `"Context:\n{context}\n\nQuestion: {question}\nAnswer:"` — đưa ngữ cảnh vào trước câu hỏi để LLM bám vào chunk truy xuất được thay vì bịa. Gọi `llm_fn(prompt)` trả kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
PS C:\Users\THIS PC\Desktop\IT\AI THUC CHIEN\Lesson\Lesson7\lab\DAY07_2A202601241_NguyenVanPhong> pytest tests/ -v
===================================================================== test session starts ======================================================================
platform win32 -- Python 3.10.9, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\THIS PC\AppData\Local\Programs\Python\Python310\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\THIS PC\Desktop\IT\AI THUC CHIEN\Lesson\Lesson7\lab\DAY07_2A202601241_NguyenVanPhong
plugins: anyio-4.14.1, deepeval-4.1.5, langsmith-0.10.10, asyncio-1.3.0, cov-7.1.0, repeat-0.9.4, rerunfailures-16.4, xdist-3.8.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 42 items                                                                                                                                            

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                     [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                              [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                       [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                        [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                             [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                             [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                   [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                    [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                  [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                    [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                    [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                               [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                           [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                     [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                            [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                          [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                    [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                      [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                        [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                              [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                   [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                     [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                         [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                      [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                               [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                              [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                         [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                     [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                    [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                          [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                    [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                 [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                               [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                              [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                  [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                             [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                      [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                            [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                [100%]Running teardown with pytest sessionfinish...


====================================================================== 42 passed in 0.12s ======================================================================
PS C:\Users\THIS PC\Desktop\IT\AI THUC CHIEN\Lesson\Lesson7\lab\DAY07_2A202601241_NguyenVanPhong>
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                                               | Câu B                                                                     | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | "Sinh viên đăng ký học phần qua cổng thông tin đào tạo."                  | "Đăng ký môn học được thực hiện trực tuyến qua hệ thống."    | cao        | 0.0422           | Sai     |
| 2    | "Thư viện trường mở cửa từ 7h đến 21h các ngày trong tuần."              | "Học bổng khuyến khích học tập dành cho sinh viên có điểm cao." | thấp      | 0.2786           | Sai     |
| 3    | "Học phí học kỳ này phải đóng trước ngày 15 tháng 8."                    | "Sinh viên nợ học phí sẽ bị khóa tài khoản đăng ký môn."      | cao        | -0.0506          | Sai     |
| 4    | "Ký túc xá có phòng 4 người và phòng 8 người."                            | "Con mèo đang ngủ trên ghế sofa."                                     | thấp      | -0.1127          | Đúng  |
| 5    | "Sinh viên cần điểm trung bình tích lũy 3.2 trở lên để nhận học bổng." | "Học bổng khuyến khích học tập yêu cầu GPA tối thiểu 3.2."       | cao        | -0.0905          | Sai     |

> Chạy với `EMBEDDING_PROVIDER` mặc định (`_mock_embed`) — chưa cài `sentence-transformers` nên chưa bật `local`. 4/5 dự đoán sai.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất: cặp 5 — hai câu paraphrase gần như giống hệt nhau về nghĩa (cùng nói điều kiện GPA 3.2 để nhận học bổng) lại có điểm âm (-0.0905), thấp hơn cả cặp 4 (hai câu hoàn toàn không liên quan). Ngược lại cặp 2 (thư viện vs học bổng, hai chủ đề khác nhau) lại có điểm cao nhất (0.2786). Điều này cho thấy `_mock_embed` sinh vector từ hash MD5 của chuỗi ký tự — gần như ngẫu nhiên, không mã hoá ngữ nghĩa thật, nên điểm similarity chỉ phản ánh "trùng khớp ký tự ngẫu nhiên" chứ không phản ánh nội dung câu. Đúng như cảnh báo trong README/exercises.md: mock chỉ dùng để unit test cơ chế (đúng công thức cosine), không dùng để kết luận chất lượng ngữ nghĩa — cần chạy lại với `EMBEDDING_PROVIDER=local` để có kết quả phản ánh đúng ngữ nghĩa tiếng Việt.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chiến lược cá nhân: `ClauseChunker` (custom — tách theo mục đánh số kiểu "1.1", "2.3", fallback `RecursiveChunker` nếu tài liệu không có clause đánh số). Corpus: 7 tài liệu K3 thật (`data/k3_university/`), `EMBEDDING_PROVIDER=local`. Chạy bằng `scripts/member_strategies.py` (thành viên "Nguyen Van Phong").

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 | 1 tín chỉ tương đương bao nhiêu giờ học? | `k3-financial-regulations-tariff` — "Note: Credits are understood as subjects that have determined a specific number of academic credits according to VinUniversity's current Training Regulations..." | 0.7584 | **Không** trong top-3 — nhầm nghĩa "credit" tài chính với "credit" học thuật (câu định nghĩa thật nằm trong prose Article 4, không có số clause riêng nên `ClauseChunker` không tách ra được) → **0đ** | Sai — trích nhầm đoạn "credit" tài chính |
| 2 | Sinh viên đóng học phí mấy lần/năm? | `k3-financial-regulations-tariff` — "2.3. Annual Payment Discount — Students who pay tuition and dormitory fees upfront for the entire academic year will receive a 5% discount..." | 0.7199 | Có, nhưng **hạng 3** (chunk chứa "twice/year" không lọt top-1) → **1đ** | Nói về chiết khấu đóng trước, không phải tần suất — sai |
| 3 | Sinh viên đại học mượn tối đa bao nhiêu tài liệu, trong bao lâu? | `k3-library-borrow-request-undergrad` — "Undergraduate students may borrow up to 3 items during two weeks per item. Books may be renewed once..." | 0.7385 | Có, rank-1 → **2đ** | Đúng, đủ chi tiết |
| 4 | Sinh viên năm nhất có bắt buộc ở ký túc xá không? | `k3-residential-life-guideline` — "II. Scope — This guideline applies to all students of VinUniversity residing in VinUni-provided accommodation..." | 0.8194 | Có, rank-1 nhưng **1đ** — câu "required to reside" nằm ngoài phạm vi ~400 ký tự trích xuất được từ chunk "Scope" | Đúng hướng nhưng chưa đủ chi tiết |
| 5 | Sinh viên cần làm gì để giữ học bổng suốt thời gian học? | `k3-undergrad-scholarships` — "The scholarship applies for the entire duration of study and is subject to meeting the minimum scholarship maintenance conditions..." | 0.7889 | Có, rank-1 → **2đ** | Đúng, đủ chi tiết |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 — Tổng điểm theo `docs/SCORING.md`: **6/10** (Q1=0, Q2=1, Q3=2, Q4=1, Q5=2).

Câu 1 thất bại vì corpus dùng từ **"credit"** với 2 nghĩa khác nhau (tín chỉ học thuật ở `k3-academic-regulations-undergrad` Article 4, và một loại phí ở `k3-financial-regulations-tariff`) — embedding không phân biệt được, chọn nhầm chunk cùng từ khóa nhưng khác ngữ cảnh. Với `ClauseChunker` cụ thể, câu định nghĩa "50 hours" nằm trong đoạn văn của Article 4 nhưng không có số clause "N.N" riêng nên bị gộp vào chunk khác hoặc rơi vào fallback — thua kém tài liệu tài chính có clause đánh số dày đặc chứa cùng từ khóa "credit". Đây là giới hạn cấu trúc thật của chiến lược, không phải lỗi implement (xem thêm `REPORT_NHOM.md` — Phần 4).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Chiến lược `RecursiveChunker` (built-in, không cần viết code riêng) của Lê Thị Yến Nhi đạt điểm retrieval cao hơn hẳn `ClauseChunker` tôi tự viết (8/10 so với 6/10 trên `scripts/score_benchmark.py`) — cho thấy với corpus có cấu trúc đoạn văn rõ ràng (quy định đại học), việc ưu tiên tách theo `\n\n`/`\n` sẵn có trong `RecursiveChunker` giữ ngữ cảnh tốt hơn cách tách theo clause đánh số của tôi, nhất là với những câu định nghĩa nằm trong prose không có số clause riêng (đúng lỗi tôi gặp ở Câu 1). Ngược lại `HeadingSectionChunker` của Vũ Huy Hoàng (7/10) tuy giữ trọn 1 Article/mục và có recall cao nhất nhóm, nhưng lại làm tài liệu `audience=staff` dễ lọt gần top-k hơn khi quên bật metadata filter — bài học là chunk "sạch cấu trúc" không tự động đồng nghĩa với an toàn hơn về phân quyền audience, và granularity mịn (ClauseChunker) không tự động thắng granularity thô nếu câu trả lời nằm ở phần văn bản không có cấu trúc rõ (prose thuần).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5/ 5                   |
| Hướng tiếp cận của tôi (My Approach)           | 10/ 10                 |
| Hoàn thiện code (Core Implementation — tests)     | 30/ 30                 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5                   |
| Kết quả truy xuất của tôi (Competition Results) | 6/ 10 |
| **Tổng phần cá nhân**                      | **56/ 60**       |
