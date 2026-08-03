# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Huy Hoàng
**Nhóm:** A3
**Ngày:** 8/3/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Mỗi đoạn văn bản (chunk) được mã hóa thành một vector (embedding). Khi hai vector có độ tương tự cosine cao, điều đó chứng tỏ hai đoạn văn bản có ngữ nghĩa và chủ đề rất giống nhau hoặc liên quan mật thiết với nhau, bất kể một đoạn có thể dài hơn đoạn kia rất nhiều.

**Ví dụ có độ tương tự CAO:**

- Câu A:"Mình rất thích nghe nhạc acoustic vào những ngày mưa."
- Câu B:"Việc thưởng thức các giai điệu mộc mạc nhẹ nhàng lúc trời đang trút nước mang lại cho tôi cảm giác thực sự bình yên."
- Tại sao tương đồng:`Dù hai câu dùng từ vựng khác hẳn nhau và câu B dài hơn hẳn câu A, nhưng cả hai đều miêu tả chung một ý là thích nghe nhạc êm dịu khi trời mưa. AI hiểu được nội dung bên trong thay vì chỉ so sánh từng chữ cái, nên sẽ chấm điểm tương đồng rất cao.`

**Ví dụ có độ tương tự THẤP:**

- Câu A:"Ngân hàng nhà nước vừa thông báo giảm lãi suất tiền gửi."
- Câu B:"Chiều nay tôi phải ra ngân hàng để lấy cái áo mưa bỏ quên."
- Tại sao khác:Dù cả hai câu đều có chung từ "ngân hàng", nhưng ngữ cảnh và chủ đề lại không hề liên quan. Một câu nói về tin tức tài chính, còn một câu là chuyện sinh hoạt cá nhân hàng ngày. Vì nội dung nhắc tới hoàn toàn khác biệt, AI sẽ đánh giá độ tương tự của hai câu này rất thấp.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Độ tương tự cosine được ưu tiên vì nó chỉ dựa vào góc giữa hai vector để so sánh ý nghĩa nội dung, hoàn toàn bỏ qua sự chênh lệch về độ dài ngắn của văn bản. Nhờ đó, AI nhận diện chính xác hai đoạn văn có cùng chủ đề dù một đoạn rất ngắn và một đoạn rất dài, điều mà khoảng cách Euclid dễ đánh giá sai vì bị ảnh hưởng bởi số lượng từ vựng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> -Chunk đầu tiên sẽ chứa 500 ký tự. Số ký tự còn lại cần xử lý là: 10.000 - 500 = 9.500 ký tự.
>
> -Do các chunk gối lên nhau (overlap) 50 ký tự, nên mỗi chunk tiếp theo chỉ thực sự tiến về phía trước được một đoạn nội dung mới là: 500 - 50 = 450 ký tự.
>
> -Số lượng chunk cần thêm để chứa hết phần 9.500 ký tự còn lại là: 9.500 / 450 ≈ 21,11 (làm tròn lên thành 22 chunk vì phần lẻ vẫn cần một chunk riêng để chứa).
>
> -Tổng số chunk của cả tài liệu là: 1 (chunk đầu) + 22 (chunk sau) = 23 chunk.
>
> * *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Nếu tăng độ chồng chéo lên 100, số lượng chunk sẽ tăng lên thành 25 chunk (do mỗi đoạn sau chỉ tiến lên được 400 ký tự mới). Việc tăng độ chồng chéo giúp các ý quan trọng hoặc câu văn dài không bị cắt đứt gãy giữa chừng, đảm bảo đoạn trích xuất luôn giữ được trọn vẹn ngữ cảnh.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi sử dụng biểu thức chính quy (regex) nhận diện các dấu kết thúc câu phổ biến như dấu chấm, dấu hỏi chấm và dấu chấm than đi kèm với khoảng trắng (ví dụ: `(?<=[.!?])\s+`) để tách văn bản thành từng câu. Bên cạnh đó, tôi cũng xử lý thêm các trường hợp ngoại lệ như những từ viết tắt có chứa dấu chấm (ví dụ: "Th.S", "TP.HCM") hoặc cụm dấu ba chấm ("...") để đảm bảo hệ thống không vô tình cắt sai làm đứt gãy ý nghĩa của câu văn.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán hoạt động bằng cách đệ quy chia nhỏ văn bản dựa trên một danh sách các dấu phân cách có mức độ ưu tiên giảm dần (ví dụ: tách theo đoạn văn trước, nếu đoạn đó vẫn quá dài thì đệ quy tách tiếp theo từng câu, rồi mới đến từng từ). Trường hợp cơ sở (base case) để dừng đệ quy là khi phần văn bản đang xét có kích thước nhỏ hơn hoặc bằng giới hạn `chunk_size` quy định. Khi thỏa mãn điều kiện này, thuật toán sẽ ngừng chia nhỏ và lưu ngay phần văn bản đó thành một chunk hoàn chỉnh.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Đối với `EmbeddingStore`, tôi lưu trữ các vector nhúng (embeddings) cùng với siêu dữ liệu (metadata) của tài liệu vào các cấu trúc dữ liệu trên bộ nhớ (in-memory) hoặc sử dụng cơ sở dữ liệu vector như ChromaDB. Khi thực hiện hàm `search`, tôi tính toán độ tương tự Cosine (Cosine Similarity) giữa vector của câu truy vấn và vector của các tài liệu đã lưu để xếp hạng, qua đó trả về những đoạn văn bản có độ liên quan cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Với hàm `search_with_filter`, tôi áp dụng cơ chế lọc dựa trên siêu dữ liệu (metadata) trước khi tính toán độ tương tự (pre-filtering) để thu hẹp phạm vi tìm kiếm và tối ưu tốc độ xử lý. Đối với `delete_document`, hệ thống sẽ tìm kiếm thông qua mã định danh (document ID) của tài liệu để xác định chính xác các phần tử cần xóa. Sau đó, toàn bộ các chunk văn bản, vector nhúng và siêu dữ liệu (metadata) liên quan đến ID này sẽ được gỡ bỏ hoàn toàn khỏi không gian lưu trữ.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Cấu trúc prompt được thiết kế với chỉ dẫn rõ ràng, yêu cầu mô hình ngôn ngữ lớn (LLM) chỉ được phép trả lời dựa trên thông tin được cung cấp nhằm hạn chế tối đa tình trạng "ảo giác" (hallucination) hay bịa đặt thông tin. Ngữ cảnh (context) được đưa vào bằng cách nối (concatenate) các đoạn văn bản (chunks) liên quan nhất vừa được truy xuất từ `EmbeddingStore`, sau đó chèn trực tiếp vào template cùng với câu hỏi gốc của người dùng trước khi gửi cho LLM xử lý.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
PS C:\Lab07\Day07_2A202601057_VuHuyHoang> pytest tests/ -v
======================================= test session starts =======================================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\asus\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: C:\Lab07\Day07_2A202601057_VuHuyHoang
plugins: anyio-4.8.0, langsmith-0.10.10, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 42 items                                                                             

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED        [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                 [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED          [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED           [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED      [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED       [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED     [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                       [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED       [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                  [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED              [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                        [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED   [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED   [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                       [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED         [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED           [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                 [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED      [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED        [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED         [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                  [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                 [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED            [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED        [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED   [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED       [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED             [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED       [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED  [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_docPASSED [100%]

======================================= 42 passed in 1.27s ========================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---



## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp        | Câu A                                                                                                                                                                   | Câu B                                                                                                                                                                                                                                                                                                                                               | Dự đoán | Điểm thực tế | Đúng? |
| :---------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------- | :--------------- | :------ |
| **1** | A full-time student is undertaking at least 80% of a full-time load in an academic program[cite: 1].                                                                     | To be classified as a full-time student, s/he must be enrolled in at a minimum, 80% of a normal full-time load in a regular Semester (equivalent to 12 credits)[cite: 1].                                                                                                                                                                            | cao        | -0.1983          | Không  |
| **2** | From 2025 to 2030, all students enrolling at VinUniversity will be granted a 35% tuition subsidy, applied for the full duration of their studies[cite: 7].               | All Students successfully enrolled in VinUniversity until the year 2030 will receive the Educational Development Grant from the Founding Donor equivalent to 35% discount of the listed tuition fees for the entire official duration of the program (according to the standard course time designed for Students to complete the program)[cite: 2]. | cao        | 0.1018           | Có     |
| **3** | Equipment overdue for more than 05 days will be considered lost, and the borrower will be charged for a replacement[cite: 4].                                            | The library may recall items for maintenance or other needs[cite: 3].                                                                                                                                                                                                                                                                                | thấp      | -0.3902          | Có     |
| **4** | Library opening hours are subject to change during exam periods, holidays, and summer break and will be posted at the main library entrance and on the library[cite: 3]. | Students are allowed to apply for a voluntary leave of absence or withdrawal and to reserve the study results in the following cases[cite: 1]:                                                                                                                                                                                                       | thấp      | -0.1575          | Có     |
| **5** | Provost’s Merit Scholarship: Covers 100% of tuition[cite: 7].                                                                                                           | Residents should not bypass or disable residential security[cite: 6].                                                                                                                                                                                                                                                                                | thấp      | 0.1414           | Không  |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Kết quả bất ngờ nhất là Cặp 1 (hai câu có nội dung định nghĩa sinh viên toàn thời gian gần như tương đồng tuyệt đối) lại có điểm số thực tế âm (-0.1983) và bị đánh giá là "Không" khớp với dự đoán. Điều này cho thấy các hàm embedding giả lập (`_mock_embed`) hoặc mô hình chưa qua huấn luyện sâu thường không nắm bắt được ý nghĩa ngữ nghĩa thực sự của từ ngữ, mà chỉ tạo ra các vector ngẫu nhiên hoặc dựa trên bề nổi, dẫn đến việc các câu có ý nghĩa giống nhau lại có độ tương đồng thấp.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chiến lược cá nhân: `HeadingSectionChunker` (custom — tách theo heading "Article N.", La Mã "I./II.", chữ cái "A./B.", fallback `RecursiveChunker` nếu tài liệu không có heading; đây là chiến lược **bắt buộc theo K3_VARIANT.md** — ít nhất 1 thành viên chunk theo heading/section của quy định học vụ). Corpus: 7 tài liệu K3 thật (`data/k3_university/`), `EMBEDDING_PROVIDER=local`. Chạy bằng `scripts/member_strategies.py` (thành viên "Vu Huy Hoang"), chấm bằng `scripts/score_benchmark.py`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 | Định nghĩa credit theo giờ học? | `k3-academic-regulations-undergrad` — "Article 4. Course and Credit — A course is known as a relatively complete amount of knowledge..." | 0.6294 | Có, rank-1 → **1đ** (câu "50 hours of study" nằm ở vị trí ~1300 ký tự trong chunk 2516 ký tự — quá xa để lọt vào ~400 ký tự trích xuất) | Đúng hướng (đúng Article) nhưng chưa đủ chi tiết |
| 2 | Sinh viên đóng học phí mấy lần/năm? | `k3-financial-regulations-tariff` — "I. LISTED TUITION FEE — Listed tuition fee is issued according to..." | 0.6923 | Có, rank-1 → **1đ** (câu "twice/year" ở gần cuối chunk, ngoài phạm vi trích xuất) | Đúng hướng, chưa đủ chi tiết |
| 3 | Sinh viên đại học mượn tối đa bao nhiêu tài liệu, trong bao lâu? | `k3-library-borrow-request-undergrad` — "Undergraduate students may borrow up to 3 items during two weeks per item..." | 0.7385 | Có, rank-1 → **2đ** | Đúng, đủ chi tiết |
| 4 | Sinh viên năm nhất có bắt buộc ở ký túc xá không? | `k3-residential-life-guideline` — "II. Scope — This guideline applies to all students..." | 0.7515 | Có, nhưng **hạng 2** (chunk rank-1 "II. Scope" không chứa câu "required to reside"; câu đó nằm ở chunk rank-2 "III. General Policy Principles") → **1đ** | Đúng hướng, chưa đủ chi tiết |
| 5 | Sinh viên cần làm gì để giữ học bổng suốt thời gian học? | `k3-undergrad-scholarships` — "The scholarship applies for the entire duration of study..." | 0.7889 | Có, rank-1 → **2đ** | Đúng, đủ chi tiết |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 (recall cao nhất nhóm) — Tổng điểm theo `docs/SCORING.md`: **7/10** (Q1=1, Q2=1, Q3=2, Q4=1, Q5=2).

Đánh đổi thật của chiến lược: chunk theo cả Article/section giữ trọn 1 điều khoản trong 1 chunk (dễ truy vết nguồn, recall cao), nhưng vì chunk dài (2500-3200 ký tự) nên câu chứa số liệu cụ thể thường nằm sâu, dễ nằm ngoài phạm vi câu trả lời trích xuất được — 3/5 câu chỉ đạt 1đ dù retrieval đúng 100%. Ngoài ra, nếu **bỏ** `metadata_filter`, tài liệu `k3-library-management-regulation` (audience=**staff**) đứng **hạng 2/8** trong kết quả không lọc — rủi ro rò rỉ audience cao nhất trong 5 chiến lược của nhóm, bằng chứng rõ nhất cho việc Câu 3 bắt buộc dùng metadata filter.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Chiến lược `RecursiveChunker` (built-in) của Lê Thị Yến Nhi đạt điểm cao hơn tôi (8/10 so với 7/10) dù chunk nhỏ hơn nhiều (chunk_size=400 so với cả Article 2500-3200 ký tự của tôi) — cho thấy chunk nhỏ, gọn theo đoạn văn giúp câu trả lời trích xuất "chạm" tới đúng câu chứa số liệu dễ hơn, dù chunk lớn theo Article có recall tốt hơn (chunk đúng hầu như luôn xuất hiện). Học được là recall cao (tìm đúng chunk) không tự động đồng nghĩa với answer đúng — kích thước chunk ảnh hưởng trực tiếp tới việc câu trả lời có đủ chi tiết hay không.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5/ 5                   |
| Hướng tiếp cận của tôi (My Approach)           | 10/ 10                 |
| Hoàn thiện code (Core Implementation — tests)     | 30/ 30                 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5                   |
| Kết quả truy xuất của tôi (Competition Results) | 7/ 10  |
| **Tổng phần cá nhân**                      | **57/ 60**       |
