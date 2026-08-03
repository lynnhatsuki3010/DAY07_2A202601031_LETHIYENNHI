# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thanh Phúc
**Nhóm:** A3
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau, cho thấy hai đoạn văn bản có nội dung hoặc ý nghĩa gần nhau. Trong bài này, hai câu hỏi cùng nói về một thủ tục đại học có khả năng truy xuất cùng một chunk tài liệu.

**Ví dụ có độ tương tự CAO:**

- Câu A: Sinh viên đăng ký học phần như thế nào?
- Câu B: Quy trình đăng ký môn học dành cho sinh viên là gì?
- Tại sao tương đồng: Hai câu đều hỏi về cùng chủ đề là cách đăng ký học phần, dù sử dụng từ ngữ khác nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Sinh viên đăng ký học phần như thế nào?
- Câu B: Thư viện mở cửa vào thời gian nào?
- Tại sao khác: A nói về đăng ký môn học, còn câu B nói về thời gian hoạt động của thư viện, nên hai câu thuộc hai chủ đề khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
Cosine similarity so sánh hướng của các vector thay vì chỉ so sánh khoảng cách tuyệt đối, nên phù hợp hơn để đo mức độ tương đồng về ý nghĩa của văn bản. Nó cũng ít bị ảnh hưởng bởi độ dài văn bản hoặc độ lớn của vector embedding.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> _Trình bày phép tính:_

Bước dịch của mỗi chunk:

    step = chunk_size - overlap
         = 500 - 50
         = 450

Số lượng chunk:

    ceil((10,000 - 50) / 450)
    = ceil(9,950 / 450)
    = ceil(22.11)
    = 23

> _Đáp án:_ 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
Khi overlap tăng lên 100

    step = 500 - 100
         = 400

Số lượng chunk:

    ceil((10,000 - 100) / 400)
    = ceil(9,900 / 400)
    = ceil(24.75)
    = 25

Đáp án mới: 25 chunks.

Overlap lớn hơn giúp giữ lại nhiều ngữ cảnh giữa hai chunk, nhưng làm tăng số lượng chunk và chi phí lưu trữ/embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

Tôi dùng biểu thức chính quy `r"(?<=[.!?])(?:\s+|$)"` để tách văn bản sau các dấu kết thúc câu `.`, `!` và `?`. Sau đó, các câu được gom thành từng nhóm, mỗi nhóm có tối đa `max_sentences_per_chunk` câu; nếu văn bản rỗng thì hàm trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

Thuật toán lần lượt thử các separator theo thứ tự ưu tiên là đoạn văn, xuống dòng, kết thúc câu, khoảng trắng và cuối cùng là tách theo kích thước ký tự. Trường hợp cơ sở là khi đoạn văn không vượt quá `chunk_size`; nếu đoạn quá dài, hàm tiếp tục chia bằng separator tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

`add_documents` chuyển mỗi `Document` thành một record gồm `id`, `content`, `metadata` và vector embedding, sau đó lưu vào ChromaDB nếu khả dụng hoặc danh sách `_store` trong bộ nhớ nếu không có ChromaDB. Khi `search` được gọi, câu hỏi cũng được chuyển thành embedding; hệ thống tính dot product giữa vector câu hỏi và các vector đã lưu, sắp xếp theo điểm giảm dần rồi trả về tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

`search_with_filter` lọc các record theo metadata trước, yêu cầu mọi cặp khóa–giá trị trong `metadata_filter` phải khớp, sau đó mới tính similarity trên tập record đã lọc. `delete_document` tìm các record có `metadata["doc_id"]` bằng `doc_id` cần xóa và loại bỏ toàn bộ chúng; hàm trả về `True` nếu có record bị xóa và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

Agent gọi `store.search()` để truy xuất các chunk liên quan đến câu hỏi, sau đó ghép nội dung các chunk thành phần ngữ cảnh. Ngữ cảnh và câu hỏi được đưa vào prompt rồi truyền cho `llm_fn` để tạo câu trả lời dựa trên thông tin đã truy xuất.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
Test command: uv run pytest tests/ -v

Result: 42 passed
Status: All tests passed.
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                      | Câu B                                                                 | Dự đoán | Điểm thực tế | Đúng? |
| --- | ---------------------------------------------------------- | --------------------------------------------------------------------- | ------- | -----------: | ----- |
| 1   | Sinh viên đăng ký học phần như thế nào?                    | Quy trình đăng ký môn học dành cho sinh viên là gì?                   | cao     |    -0.149741 | Không |
| 2   | Sinh viên đăng ký học phần như thế nào?                    | Thư viện mở cửa vào thời gian nào?                                    | thấp    |     0.125513 | Đúng  |
| 3   | How many items can a student borrow?                       | What is the maximum number of library materials a student may borrow? | cao     |     0.135104 | Không |
| 4   | How many times per year do students pay tuition fees?      | What scholarship conditions must students maintain?                   | thấp    |     0.142045 | Đúng  |
| 5   | Are first-year students required to live in the dormitory? | Do first-year students have to reside in the VinUni dormitory?        | cao     |     0.045898 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Kết quả bất ngờ là những câu có cùng ý nghĩa vẫn có thể nhận điểm tương tự rất thấp, thậm chí âm. Nguyên nhân là bài này đang dùng `_mock_embed`, một embedder tạo vector xác định nhưng gần như ngẫu nhiên theo chuỗi ký tự, nên điểm số không phản ánh tốt ngữ nghĩa. Vì vậy, kết quả này cho thấy cần dùng LocalEmbedder khi muốn đánh giá semantic similarity thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| #   | Câu hỏi                                                                                        | Top-1 Chunk truy xuất được                                                                            | Điểm Score | Relevant                        | Agent answer                                       |
| --- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------: | ------------------------------- | -------------------------------------------------- |
| 1   | How many hours of study is one academic credit at VinUniversity equivalent to?                 | `k3-financial-regulations-tariff`: “…olling from the 2024-2025 academic year onwards. Note: Credits…” |     0.7969 | Có trong top-3, rank-2 — 1 điểm | “olling from the 2024-2025 academic year onwards.” |
| 2   | How many times per year do students pay tuition fees?                                          | `k3-financial-regulations-tariff`: “…informed. This fee is NOT refundable…”                           |     0.6626 | Không trong top-3 — 0 điểm      | “informed.”                                        |
| 3   | How many items can an undergraduate student borrow from the library at once, and for how long? | `k3-library-borrow-request-undergrad`: “…rary card to borrow library materials…”                      |     0.7679 | Có trong top-3, rank-1 — 1 điểm | Bị cắt giữa từ “library”, thiếu ngữ cảnh           |
| 4   | Are first-year students required to live in the VinUni dormitory?                              | `k3-residential-life-guideline`: “…ersity residing in VinUni-provided accommodation…”                 |     0.8183 | Có trong top-3, rank-1 — 1 điểm | Bị cắt giữa từ “university”                        |
| 5   | What must a student do to keep their scholarship for the whole duration of study?              | `k3-financial-regulations-tariff`: “…able for the entire duration of the Student's study…”            |     0.7036 | Có trong top-3, rank-2 — 1 điểm | Bị cắt giữa từ “applicable”                        |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** Tổng điểm: 4 / 10

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

Điều hay nhất tôi học được từ thành viên khác / nhóm khác là chiến lược Recursive, Heading và Clause giữ được ranh giới ngữ nghĩa tốt hơn FixedSizeChunker. Tôi cũng nhận ra retrieval đúng chưa đảm bảo câu trả lời đúng, vì hàm extractive_llm có thể cắt giữa từ hoặc chỉ lấy phần heading của chunk. Metadata filter đặc biệt quan trọng với câu hỏi về tài liệu thư viện dành cho sinh viên.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------- |
| Khởi động (Warm-up)                             | 5 / 5            |
| Hướng tiếp cận của tôi (My Approach)            | 10 / 10          |
| Hoàn thiện code (Core Implementation — tests)   | 30 / 30          |
| Dự đoán độ tương tự (Similarity Predictions)    | 2 / 5            |
| Kết quả truy xuất của tôi (Competition Results) | 4 / 10           |
| **Tổng phần cá nhân**                           | **51 / 60**      |
