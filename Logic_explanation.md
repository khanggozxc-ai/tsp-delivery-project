# Nhật Ký Đồ Án TSP

> **Note:** File này dùng để cập nhật liên tục!

---

## 1. Tổng Quan Dự Án
Đồ án xây dựng hệ thống tối ưu hóa lộ trình giao hàng thông minh, giải quyết bài toán kinh điển Traveling Salesman Problem(TSP)

## 1.1 Quy trình Pipeline

1. **Uploads Data**: Tiếp nhận tọa độ khách hàng qua file '.csv' hoặc nhận gián tiếp
2. **Preprocessing**: Tính toán ma trận khoảng cách(*distance_matrix*) bằng công thức *Haversine*
3. **Core Engine**: Thực thi thuật toán tối ưu
4. **Presentation**: Trực quan hóa lộ trình qua giao diện *streamlit* 

## 2. Các thuật toán đã triển khai

| Thuật toán | Cơ chế hoạt động | Ưu điểm | Nhược điểm |
| :--- | :--- | :--- | :--- |
| **Brute Force** | Thử tất cả hoán vị $(n-1)!$ | Kết quả tối ưu nhất | Rất chậm khi $n > 10$ |
| **Nearest Neighbor** | Chọn điểm gần nhất (Tham lam) | Tốc độ cực nhanh | Không đảm bảo tối ưu |
| **Genetic Algorithm** | Lai ghép, đột biến quần thể | Tốt cho bài toán lớn | Cần tinh chỉnh tham số |
| **2-opt** | Hoán đổi chéo đường đi | Cải thiện kết quả nhanh | Dễ bị kẹt ở cực tiểu |

## 3. Kiến thức cốt lỗi

### Ngày 1: NỀN TẢNG & GIẢI THUẬT

1. **Haversine Formula**: Công thức tính khoảng cách ngắn nhất giữa hai điểm trên bề mặt cầu dựa trên vĩ độ ($\phi$) và kinh độ ($\lambda$). 

Giả sử có 2 điểm trên bản đồ với tọa độ là $(\phi_1, \lambda_1)$ và $(\phi_2, \lambda_2)$ (đơn vị Radian):

1.1 **Tính độ lệch:**
   $$\Delta\phi = \phi_2 - \phi_1$$
   $$\Delta\lambda = \lambda_2 - \lambda_1$$

1.2 **Tính giá trị trung gian $a$:**
   $$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2\left(\frac{\Delta\lambda}{2}\right)$$

1.3 **Tính góc ở tâm $c$:**
   $$c = 2 \cdot \operatorname{asin}\left(\sqrt{\min(1.0, a)}\right)$$

1.4 **Khoảng cách thực tế $d$:**
   $$d = R \cdot c$$
   *(Trong đó $R \approx 6371$ km là bán kính Trái Đất).*

---

2. **Time Complexity**: Độ phức tạp của thuật toán == đo sức chịu đựng của thuật toán.

- Brute Force $O(n!)$: Tăng trưởng theo hàm mũ. VỚi mỗi khách hàng thêm vào, số lộ trình cần kiểm tra sẽ nhân theo cấp số nhân => Chỉ nên áp dụng cho tập tài liệu nhỏ (n < 10).

- Nearest Neighbor $O(n^2)$: Tăng trưởng theo diện tích. Nếu số khách hàng gấp đôi, thời gian tính toán tăng gấp 4 lần => Hiệu năng tốt cho các bài toán lớn.

---

3. **Input validation**: Không cho phép hệ thống nhận dữ liệu 'rác' gây ra crash hoặc kết quả vô lý

- Các chốt chặn:

+ Vĩ độ: Phải trong khoảng [-90, 90].

+ Kinh độ: Phải trong khoảng [-180, 180].

+ Số lượng điểm: Kiểm tra, tối thiểu 2 điểm mới có thể tạo lộ trình.

---

## 4. Chức năng các file trọng tâm

* `app.py`: Giao diện chính, hiện bản đồ và các nút bấm.
* `requirements.txt`: Danh sách thư viện cần cài để chạy máy.
* `algorithms/brute_force.py`: Thuật toán tìm đường ngắn nhất tuyệt đối.
* `algorithms/nearest_neighbor.py`: Thuật toán tìm đường tham lam siêu tốc.
* `services/distance_service.py`: Bộ đo khoảng cách và lập ma trận vuông.

---

### Ngày 2: THUẬT TOÁN NÂNG CAO & DATABASE


CẬP NHẬT NGÀY 3 — LỊCH SỬ VÀ DASHBOARD

1. Chép các thư mục database/ và views/ vào thư mục gốc repository.
2. Thay app.py hiện tại bằng app.py trong gói này.
3. Thêm các dòng trong GITIGNORE_ADD.txt vào .gitignore.
4. Không cần cài thư viện SQLite vì sqlite3 có sẵn trong Python.
5. Chạy:
   python -m py_compile app.py
   python -m py_compile database/history_repository.py
   python -m py_compile views/history_dashboard.py
   streamlit run app.py

Chức năng:
- Lưu kết quả tối ưu vào SQLite.
- Ngăn lưu trùng cùng một kết quả.
- Dữ liệu vẫn còn sau khi khởi động lại.
- Lọc lịch sử theo thuật toán.
- Dashboard tổng hợp.
- Biểu đồ so sánh thuật toán.
- Xuất CSV.
- Xóa một bản ghi hoặc toàn bộ lịch sử.
