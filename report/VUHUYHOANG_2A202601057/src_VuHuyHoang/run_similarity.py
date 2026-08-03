# Import hàm tính độ tương đồng của bạn
from src.chunking import compute_similarity

# Import hàm tạo vector (embedding) 
# Chú ý: Ở đây mình đang gọi _mock_embed theo cấu trúc file của bạn. 
# Nếu bài Lab yêu cầu dùng model thật (như SentenceTransformer hay OpenAI), bạn hãy thay hàm này nhé.
from src.embeddings import _mock_embed

# 1. 5 CẶP CÂU TỪ DỮ LIỆU VINUNI POLICIES:
pairs = [
    # Cặp 1 (Dự đoán: Cao - vì cùng nói về định nghĩa sinh viên full-time)
    ("A full-time student is undertaking at least 80% of a full-time load in an academic program.", 
     "To be classified as a full-time student, s/he must be enrolled in at a minimum, 80% of a normal full-time load in a regular Semester (equivalent to 12 credits)."),
    
    # Cặp 2 (Dự đoán: Cao - vì cùng nói về trợ cấp học phí 35% đến năm 2030)
    ("From 2025 to 2030, all students enrolling at VinUniversity will be granted a 35% tuition subsidy, applied for the full duration of their studies.", 
     "All Students successfully enrolled in VinUniversity until the year 2030 will receive the Educational Development Grant from the Founding Donor equivalent to 35% discount of the listed tuition fees for the entire official duration of the program (according to the standard course time designed for Students to complete the program)."),
    
    # Cặp 3 (Dự đoán: Thấp - một câu nói về phạt mượn thiết bị quá hạn, một câu về thu hồi tài liệu)
    ("Equipment overdue for more than 05 days will be considered lost, and the borrower will be charged for a replacement.", 
     "The library may recall items for maintenance or other needs."),
    
    # Cặp 4 (Dự đoán: Thấp - hoàn toàn không liên quan, thư viện và việc xin nghỉ học)
    ("Library opening hours are subject to change during exam periods, holidays, and summer break and will be posted at the main library entrance and on the library .", 
     "Students are allowed to apply for a voluntary leave of absence or withdrawal and to reserve the study results in the following cases:"),
    
    # Cặp 5 (Dự đoán: Thấp - hoàn toàn không liên quan, học bổng và an ninh ký túc xá)
    ("Provost’s Merit Scholarship: Covers 100% of tuition.", 
     "Residents should not bypass or disable residential security.")
]

# 2. Vòng lặp để tính và in ra điểm số
print("--- KẾT QUẢ ĐIỂM TƯƠNG ĐỒNG (COSINE SIMILARITY) ---")
for i, (cau_a, cau_b) in enumerate(pairs, 1):
    # Bước A: Biến chữ thành số (Vector)
    vec_a = _mock_embed(cau_a)
    vec_b = _mock_embed(cau_b)
    
    # Bước B: Tính điểm Cosine Similarity
    score = compute_similarity(vec_a, vec_b)
    
    # In kết quả
    print(f"Cặp {i}:")
    print(f"  Câu A: {cau_a}")
    print(f"  Câu B: {cau_b}")
    print(f"  => Điểm thực tế: {score:.4f}\n")