# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** A3
**Thành viên:**
- Phạm Khánh Linh - 2A202601507
- Nguyễn Thanh Phúc - 2A202601345
- Vũ Huy Hoàng - 2A202601057
- Nguyễn Văn Phong - 2A202601241
- Lê Thị Yến Nhi - 2A202601031

**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> Dịch vụ và quy định đại học tại **VinUniversity**: đăng ký học phần/quy chế học vụ, học phí, học bổng, dịch vụ thư viện, và ký túc xá (residential life).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Academic Regulations for Full-Time Undergraduate Programs | policy.vinuni.edu.vn/all-policies/academic-regulations-for-full-time-undergraduate-programs/ | 2026-08-03 / not-stated | 71,239 | audience=student, department=registrar, category=course-registration, language=en |
| 2 | Financial Regulations and Tariff (for student) | policy.vinuni.edu.vn/all-policies/financial-regulations-and-tariff-for-student-2/ | 2026-08-03 / not-stated | 36,722 | audience=student, department=finance, category=tuition, language=en |
| 3 | Undergraduate Scholarships | admissions.vinuni.edu.vn/scholarship-and-financial-aid/undergraduate-programs/scholarships/ | 2026-08-03 / not-stated | 3,606 | audience=student, department=admissions, category=scholarship, language=en |
| 4 | Library Access & Services Policy | policy.vinuni.edu.vn/all-policies/library-policies-for-users/ | 2026-08-03 / not-stated | 8,427 | audience=student, department=library, category=library-services, language=en |
| 5 | Borrow and Request - Undergraduate Students and Staff | library.vinuni.edu.vn/services/borrow-and-request/undergraduate-and-staff/ | 2026-08-03 / not-stated | 7,648 | audience=student, department=library, category=library-services, language=en |
| 6 | Regulation for Library Management | policy.vinuni.edu.vn/all-policies/regulation-for-library-management/ | 2026-08-03 / not-stated | 11,719 | audience=**staff**, department=library, category=library-management, language=en |
| 7 | Residential Life Guideline | policy.vinuni.edu.vn/all-policies/residential-life-guideline/ | 2026-08-03 / not-stated | 17,105 | audience=student, department=student-life, category=dormitory, language=en |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string (enum) | `student`, `staff` | Bắt buộc theo K3 — lọc loại trừ tài liệu dành cho staff (vd. quy định quản lý thư viện nội bộ) khi câu hỏi chỉ hỏi về quyền lợi sinh viên |
| `department` | string | `registrar`, `finance`, `admissions`, `library`, `student-life` | Thu hẹp phạm vi tìm kiếm về đúng đơn vị phụ trách, hữu ích khi câu hỏi nêu rõ phòng ban |
| `category` | string | `tuition`, `scholarship`, `library-services`, `dormitory`... | Lọc theo chủ đề cụ thể, mịn hơn `department` (vd. tách `library-services` cho SV khỏi `library-management` cho staff dù cùng department) |
| `language` | string | `en` | Dự phòng khi corpus mở rộng thêm tài liệu tiếng Việt, tránh trộn lẫn kết quả khác ngôn ngữ |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` (chunk_size=500) trên 3 tài liệu thật (`data/k3_university/`), dùng `_mock_embed` mặc định (bước này chỉ đo thống kê chunking, không cần embedder thật):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| academic-regulations-undergrad (71,239 ký tự) | FixedSizeChunker (`fixed_size`) | 178 | 499.7 | Không — cắt cứng theo ký tự, có thể đứt giữa câu/điều khoản |
| academic-regulations-undergrad | SentenceChunker (`by_sentences`) | 160 | 442.6 | Có — trọn câu, nhưng gộp 3 câu cố định không theo cấu trúc Article/mục |
| academic-regulations-undergrad | RecursiveChunker (`recursive`) | 190 | 373.0 | Tốt nhất — ưu tiên tách theo `\n\n`/`\n` nên bám theo đoạn văn/điều khoản gốc |
| library-access-services-policy (8,427 ký tự) | FixedSizeChunker (`fixed_size`) | 21 | 496.5 | Không |
| library-access-services-policy | SentenceChunker (`by_sentences`) | 31 | 267.2 | Có, nhưng chunk ngắn hơn hẳn (câu chính sách thư viện ngắn) |
| library-access-services-policy | RecursiveChunker (`recursive`) | 18 | 466.3 | Tốt — theo cấu trúc mục I/II/1.1... |
| residential-life-guideline (17,105 ký tự) | FixedSizeChunker (`fixed_size`) | 43 | 495.5 | Không |
| residential-life-guideline | SentenceChunker (`by_sentences`) | 40 | 425.3 | Có |
| residential-life-guideline | RecursiveChunker (`recursive`) | 46 | 369.9 | Tốt — theo đoạn văn |

**Nhận xét:** `fixed_size` luôn bám sát avg_length ≈ chunk_size (đúng thiết kế, nhưng dễ cắt đứt câu/điều khoản ở ranh giới). `by_sentences` giữ trọn câu nhưng độ dài dao động mạnh theo văn phong nguồn (câu luật dài/ngắn thất thường — thấy rõ ở library-access-services-policy chỉ 267.2 ký tự/chunk). `recursive` cho count cao nhất + avg thấp nhất trong cả 3 tài liệu vì ưu tiên tách theo `\n\n`/`\n` — bám theo cấu trúc đoạn văn/điều khoản gốc của văn bản chính sách, phù hợp nhất với dữ liệu K3 (quy định có cấu trúc Article/mục rõ ràng).

### Chiến lược của từng thành viên

> Cả 5 chạy trên cùng corpus thật `data/k3_university/` (7 tài liệu), cùng `LocalEmbedder` (`EMBEDDING_PROVIDER=local`). Code: `scripts/member_strategies.py`.

**Thành viên 1 — Lê Thị Yến Nhi**
- **Loại chiến lược:** Recursive (built-in, `chunk_size=400`)
- **Mô tả & lý do chọn cho chủ đề này:** Baseline Phần 2.1 đã cho thấy `RecursiveChunker` bám cấu trúc đoạn văn/điều khoản gốc tốt nhất trong 3 chiến lược có sẵn (ưu tiên tách theo `\n\n`/`\n` trước khi phải cắt cứng). Chọn `chunk_size=400` (nhỏ hơn baseline 500) để chunk gọn hơn, giảm nhiễu ngữ nghĩa khi nhúng.

**Thành viên 2 — Phạm Khánh Linh**
- **Loại chiến lược:** Sentence (built-in, `max_sentences_per_chunk=4`)
- **Mô tả & lý do chọn:** Giữ trọn câu — hợp với văn bản quy định vì mỗi câu luật thường là một điều kiện/quy tắc hoàn chỉnh, không muốn cắt đứt giữa chừng như FixedSize.

**Thành viên 3 — Nguyễn Thanh Phúc**
- **Loại chiến lược:** FixedSize (built-in, `chunk_size=400, overlap=80`)
- **Mô tả & lý do chọn:** Dùng làm nhóm đối chứng (control) — overlap 20% để giữ ngữ cảnh qua ranh giới cắt cứng, xem chênh lệch so với 2 chiến lược "hiểu cấu trúc" ở trên.

**Thành viên 4 — Vũ Huy Hoàng** *(chunk theo heading/section — bắt buộc K3)*
- **Loại chiến lược:** Custom — `HeadingSectionChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Tài liệu `k3-academic-regulations-undergrad.md` (quy định học vụ) có cấu trúc "Article 1.", "Article 2."... rất rõ ràng (29 Article); các tài liệu khác dùng heading La Mã ("I. PURPOSES") hoặc chữ cái ("A. FINANCIAL REGULATIONS..."). Chunker tách theo đúng các heading này thay vì cắt cứng theo ký tự, giữ trọn nội dung một điều/mục trong một chunk.
- **Code snippet:**
```python
class HeadingSectionChunker:
    HEADING_PATTERN = re.compile(
        r"^(Article\s+\d+\.|[IVXLC]{1,5}\.\s+[A-Z]|[A-Z]\.\s{1,4}[A-Z]{2,})"
    )

    def chunk(self, text: str) -> list[str]:
        lines = text.split("\n")
        chunks, current = [], []
        for line in lines:
            if self.HEADING_PATTERN.match(line.strip()) and current:
                chunks.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            chunks.append("\n".join(current).strip())
        if len(chunks) <= 1:
            return RecursiveChunker(chunk_size=500).chunk(text)  # fallback nếu văn bản không có heading
        return [c for c in chunks if c]
```

**Thành viên 5 — Nguyễn Văn Phong**
- **Loại chiến lược:** Custom — `ClauseChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Tài liệu học phí/thư viện có nhiều điều khoản đánh số kiểu "1.1", "2.3" (mức phí, mức phạt cụ thể). Tách theo đúng các clause này cho granularity mịn hơn `HeadingSectionChunker` (1 chunk = 1 điều khoản con thay vì cả Article/section). Có fallback về `RecursiveChunker` cho tài liệu không có đánh số clause (vd. trang học bổng).

### So Sánh Giữa Các Thành Viên

> Điểm chấm theo `docs/SCORING.md` (2/1/0 mỗi câu) trên đúng 5 câu hỏi Phần 3, đối chiếu bằng cụm từ chính xác trích từ nguồn thay vì chấm cảm tính. Script: `scripts/score_benchmark.py`.

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Lê Thị Yến Nhi | Recursive (400) | **8** | Q1/Q3/Q4/Q5 đạt tuyệt đối (rank-1 + agent trả lời đúng, đầy đủ) — chunk theo đoạn văn tự nhiên nên câu trả lời trích xuất không bị đứt | Q2 (tần suất đóng học phí) miss — chunk đúng ("twice/year") không lọt top-3, bị 3 chunk khác về số tiền/chiết khấu học phí lấn hạng |
| Vũ Huy Hoàng | HeadingSectionChunker (custom) | **7** | Q3/Q5 tuyệt đối; recall tốt nhất nhóm — cả 5/5 câu đều tìm đúng chunk (Q4 rank-2, còn lại rank-1); giữ trọn 1 Article/section = dễ truy vết nguồn | Q1/Q2/Q4 dừng ở 1đ vì chunk theo cả Article dài (2500-3200 ký tự), câu chứa số liệu cụ thể nằm sâu quá xa đầu chunk để lọt vào phần trích xuất; tài liệu staff (`k3-library-management-regulation`) đứng hạng 2 nếu KHÔNG lọc metadata — rủi ro rò rỉ audience cao nhất nhóm |
| Nguyễn Thanh Phúc | FixedSize (400/80) | **7** | Q1/Q3/Q4 đạt tuyệt đối sau khi mở rộng ngưỡng trích xuất; baseline đơn giản vẫn theo kịp 2 chiến lược "hiểu cấu trúc" | Q2 miss hẳn (không chunk nào chứa "twice/year" lọt top-3); Q5 đúng chunk nhưng không ở rank-1 |
| Phạm Khánh Linh | Sentence (4 câu/chunk) | 6 | Q1/Q4 đạt tuyệt đối; retrieval tìm đúng chunk khá tốt (Q2/Q5 rank-2) | Q3 miss hẳn (chunk dạng bảng "Policy / Borrowed items..." không khớp cụm từ chấm điểm dù đúng nội dung) |
| Nguyễn Văn Phong | ClauseChunker (custom) | 6 | Q3/Q5 tuyệt đối; granularity mịn giúp câu trả lời phí/mức phạt chính xác từng điều khoản | Q1 vẫn miss hoàn toàn — câu định nghĩa "50 hours" nằm trong prose của Article 4, không có số clause "N.N" riêng nên ClauseChunker không tách được thành chunk riêng, thua chunk tài chính có clause đánh số dày đặc chứa cùng từ khoá "credit" |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **Recursive (Nhi, 8/10)** tốt nhất — đạt tuyệt đối 4/5 câu, chỉ thua đúng 1 câu (Q2, giới hạn dữ liệu chung cho cả nhóm, xem Phần 4). Lý do: chunk theo ranh giới đoạn văn tự nhiên (`\n\n`/`\n`) vừa giữ trọn ngữ nghĩa một ý/điều khoản — đủ ngắn để câu trả lời trích xuất luôn chạm tới câu chứa số liệu — vừa không cần regex tinh chỉnh riêng cho từng định dạng tài liệu như Heading/Clause. **Heading (Hoàng, 7/10)** có recall cao nhất nhóm (5/5 câu tìm đúng chunk) nhưng hay dừng ở 1đ vì chunk theo cả Article dài, số liệu cụ thể nằm sâu bên trong. **FixedSize (Phúc, 7/10)** bất ngờ theo sát top đầu sau khi mở rộng ngưỡng trích xuất — cắt cứng ký tự hoá ra ít ảnh hưởng hơn dự kiến vì phần đầu chunk bị cắt dở thường chỉ là vài ký tự thừa, không mất hẳn câu quan trọng. Sentence và Clause (6/10) đều vướng đúng 1 điểm yếu cấu trúc riêng (chunk dạng bảng / thiếu số clause cho câu định nghĩa) khó sửa chỉ bằng tinh chỉnh tham số.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy (`scripts/member_strategies.py`).

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | What is the definition of an academic credit in terms of study hours for undergraduate students? | 1 credit = 50 hours of study (contact hours, tutorials, self-managed study, experiential learning, assessments, exams). | `k3-academic-regulations-undergrad` — Article 4. Course and Credit |
| 2 | How many times per year do students pay tuition fees? | Twice a year, at the beginning of each main semester, per VinUni's annual announced schedule. | `k3-financial-regulations-tariff` — mục Payment deadline |
| 3 | How many items can an undergraduate student borrow from the library at once, and for how long? | Tối đa 3 tài liệu, 2 tuần/tài liệu; gia hạn 1 lần thêm 1 tuần nếu không quá hạn và không ai khác yêu cầu. | `k3-library-borrow-request-undergrad` |
| 4 | Are first-year students required to live in the VinUni dormitory? | Có — bắt buộc với mọi sinh viên năm nhất (trừ trường hợp đặc biệt được duyệt). | `k3-residential-life-guideline` — II. Scope / III.1 Community Principles |
| 5 | What must a student do to keep their scholarship for the whole duration of study? | Đáp ứng điều kiện duy trì học bổng tối thiểu của trường (học lực, hoạt động ngoại khoá...); học bổng áp dụng suốt thời gian học nếu đạt điều kiện. | `k3-undergrad-scholarships` |

Câu 3 **bắt buộc dùng `metadata_filter={"audience": "student"}`** (yêu cầu K3) — tránh để `k3-library-management-regulation` (tài liệu nội bộ thư viện, `audience=staff`) lẫn vào kết quả.

> Câu 1 đã được viết lại 1 lần so với bản nháp đầu ("How many hours... credit... equivalent to?" → "What is the definition of an academic credit in terms of study hours...") sau khi phát hiện bản gốc quá ngắn/nhập nhằng khiến embedding nhầm sang nghĩa "credit" tài chính ở tài liệu học phí. Gold answer và corpus giữ nguyên — chỉ diễn đạt lại câu hỏi cho rõ ý, không tiết lộ vị trí câu trả lời.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0). Chấm bằng cách đối chiếu cụm từ chính xác từ nguồn (`scripts/score_benchmark.py`), không chấm cảm tính.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Credit = 50 hours | Recursive, Sentence, FixedSize (cả 3 đạt 2đ) | Có ở 4/5 chiến lược (Heading rank-1 nhưng answer thiếu, Clause **không**) | Sau khi viết lại câu hỏi rõ nghĩa hơn + mở rộng ngưỡng trích xuất, 3/5 chiến lược đạt tuyệt đối — chỉ Clause vẫn miss vì mảnh clause quá nhỏ, mất ngữ cảnh câu định nghĩa |
| 2 | Đóng học phí 2 lần/năm | Heading, Sentence, Clause (1đ — **chưa chiến lược nào đạt 2đ**) | Có ở 3/5 chiến lược | Câu khó nhất trong bộ 5 câu — câu trả lời hay lẫn với thông tin số tiền/chiết khấu học phí thay vì tần suất đóng; đã thử 8 cách diễn đạt lại câu hỏi và mở rộng ngưỡng trích xuất, không chiến lược nào giải quyết trọn vẹn được — coi là giới hạn thật của corpus/embedding, không phải lỗi implement |
| 3 | Mượn tối đa 3 tài liệu/2 tuần | Recursive, FixedSize, Heading, Clause (cả 4 đạt 2đ) | Có ở **4/5** chiến lược (Sentence **không** — chunk rank=None) | Câu dễ nhất về nội dung — câu trả lời nằm trọn 1 câu duy nhất trong nguồn; chỉ Sentence miss hẳn vì chunk dạng bảng "Policy/Borrowed items..." không khớp cụm từ chấm điểm dù nội dung đúng |
| 4 | Năm nhất bắt buộc ở KTX | Recursive, Sentence, FixedSize (cả 3 đạt 2đ) | Có ở cả 5 chiến lược | Heading/Clause tìm đúng chunk nhưng không ở rank-1 (Heading) hoặc answer 2-3-câu-đầu chưa chạm câu chứa "required to reside" (Clause) |
| 5 | Duy trì học bổng | Recursive, Heading, Clause (cả 3 đạt 2đ) | Có ở cả 5 chiến lược | Sentence/Fixed tìm ra chunk đúng nhưng không ở rank-1 (bị `k3-financial-regulations-tariff` nói về "Talent Scholarship" khác lấn hạng 1) |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, rõ nhất ở Câu 3. Kiểm tra riêng (không dùng filter, lấy top-8): tài liệu `k3-library-management-regulation` (audience=staff) đứng **hạng 2/8** ở Heading (Hoàng) — chỉ sau đúng 1 bậc so với chunk trả lời đúng; **hạng 4/8** ở Sentence (Linh); **hạng 5/8** ở FixedSize (Phúc); **hạng 8/8** (chót nhưng vẫn có mặt) ở Recursive (Nhi); và **không lọt top-8** ở Clause (Phong) — trường hợp an toàn duy nhất. Kết luận: mức độ cần filter phụ thuộc vào chiến lược chunking — chunk theo heading/section rộng dễ làm tài liệu sai audience "trồi" lên gần top-k hơn vì mỗi chunk bao trọn ngữ cảnh chủ đề "thư viện" nói chung, trong khi granularity mịn hơn (clause) cô lập nhiễu audience tốt nhất.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Phân tích lỗi (Failure Analysis — Bài tập 3.5)

Quá trình benchmark trải qua 3 vòng: vòng 1 phát hiện lỗi, vòng 2 sửa lỗi generation + tinh chỉnh câu hỏi, vòng 3 nới ngưỡng trích xuất — cả ba đều ghi lại dưới đây vì đều là bài học thật, không chỉ báo cáo kết quả cuối.

**Lỗi 1 (đã sửa) — `llm_fn` cắt cụt câu trả lời tại heading.** Ở vòng chạy đầu tiên, câu trả lời của agent nhiều lần chỉ còn đúng 1 dòng heading (vd. "Credits", "Article 11. Study Load", "II. Scope") dù chunk truy xuất được **đúng** và đủ thông tin. Nguyên nhân: `extractive_llm` (`scripts/member_strategies.py`) cô lập "chunk đầu tiên" bằng cách cắt tại dấu `"\n\n"` đầu tiên trong context — nhưng nhiều chunk có cấu trúc "Tiêu đề\n\nNội dung..." nên hàm chỉ lấy được dòng tiêu đề rồi dừng. Đây là lỗi ở tầng **generation**, không phải retrieval — minh hoạ rõ 2 giai đoạn RAG có thể lỗi độc lập nhau. **Đã sửa**: flatten toàn bộ context thành 1 dòng trước khi tách câu bằng regex `[.!?]`, không còn phụ thuộc cấu trúc `"\n\n"` nội bộ của chunk.

**Lỗi 1b (đã cải thiện) — giới hạn "2 câu đầu" vẫn quá chặt.** Sau khi sửa lỗi trên, câu trả lời không còn dừng ở heading trơ trụi, nhưng vẫn dừng ở đúng 2 câu — với `HeadingSectionChunker` (chunk theo cả Article, dài 2500-3200 ký tự) hay `ClauseChunker`, câu chứa số liệu cụ thể thường là câu thứ 3-4 trong chunk, nên vẫn bị cắt trước khi tới. **Đã cải thiện**: đổi từ giới hạn cứng "2 câu" sang ngân sách ~400 ký tự (dừng khi thêm câu tiếp theo sẽ vượt ngưỡng) — gần với cách một LLM thật sẽ tóm tắt đủ ý mà vẫn ngắn gọn, không phải chép nguyên si cả chunk. Sau 2 lần sửa, nhiều câu trả lời tăng điểm (Linh Q1/Q4, Phúc Q1/Q3/Q4) mà không đổi corpus/chiến lược chunking gì cả — chứng tỏ các lỗi này oan uổng, không phản ánh chất lượng retrieval thật. **Giới hạn còn lại**: với Heading (chunk quá dài, câu đích ở vị trí 1300-3100 ký tự) tăng ngân sách trích xuất thêm nữa sẽ đồng nghĩa trả về gần nguyên chunk — không còn là "trích xuất" nữa, nên nhóm dừng ở 400 ký tự và chấp nhận đây là nhược điểm thật của chunk theo Article dài.

**Lỗi 2 (đã cải thiện một phần) — Câu 1 nhầm giữa 2 nghĩa của từ "credit".** Corpus dùng từ **"credit"** với 2 nghĩa khác nhau: (a) tín chỉ học thuật (`k3-academic-regulations-undergrad`, Article 4) và (b) một loại phí/khoản mục tài chính (`k3-financial-regulations-tariff`: "Credits are understood as subjects that have determined a specific number of academic credits..."). Câu hỏi gốc quá ngắn ("How many hours... credit... equivalent to?") khiến embedding lẫn sang nghĩa tài chính ở 4/5 chiến lược. **Đã cải thiện**: viết lại câu hỏi rõ nghĩa hơn ("What is the definition of an academic credit in terms of study hours...") — gold answer và corpus giữ nguyên, chỉ diễn đạt lại — giúp 4/5 chiến lược tìm đúng chunk (rank-1). Riêng `ClauseChunker` (Phong) **vẫn miss** vì cách tách theo clause "N.N" làm câu định nghĩa ("A credit is equivalent to 50 hours...") nằm trong prose không có số clause riêng, bị chunk khác (financial, cũng đánh số clause) lấn át. Đây là giới hạn thật của chiến lược, không sửa thêm được chỉ bằng cách đổi câu hỏi.

**Lỗi còn tồn tại — Câu 2 (tần suất đóng học phí) vẫn khó nhất.** Đã thử 8 cách diễn đạt lại câu hỏi (xem lịch sử thử nghiệm), không cải thiện đáng kể — tài liệu `k3-financial-regulations-tariff` có quá nhiều câu "đậm đặc" số tiền/VND làm lấn át câu duy nhất nói về tần suất ("Payment deadline: Students will pay tuition fees (02) twice/year..."). Đây là giới hạn thật của mock/local embedder với văn bản tài chính dày đặc số liệu, không phải lỗi implement.

**Đề xuất cải thiện tiếp theo (nếu làm lại):**
- Thêm metadata `topic` phân biệt "academic" vs "financial" ngay từ lúc ingest để giảm nhập nhằng nghĩa từ khoá trong domain hẹp.
- Với văn bản dày đặc số liệu (tài chính), cân nhắc chunk theo câu đơn (SentenceChunker với max_sentences nhỏ) thay vì đoạn văn dài, để câu "tần suất đóng" không bị chìm giữa các câu "số tiền".

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. Qua 3 vòng sửa lỗi generation + tinh chỉnh câu hỏi, điểm cải thiện rõ rệt cho **mọi thành viên** mà **không đổi corpus hay chunking**: Nhi 6→8, Hoàng 6→7, Phúc 4→7, Linh 4→6, Phong giữ 6 — cho thấy retrieval quality không chỉ phụ thuộc chunking, mà cách đặt câu hỏi và cách trích xuất câu trả lời ảnh hưởng ngang hàng, đôi khi còn hơn.
> 2. **Recursive (Nhi) và Heading/FixedSize (Hoàng, Phúc) hội tụ về nhóm dẫn đầu (7-8/10)** sau khi loại bỏ nhiễu do lỗi generation, thay vì cách biệt rõ như tưởng ban đầu — chunk theo cấu trúc "thông minh" (đoạn văn/Article) vẫn nhỉnh hơn nhưng khoảng cách với cắt cứng ký tự (FixedSize) hẹp lại đáng kể khi tầng generation không còn là điểm nghẽn.
> 3. Metadata filter `audience` không "vô thưởng vô phạt" — mức độ cần thiết phụ thuộc chiến lược: HeadingSectionChunker khiến tài liệu staff xém lọt top-3 (hạng 2/8), trong khi RecursiveChunker tự nhiên đẩy nó ra xa top-8.
> 4. Không phải mọi lỗi đều sửa được: Câu 1 cải thiện được (nhập nhằng do diễn đạt câu hỏi + tầng generation quá chặt), Câu 2 thì không dù đã thử 8 cách diễn đạt (nhiễu do bản chất dữ liệu tài chính dày số liệu) — biết phân biệt "lỗi implement/config sửa được" và "giới hạn dữ liệu thật" quan trọng hơn là cố ép điểm bằng mọi giá.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ 7 tài liệu, cùng 5 câu hỏi, điểm cuối dao động 6-8/10 — hẹp hơn nhiều so với lần chạy đầu (4-6/10) sau khi loại bỏ 2 lỗi hệ thống ở tầng generation. Phần chênh lệch còn lại giữa các chiến lược (Recursive 8 vs Sentence/Clause 6) mới thực sự phản ánh khác biệt do chunking, không còn bị lỗi implementation che lấp — bài học lớn nhất là nên tách bạch rạch ròi 2 tầng retrieval và generation khi debug, thay vì gộp chung "điểm thấp = retrieval tệ".

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Sẽ tách riêng field `topic` (academic/financial/library/housing) cho từng chunk ngay lúc ingest thay vì chỉ dựa vào `category` cấp tài liệu, để giảm nhập nhằng loại lỗi như Câu 1. Với `ClauseChunker`, sẽ thêm bước gộp câu định nghĩa/prose không có số clause riêng vào clause gần nhất thay vì để lạc trong fallback `RecursiveChunker` cỡ lớn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **38 / 40** |
