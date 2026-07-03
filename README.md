# Bài toán tối ưu lộ trình giao hàng bằng TSP

Ứng dụng minh họa việc áp dụng các thuật toán giải **Traveling Salesman Problem (TSP)** để đề xuất thứ tự giao hàng cho một phương tiện đi qua nhiều địa điểm đã biết trước.

Ứng dụng hỗ trợ nhập danh sách địa điểm, tính khoảng cách theo mạng lưới đường giao thông, chạy nhiều thuật toán TSP, hiển thị tuyến đường trên bản đồ, ước tính ETA và chi phí, đồng thời lưu lịch sử kết quả bằng SQLite để phục vụ so sánh.

---

## 1. Bài toán được giải quyết

Bài toán xét trường hợp một cửa hàng hoặc kho cần giao hàng đến nhiều địa điểm bằng **một phương tiện**.

### Đầu vào

- Một điểm xuất phát.
- Danh sách các địa điểm cần đi qua.
- Tọa độ của từng địa điểm.
- Thời gian phục vụ tại mỗi địa điểm.
- Loại phương tiện định tuyến.
- Chi phí trung bình trên mỗi kilomet.
- Loại lộ trình mở hoặc khép kín.

### Mục tiêu chính

Ứng dụng tìm thứ tự ghé thăm các địa điểm sao cho **tổng quãng đường đường bộ được giảm xuống**.

Chi phí được ước tính theo công thức:

```text
Chi phí dự kiến = Tổng quãng đường × Chi phí mỗi kilomet
```

Vì vậy, trong mô hình hiện tại, giảm quãng đường cũng giúp giảm chi phí vận hành ước tính.

> Thời gian di chuyển và ETA được dùng để đánh giá lộ trình. Thuật toán hiện tại tối ưu theo quãng đường, chưa tối ưu trực tiếp theo giao thông thời gian thực.

---

## 2. Chức năng chính

### Quản lý địa điểm

- Tải danh sách địa điểm từ file CSV.
- Khôi phục dữ liệu mẫu.
- Thêm địa điểm mới.
- Sửa trực tiếp dữ liệu trong bảng.
- Xóa địa điểm.
- Kiểm tra tên, mã, tọa độ và thời gian phục vụ.

### Tối ưu lộ trình

- Chọn điểm xuất phát.
- Chọn lộ trình mở hoặc khép kín.
- Chọn phương tiện định tuyến:
  - Xe giao hàng.
  - Xe đạp.
  - Đi bộ.
- Thiết lập chi phí mỗi kilomet.
- Thiết lập giờ xuất phát.
- Chạy và so sánh nhiều thuật toán.

### Hiển thị kết quả

- Thứ tự di chuyển.
- Tổng quãng đường đường bộ.
- Thời gian xử lý thuật toán.
- Chi phí giao hàng dự kiến.
- Tổng thời gian dự kiến.
- Thời gian di chuyển.
- Tốc độ trung bình của tuyến.
- Bảng ETA theo từng điểm.
- Biểu đồ hội tụ của Genetic Algorithm.
- Mức cải thiện của 2-opt.
- Bản đồ tuyến đường bám theo mạng lưới giao thông.

### Lịch sử và dashboard

- Lưu kết quả vào SQLite.
- Ngăn lưu trùng cùng một kết quả.
- Dữ liệu vẫn còn sau khi khởi động lại ứng dụng.
- Lọc lịch sử theo thuật toán.
- Thống kê số lần chạy, quãng đường, chi phí và thời gian xử lý.
- So sánh các thuật toán bằng bảng và biểu đồ.
- Xuất lịch sử ra CSV.
- Xóa một bản ghi hoặc toàn bộ lịch sử.

---

## 3. Các thuật toán được sử dụng

| Thuật toán | Đặc điểm | Phạm vi phù hợp |
|---|---|---|
| Brute Force | Kiểm tra toàn bộ hoán vị và cho nghiệm tối ưu trong phạm vi đã xét | Dữ liệu nhỏ, tối đa 10 địa điểm trong ứng dụng |
| Nearest Neighbor | Luôn chọn điểm chưa đi gần nhất | Chạy nhanh, phù hợp dữ liệu lớn hơn |
| Nearest Neighbor + 2-opt | Cải thiện nghiệm Nearest Neighbor bằng cách đảo các đoạn đường | Cân bằng giữa tốc độ và chất lượng nghiệm |
| Genetic Algorithm | Tìm kiếm nghiệm gần tối ưu dựa trên quần thể, chọn lọc, lai ghép và đột biến | Dữ liệu vừa và lớn |
| Genetic Algorithm + 2-opt | Dùng 2-opt để tiếp tục cải thiện nghiệm từ Genetic Algorithm | Chất lượng nghiệm tốt hơn trong nhiều trường hợp |

---

## 4. Công nghệ sử dụng

- Python
- Streamlit
- Pandas
- NumPy
- Folium
- streamlit-folium
- Requests
- SQLite
- Pytest
- OpenRouteService
- OpenStreetMap

SQLite đã có sẵn trong Python thông qua thư viện `sqlite3`, không cần cài đặt riêng.

---

## 5. Cấu trúc thư mục

```text
tsp-delivery-project/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── .streamlit/
│   └── secrets.toml
│
├── algorithms/
│   ├── brute_force.py
│   ├── nearest_neighbor.py
│   ├── genetic_algorithm.py
│   └── two_opt.py
│
├── services/
│   ├── delivery_service.py
│   ├── distance_service.py
│   └── road_routing_service.py
│
├── database/
│   ├── __init__.py
│   └── history_repository.py
│
├── views/
│   ├── __init__.py
│   └── history_dashboard.py
│
├── utils/
│   └── validators.py
│
├── tests/
│   ├── test_algorithms.py
│   ├── test_day2_algorithms.py
│   └── test_history_repository.py
│
└── data/
    ├── locations_5.csv
    ├── locations_10.csv
    ├── locations_20.csv
    └── optimization_history.db
```


---

## 6. Yêu cầu môi trường

- Python 3.10 trở lên.
- Git.
- Kết nối Internet để gọi OpenRouteService.
- API key của OpenRouteService.

Kiểm tra Python:

```powershell
python --version
```

Kiểm tra Git:

```powershell
git --version
```

---

## 7. Tải mã nguồn

Mở PowerShell hoặc terminal và chạy:

```powershell
git clone <https://github.com/khanggozxc-ai/tsp-delivery-project.git>
cd tsp-delivery-project
```


---

## 8. Tạo môi trường ảo

### Windows PowerShell

```powershell
python -m venv .venv
```

Kích hoạt:

```powershell
.\.venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Sau khi kích hoạt, terminal sẽ có tiền tố:

```text
(.venv)
```

### macOS hoặc Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 9. Cài đặt thư viện

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Kiểm tra nhanh:

```powershell
python -c "import streamlit, pandas, numpy, folium, requests; print('LIBRARIES OK')"
```

Kết quả mong đợi:

```text
LIBRARIES OK
```

---

## 10. Cấu hình OpenRouteService API key

Tạo thư mục:

```text
.streamlit
```

Trong thư mục đó, tạo file:

```text
secrets.toml
```

Cấu trúc cuối cùng:

```text
.streamlit/
└── secrets.toml
```

Nội dung file:

```toml
ORS_API_KEY = "
eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImYzOWM1M2UyM2IxYzQ3ZmRhYTEzMzRjMGUwYjdhZGFiIiwiaCI6Im11cm11cjY0In0="
"
```

Kiểm tra file TOML:

```powershell
python -c "import tomllib; d=tomllib.load(open('.streamlit/secrets.toml','rb')); print('ORS KEY OK' if d.get('ORS_API_KEY') else 'ORS KEY MISSING')"
```

Kết quả mong đợi:

```text
ORS KEY OK
```

---

## 11. Cấu hình `.gitignore`

Bảo đảm `.gitignore` có các dòng:

```gitignore
.venv/
__pycache__/
.pytest_cache/
.streamlit/secrets.toml

data/optimization_history.db
data/optimization_history.db-shm
data/optimization_history.db-wal
```

Kiểm tra API key đã được Git bỏ qua:

```powershell
git check-ignore .streamlit/secrets.toml
```

Kết quả mong đợi:

```text
.streamlit/secrets.toml
```

---

## 12. Chạy ứng dụng

Tại thư mục chứa `app.py`, chạy:

```powershell
streamlit run app.py
```

Ứng dụng thường được mở tại:

```text
http://localhost:8501
```

Dừng ứng dụng bằng:

```text
Ctrl + C
```

---

## 13. Định dạng file CSV

File CSV cần có năm cột:

```text
id,name,latitude,longitude,service_time
```

Ví dụ:

```csv
id,name,latitude,longitude,service_time
0,Kho trung tâm,10.762622,106.660172,0
1,Khách hàng A,10.771200,106.671500,5
2,Khách hàng B,10.754800,106.681300,10
3,Khách hàng C,10.748500,106.654100,7
```

### Ý nghĩa các cột

| Cột | Ý nghĩa |
|---|---|
| `id` | Mã duy nhất của địa điểm |
| `name` | Tên địa điểm |
| `latitude` | Vĩ độ, từ -90 đến 90 |
| `longitude` | Kinh độ, từ -180 đến 180 |
| `service_time` | Thời gian phục vụ tại điểm, tính bằng phút |

Yêu cầu dữ liệu:

- Không để trống tên địa điểm.
- Không dùng ID trùng nhau.
- Không dùng tên trùng nhau.
- Không dùng tọa độ trùng nhau.
- Thời gian phục vụ không được âm.
- Nên đặt kho trung tâm có `id = 0`.

---

## 14. Hướng dẫn sử dụng giao diện

### Bước 1: quản lý địa điểm

Mở tab **Quản lý địa điểm**.

Người dùng có thể:

1. Tải file CSV.
2. Dùng dữ liệu mẫu.
3. Thêm địa điểm bằng biểu mẫu.
4. Sửa dữ liệu trực tiếp trong bảng.
5. Nhấn **Lưu thay đổi danh sách**.

### Bước 2: cấu hình lộ trình

Mở tab **Tối ưu lộ trình** và thiết lập:

1. Điểm xuất phát.
2. Thuật toán.
3. Loại lộ trình.
4. Phương tiện định tuyến.
5. Chi phí mỗi kilomet.
6. Giờ xuất phát.
7. Các tham số Genetic Algorithm nếu sử dụng GA.

### Bước 3: chọn loại lộ trình

- **Khép kín:** phương tiện quay lại điểm xuất phát.
- **Mở:** phương tiện kết thúc tại địa điểm cuối cùng.

### Bước 4: chạy thuật toán

Nhấn:

```text
Tối ưu lộ trình
```

Ứng dụng sẽ thực hiện:

```text
Địa điểm
→ Ma trận khoảng cách và thời gian đường bộ
→ Thuật toán TSP
→ Tuyến đường GeoJSON
→ ETA và chi phí
→ Bản đồ và kết quả
```

### Bước 5: xem kết quả

Kiểm tra:

- Tổng quãng đường.
- Chi phí dự kiến.
- Thời gian xử lý.
- Tổng thời gian dự kiến.
- Thứ tự địa điểm.
- Bảng ETA.
- Bản đồ tuyến đường.
- Biểu đồ hội tụ nếu dùng Genetic Algorithm.
- Mức cải thiện nếu dùng 2-opt.

### Bước 6: lưu lịch sử

Nhấn:

```text
Lưu kết quả vào lịch sử
```

Nếu kết quả đã tồn tại, ứng dụng sẽ thông báo và không tạo bản ghi trùng.

### Bước 7: xem dashboard

Mở tab **Lịch sử & thống kê** để:

- Lọc theo thuật toán.
- Xem danh sách các lần chạy.
- So sánh quãng đường và thời gian xử lý.
- Tải dữ liệu CSV.
- Xóa bản ghi.
- Xóa toàn bộ lịch sử.

---

## 15. Tham số Genetic Algorithm đề xuất

Cấu hình mặc định:

```text
Kích thước quần thể: 100
Số thế hệ: 300
Tỷ lệ lai ghép: 0.8
Tỷ lệ đột biến: 0.05
Kích thước tournament: 5
Số cá thể elite: 2
Random seed: 42
```

Giải thích ngắn:

- Tăng số thế hệ có thể cải thiện nghiệm nhưng tăng thời gian chạy.
- Tăng kích thước quần thể giúp đa dạng nghiệm nhưng tốn nhiều tài nguyên hơn.
- Random seed giúp tái lập kết quả trong cùng điều kiện.

---

## 16. Chạy kiểm thử

Kiểm tra cú pháp:

```powershell
python -m compileall app.py algorithms services database views utils
```

Chạy toàn bộ test:

```powershell
pytest -v
```

Chạy riêng phần lịch sử:

```powershell
pytest tests\test_history_repository.py -v
```

Kết quả không được có:

```text
FAILED
ERROR
```

---

## 17. Kiểm tra nhanh 

### Với 5 địa điểm

Chạy:

- Brute Force.
- Nearest Neighbor.
- Nearest Neighbor + 2-opt.
- Genetic Algorithm.
- Genetic Algorithm + 2-opt.

### Với 10 địa điểm

Chạy:

- Nearest Neighbor.
- Nearest Neighbor + 2-opt.
- Genetic Algorithm.
- Genetic Algorithm + 2-opt.

Có thể chạy Brute Force nhưng thời gian sẽ tăng đáng kể.

### Với 20 địa điểm

Chạy:

- Nearest Neighbor.
- Nearest Neighbor + 2-opt.
- Genetic Algorithm.
- Genetic Algorithm + 2-opt.

Không nên chạy Brute Force vì số hoán vị tăng theo cấp giai thừa.

---

## 18. Lỗi thường gặp

### `TOMLDecodeError`

Nguyên nhân: file `secrets.toml` sai cú pháp.

Cách viết đúng:

```toml
ORS_API_KEY = "API_KEY_CUA_BAN"
```

### Không tìm thấy `ORS_API_KEY`

Kiểm tra:

- File có nằm trong `.streamlit/secrets.toml` hay không.
- File có bị đặt nhầm tên thành `secrets.toml.txt` hay không.
- Đã lưu file chưa.
- Đã dừng và chạy lại Streamlit chưa.

### `ModuleNotFoundError`

Chạy:

```powershell
pip install -r requirements.txt
```

### `ImportError`

Kiểm tra các file sau tồn tại:

```text
services/delivery_service.py
services/road_routing_service.py
database/history_repository.py
views/history_dashboard.py
```

### API trả về `401`

API key không hợp lệ hoặc bị nhập sai.

### API trả về `403`

Key chưa được cấp quyền hoặc bị giới hạn.

### API trả về `429`

Đã vượt giới hạn số lần gọi API. Chờ rồi thử lại.

### Không tìm được tuyến đường

Kiểm tra:

- Tọa độ có đúng không.
- Điểm có nằm quá xa mạng lưới giao thông không.
- Thứ tự latitude và longitude có bị đảo không.
- Kết nối Internet có hoạt động không.

### `fatal: not a git repository`

Đi vào đúng thư mục repository:

```powershell
cd tsp-delivery-project
```

### Lịch sử bị lỗi hoặc cần đặt lại

Dừng ứng dụng rồi xóa file:

```text
data/optimization_history.db
```

Ứng dụng sẽ tự tạo lại database khi chạy.

---

## 19. Giới hạn hiện tại

Ứng dụng hiện được giới hạn trong phạm vi học thuật:

- Một phương tiện.
- Danh sách địa điểm cố định.
- Chưa xử lý nhiều tài xế hoặc nhiều xe.
- Chưa xử lý tải trọng phương tiện.
- Chưa xử lý khung giờ giao hàng.
- Chưa nhận đơn hàng động theo thời gian thực.
- Chưa sử dụng dữ liệu ùn tắc giao thông thời gian thực.
- Chi phí được mô hình hóa theo chi phí trung bình trên kilomet.
- ETA phụ thuộc vào dữ liệu định tuyến được API cung cấp.

Do đó, đây là **ứng dụng minh họa bài toán TSP**, không phải nền tảng điều phối quy mô lớn như các ứng dụng bản đồ hoặc giao hàng thương mại.

---

## 20. Quy trình Git 

Tạo nhánh chức năng:

```powershell
git switch -c feature/ten-chuc-nang
```

Kiểm tra thay đổi:

```powershell
git status
git diff
```

Thêm file:

```powershell
git add .
```

Kiểm tra nội dung sắp commit:

```powershell
git diff --cached
```

Commit:

```powershell
git commit -m "feat: mo ta ngan gon thay doi"
```

Push:

```powershell
git push -u origin feature/ten-chuc-nang
```

Sau đó tạo Pull Request vào nhánh chung của nhóm.

---

## 21. Checklist chạy dự án trên máy mới

```text
[ ] Đã clone repository
[ ] Đã đi vào đúng thư mục chứa app.py
[ ] Đã tạo và kích hoạt môi trường ảo
[ ] Đã cài requirements.txt
[ ] Đã tạo .streamlit/secrets.toml
[ ] ORS_API_KEY hợp lệ
[ ] secrets.toml đã được .gitignore bỏ qua
[ ] Dữ liệu CSV đúng định dạng
[ ] python -m compileall chạy thành công
[ ] pytest không có FAILED hoặc ERROR
[ ] streamlit run app.py chạy thành công
[ ] Bản đồ hiển thị tuyến đường
[ ] Có thể lưu và xem lịch sử
```

---

## 22. Mục đích học thuật

Đồ án giúp minh họa:

- Cách mô hình hóa bài toán giao hàng thành TSP.
- Sự khác nhau giữa thuật toán chính xác và thuật toán heuristic/metaheuristic.
- Ảnh hưởng của 2-opt đến chất lượng nghiệm.
- Cách sử dụng ma trận khoảng cách đường bộ.
- Cách trực quan hóa lộ trình trên bản đồ.
- Cách lưu, thống kê và so sánh kết quả thực nghiệm.

---


