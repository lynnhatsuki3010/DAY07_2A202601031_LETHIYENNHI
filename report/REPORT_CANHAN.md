# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Thị Yến Nhi - 2A202601031
**Nhóm:** A3
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding có hướng gần giống nhau trong không gian nhiều chiều, tức nội dung ngữ nghĩa của hai đoạn văn bản gần giống nhau, bất kể độ dài câu.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên đăng ký học phần trên cổng học vụ."
- Câu B: "Sinh viên đăng ký học phần qua hệ thống học vụ trực tuyến."
- Tại sao tương đồng: cùng diễn đạt một hành động (đăng ký học phần) với cùng chủ thể và ngữ cảnh, chỉ khác cách dùng từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thư viện mở cửa từ 7 giờ sáng đến 9 giờ tối."
- Câu B: "Học bổng khuyến khích học tập dành cho sinh viên có thành tích tốt."
- Tại sao khác: hai chủ đề không liên quan (giờ mở cửa thư viện vs chính sách học bổng).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo góc (hướng) giữa hai vector, không bị ảnh hưởng bởi độ lớn (magnitude) — trong khi magnitude của embedding có thể lệch theo độ dài câu dù ý nghĩa giống nhau. Euclidean distance nhạy với magnitude nên dễ đánh giá sai hai câu đồng nghĩa nhưng độ dài khác nhau là "xa nhau".

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11)
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> ceil((10000 − 100) / (500 − 100)) = ceil(9900 / 400) = ceil(24.75) = **25 chunks** — tăng overlap làm mỗi bước tiến ngắn hơn nên số chunk tăng. Overlap lớn hơn giúp giữ ngữ cảnh liên tục qua ranh giới chunk, tránh cắt đứt ý nằm vắt giữa hai chunk, cải thiện chất lượng truy xuất khi thông tin cần thiết nằm ở mép chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng một regex duy nhất `(?<=[.!?])\s+` (lookbehind) để tách câu — nó khớp mọi khoảng trắng (kể cả xuống dòng) ngay sau dấu `.`, `!`, `?`, nên gộp được cả 3 trường hợp ". ", "! ", "? " và ".\n" mà không cần nhiều pattern riêng. Sau khi tách, lọc bỏ chuỗi rỗng và `strip()` từng câu để tránh chunk toàn khoảng trắng, rồi gom theo `max_sentences_per_chunk` bằng `range(step)`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` đệ quy thử từng separator theo thứ tự ưu tiên. Base case: nếu `len(current_text) <= chunk_size` trả về nguyên văn; nếu hết separator (hoặc separator hiện tại là `""`) thì cắt cứng theo `chunk_size`. Ngược lại, tách theo separator rồi gộp các phần liền kề vào một buffer miễn tổng độ dài không vượt `chunk_size` (tối ưu hoá dùng hết chunk_size thay vì 1 phần/chunk); phần nào tự nó đã vượt `chunk_size` thì đệ quy tiếp với danh sách separator còn lại.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` gọi `_make_record` cho từng doc để tạo dict chuẩn hoá (id, content, metadata có `doc_id`, embedding) rồi append vào list `self._store` trong bộ nhớ. `search` nhúng câu hỏi, gọi `_search_records` tính dot product giữa embedding câu hỏi và embedding từng record (`_dot`), sort giảm dần theo score rồi cắt `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc trước: duyệt `self._store`, giữ record có tất cả cặp key-value trong `metadata_filter` khớp với `record["metadata"]`, rồi mới chạy `_search_records` trên tập đã lọc — tránh tính similarity trên dữ liệu không cần thiết. `delete_document` dùng list comprehension giữ lại record có `metadata["doc_id"] != doc_id`, so sánh độ dài list trước/sau để trả `True`/`False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k)` lấy các chunk liên quan, nối `content` của chúng bằng `"\n\n"` làm context. Prompt có cấu trúc cố định: chỉ thị "trả lời dựa trên context, nếu không có thì nói rõ" + block Context + Question, rồi gọi `llm_fn(prompt)` và trả thẳng string kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================================= test session starts ==============================================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py .......................................... [100%]

============================================== 42 passed in 1.65s ==============================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên đăng ký học phần qua cổng học vụ. | Sinh viên đăng ký học phần trên hệ thống học vụ trực tuyến. | cao | -0.1484 (thấp nhất) | Sai |
| 2 | Thư viện mở cửa từ 7 giờ sáng đến 9 giờ tối. | Học bổng khuyến khích học tập dành cho sinh viên có thành tích tốt. | thấp | 0.1577 (cao nhất) | Sai |
| 3 | Con mèo đang ngủ trên ghế sofa. | Chú mèo nằm ngủ trên chiếc ghế. | cao | 0.0392 | Đúng (tương đối) |
| 4 | Học phí học kỳ này tăng 5% so với năm trước. | Hôm nay trời nắng đẹp, thích hợp đi dạo. | thấp | -0.0276 | Đúng |
| 5 | Ký túc xá ưu tiên sinh viên năm nhất ở xa. | Sinh viên năm nhất ở xa được ưu tiên xét duyệt ký túc xá. | cao | -0.0580 | Sai |

*(Điểm tính bằng `compute_similarity()` + `_mock_embed`, đúng cấu hình mặc định của lab — chưa bật `EMBEDDING_PROVIDER=local`.)*

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 1 — hai câu gần như paraphrase hoàn toàn (cùng nói về đăng ký học phần) — lại có score THẤP NHẤT (-0.1484), trong khi cặp 2 gồm hai câu hoàn toàn khác chủ đề lại có score CAO NHẤT (0.1577). Lý do: `_mock_embed` sinh vector từ hash MD5 của chuỗi ký tự (`src/embeddings.py`), không mã hoá ngữ nghĩa thật — nên cosine similarity tính ra gần như ngẫu nhiên, không phản ánh nội dung câu. Điều này đúng như cảnh báo trong README: mock chỉ dùng để unit test có kết quả xác định (deterministic), muốn so sánh ngữ nghĩa tiếng Việt thật phải chuyển `EMBEDDING_PROVIDER=local` (dùng `LocalEmbedder`).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Chiến lược cá nhân:** `RecursiveChunker(chunk_size=400)` (built-in), chạy trên corpus thật `data/k3_university/` (7 tài liệu VinUniversity) với `LocalEmbedder` (`EMBEDDING_PROVIDER=local`). Code: `scripts/member_strategies.py`, chấm điểm: `scripts/score_benchmark.py`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | What is the definition of an academic credit in terms of study hours for undergraduate students? | `k3-academic-regulations-undergrad`: "A credit is a unit that is used to determine the amount of academic work of a student. A credit is equivalent to 50 hours of study..." | 0.7934 | Có, rank-1 | Đúng, đủ chi tiết (trích đúng câu "50 hours of study") |
| 2 | Sinh viên đóng học phí mấy lần/năm? | `k3-financial-regulations-tariff`: "Listed tuition fee: 932,400,000 VND/year..." | 0.7418 | Không — trúng tài liệu đúng nhưng đúng đoạn nói về số tiền, không phải tần suất đóng | Trích số tiền học phí, không trả lời "mấy lần/năm" |
| 3 | SV đại học mượn tối đa bao nhiêu tài liệu, trong bao lâu? (metadata_filter audience=student) | `k3-library-borrow-request-undergrad`: "Undergraduate students may borrow up to 3 items during two weeks per item..." | 0.7387 | Có, rank-1 | Đúng, đủ chi tiết (3 items / 2 tuần / gia hạn 1 lần) |
| 4 | SV năm nhất có bắt buộc ở KTX không? | `k3-residential-life-guideline`: "All first-year students are required to reside in the VinUni dormitory..." | 0.8424 | Có, rank-1 | Đúng, đủ chi tiết |
| 5 | SV cần làm gì để duy trì học bổng suốt khoá học? | `k3-undergrad-scholarships`: "The scholarship applies for the entire duration of study and is subject to meeting the minimum scholarship maintenance conditions..." | 0.7687 | Có, rank-1 | Đúng, đủ chi tiết |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 — Tổng điểm theo `docs/SCORING.md`: **8/10** (Q1=2, Q2=0, Q3=2, Q4=2, Q5=2).

*(Lịch sử: bản chạy đầu tiên chỉ đạt 6/10 do 2 lỗi — hàm `llm_fn` extractive cắt cụt câu trả lời tại heading, và Câu 1 diễn đạt quá ngắn khiến embedding nhầm sang nghĩa "credit" tài chính. Sau khi sửa lỗi trích xuất và viết lại Câu 1 rõ nghĩa hơn — không đổi gold answer/corpus — chạy lại đạt 8/10. Câu 2 vẫn chưa giải quyết được dù đã thử nhiều cách diễn đạt, xem `REPORT_NHOM.md` Phần 4.)*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> So với `HeadingSectionChunker` của Hoàng, chiến lược Recursive của tôi "an toàn" hơn về mặt audience filter: tài liệu `k3-library-management-regulation` (audience=staff) không hề lọt top-8 kể cả khi bỏ metadata filter, trong khi ở chunker của Hoàng nó đứng hạng 2/8 — chỉ vì Recursive chia nhỏ theo đoạn văn nên ngữ cảnh mỗi chunk hẹp hơn, ít "bắt" được toàn bộ chủ đề chung "thư viện" như chunk theo cả section. Học được là lựa chọn chunking không chỉ ảnh hưởng độ chính xác mà còn ảnh hưởng cả mức độ rủi ro rò rỉ dữ liệu sai đối tượng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 *(điểm thật đã chạy, xem Phần 5)* |
| **Tổng phần cá nhân** | **58 / 60** |
