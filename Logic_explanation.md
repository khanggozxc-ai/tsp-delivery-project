# Nhật Ký Đồ Án TSP

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

## 4. Cấu trúc thư mục và chức năng

```text
tsp-delivery-project/
│
├── app.py                      # Giao diện chính 
├── requirements.txt            # Danh sách thư viện cần cài để chạy máy
├── LOGIC_EXPLANATION.md        # File tài liệu giải thích logic bồ đang đọc
│
├── algorithms/                 # BỘ NÃO XỬ LÝ (Chứa các thuật toán tìm đường)
│   ├── brute_force.py          # Thuật toán Vét cạn - Thử mọi cách để tìm đường ngắn nhất tuyệt đối
│   ├── nearest_neighbor.py     # Thuật toán Hàng xóm gần nhất - Điểm nào gần thì đi trước 
│   ├── genetic_algorithm.py    # Thuật toán Di truyền (GA) - Giải bài toán lớn bằng cách tiến hóa
│   └── two_opt.py              # Thuật toán 2-opt - Gỡ rối các đoạn đường bị chéo nhau
│
├── services/                   # BỘ CÔNG CỤ TRỢ GIÚP (Tính toán các thông số phụ)
│   ├── distance_service.py     # Tính khoảng cách giữa các điểm & Lập ma trận khoảng cách
│   ├── cost_service.py         # Tính tiền xăng/chi phí dựa trên số km
│   └── route_service.py          # Tính thời gian dự kiến xe chạy đến nơi (Phút)
│
└── data/                       # KHO DỮ LIỆU ĐẦU VÀO
    ├── locations_5.csv         # Dữ liệu nhỏ (5 khách hàng) - Dùng để test Vét cạn
    ├── locations_10.csv        # Dữ liệu vừa (10 khách hàng)
    └── locations_20.csv        # Dữ liệu lớn (20 khách hàng trở lên) - Dùng cho GA và 2-opt 


