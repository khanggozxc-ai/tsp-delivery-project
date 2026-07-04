# logic_explaining.md

# Tài liệu tự học logic mã nguồn đồ án TSP Delivery Optimizer

> Vai trò của tài liệu: giúp nhóm hiểu lại bản chất vận hành của đồ án tối ưu lộ trình giao hàng bằng bài toán Traveling Salesman Problem, từ luồng dữ liệu tổng thể đến các câu lệnh lõi trong Python, Pandas, NumPy, Streamlit, SQLite và các thuật toán tối ưu.
>
> Tài liệu này được xây dựng dựa trên mã nguồn `app.py` hiện tại của đồ án.

---

# 1. Bản chất bài toán nhóm đang giải quyết

## 1.1. Tên bài toán đúng

Đồ án không nên được mô tả là một “hệ thống điều phối giao hàng quy mô lớn” như Grab hoặc Google Maps.

Cách gọi chính xác hơn:

**Ứng dụng các thuật toán giải bài toán Traveling Salesman Problem trong tối ưu lộ trình giao hàng chặng cuối.**

## 1.2. Bài toán thực tế

Giả sử một cửa hàng hoặc kho hàng cần giao hàng đến nhiều địa điểm đã biết trước.

Người giao hàng cần trả lời câu hỏi:

**Nên đi qua các địa điểm theo thứ tự nào để tổng quãng đường di chuyển là nhỏ nhất?**

Ví dụ:

    Kho → Khách A → Khách B → Khách C → Kho

Nếu đi theo cảm tính, người giao hàng có thể đi vòng, quay lại khu vực cũ hoặc làm tăng chi phí vận hành.

## 1.3. Mục tiêu tối ưu

Trong phiên bản hiện tại, mục tiêu chính là:

    Tối thiểu hóa tổng quãng đường đường bộ.

Chi phí được tính theo công thức:

    Chi phí = Tổng quãng đường × Chi phí mỗi kilomet

Do đó, nếu chi phí/km cố định, giảm quãng đường sẽ trực tiếp làm giảm chi phí ước tính.

## 1.4. Thời gian có phải mục tiêu tối ưu không?

Hiện tại, thời gian và ETA được dùng để đánh giá lộ trình sau khi thuật toán đã tìm ra thứ tự đi.

Nói chính xác:

**Ứng dụng tối ưu theo quãng đường. Thời gian di chuyển và ETA là chỉ số bổ sung, chưa phải hàm mục tiêu chính.**

Nếu thầy/cô hỏi:

**“Nhóm đang tối ưu chi phí hay thời gian?”**

Trả lời:

> Nhóm đang tối ưu tổng quãng đường đường bộ. Vì chi phí được mô hình hóa theo chi phí cố định trên mỗi kilomet, nên tối ưu quãng đường đồng nghĩa với giảm chi phí vận hành ước tính. Thời gian và ETA được tính để hỗ trợ đánh giá lộ trình, nhưng chưa phải hàm mục tiêu tối ưu chính.

---

# 2. Pipeline tổng thể của ứng dụng

Luồng xử lý chính:

    Người dùng nhập dữ liệu địa điểm
            ↓
    Chuẩn hóa và kiểm tra dữ liệu
            ↓
    Chuyển latitude/longitude thành tọa độ cho OpenRouteService
            ↓
    Gọi Matrix API để lấy ma trận khoảng cách và thời gian đường bộ
            ↓
    Chạy thuật toán TSP
            ↓
    Nhận thứ tự đi qua các địa điểm
            ↓
    Gọi Directions API để lấy hình học tuyến đường thực tế
            ↓
    Tính ETA, chi phí, tốc độ trung bình
            ↓
    Hiển thị kết quả, biểu đồ, bảng và bản đồ
            ↓
    Lưu lịch sử bằng SQLite
            ↓
    Dashboard thống kê và so sánh thuật toán

## 2.1. Các dạng dữ liệu chính

Trong đồ án có 4 dạng dữ liệu quan trọng.

### Dạng 1: DataFrame địa điểm
File: app.py

Được lưu trong:

def render_location_editor() -> None:
               
    st.session_state.locations
   
Cấu trúc thường có các cột:

    id
    name
    latitude
    longitude
    service_time

Ý nghĩa:

| Cột | Ý nghĩa |
|---|---|
| `id` | Mã địa điểm |
| `name` | Tên địa điểm |
| `latitude` | Vĩ độ |
| `longitude` | Kinh độ |
| `service_time` | Thời gian phục vụ tại điểm đó, tính bằng phút |

Ví dụ:

    id | name          | latitude  | longitude  | service_time
    0  | Kho trung tâm | 10.762622 | 106.660172 | 0
    1  | Khách A       | 10.755500 | 106.671200 | 5

### Dạng 2: Ma trận khoảng cách

Ví dụ có 3 địa điểm:

    0 = Kho
    1 = A
    2 = B

Ma trận khoảng cách:

    D = [
        [0, 3, 5],
        [4, 0, 2],
        [6, 3, 0]
    ]

Ý nghĩa:

    D[0][1] = 3

Tức là đi từ điểm 0 đến điểm 1 dài 3 km.

    D[1][0] = 4

Tức là đi từ điểm 1 về điểm 0 dài 4 km.

Lưu ý: với đường bộ thực tế, khoảng cách có thể bất đối xứng vì đường một chiều, cầu vượt, rẽ cấm hoặc mạng giao thông khác nhau.

### Dạng 3: Lộ trình

Lộ trình được biểu diễn bằng danh sách chỉ số dòng trong DataFrame:

    display_route = [0, 2, 1, 3, 0]

Nghĩa là:

    locations.iloc[0] → locations.iloc[2] → locations.iloc[1] → locations.iloc[3] → locations.iloc[0]

Nếu `return_to_start = True`, điểm đầu được thêm lại ở cuối.

### Dạng 4: Result dictionary

Sau khi chạy thuật toán, kết quả thường có dạng dictionary:

    result = {
        "algorithm": "Nearest Neighbor",
        "route": [0, 2, 1, 3],
        "display_route": [0, 2, 1, 3, 0],
        "distance": 12.345,
        "execution_time": 0.00123,
        "evaluated_routes": 10
    }

Sau đó được bổ sung thêm:

    result["eta_table"]
    result["delivery_cost"]
    result["route_geojson"]
    result["road_duration_seconds"]
    result["vehicle_label"]
    result["average_speed_kmh"]

---

# 3. Kiến trúc thư mục

Một cấu trúc điển hình của đồ án:

    tsp-delivery-project/
    ├── app.py
    ├── requirements.txt
    ├── README.md
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
    │   ├── road_routing_service.py
    │   └── route_service.py
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
    ├── data/
    │   ├── locations_5.csv
    │   ├── locations_10.csv
    │   ├── locations_20.csv
    │   └── optimization_history.db
    │
    └── tests/

## 3.1. `app.py`

Đây là file trung tâm.

Nhiệm vụ:

- Khởi tạo giao diện Streamlit.
- Quản lý `session_state`.
- Cho phép upload CSV.
- Cho phép thêm/sửa/xóa địa điểm.
- Đọc API key.
- Gọi OpenRouteService.
- Gọi thuật toán.
- Tính ETA, chi phí.
- Hiển thị kết quả.
- Tạo bản đồ.
- Gọi lưu lịch sử.
- Gọi dashboard.

`app.py` không nên chứa toàn bộ logic thuật toán chi tiết. Nó chỉ nên điều phối.

Cách hiểu đơn giản:

    app.py = bộ điều khiển chính của ứng dụng

## 3.2. `algorithms/`

Chứa các thuật toán giải TSP.

### `brute_force.py`

Chạy tất cả hoán vị có thể có.

Ưu điểm:

- Luôn tìm được lời giải tối ưu tuyệt đối với dữ liệu nhỏ.

Nhược điểm:

- Rất chậm khi số địa điểm tăng.
- Độ phức tạp xấp xỉ O(n!).

### `nearest_neighbor.py`

Thuật toán tham lam.

Ý tưởng:

    Từ điểm hiện tại, luôn đi đến điểm chưa thăm gần nhất.

Ưu điểm:

- Nhanh.
- Dễ hiểu.
- Phù hợp dữ liệu lớn hơn Brute Force.

Nhược điểm:

- Không đảm bảo tối ưu toàn cục.

### `two_opt.py`

Thuật toán cải thiện lộ trình.

Ý tưởng:

    Nếu đổi chiều một đoạn trong lộ trình làm tổng quãng đường ngắn hơn, thì chấp nhận đổi.

Ưu điểm:

- Cải thiện tốt lộ trình ban đầu.
- Dễ kết hợp với Nearest Neighbor hoặc Genetic Algorithm.

Nhược điểm:

- Chỉ tối ưu cục bộ.
- Có thể mắc kẹt ở local optimum.

### `genetic_algorithm.py`

Thuật toán di truyền.

Ý tưởng:

    Mỗi cá thể là một lộ trình.
    Quần thể gồm nhiều lộ trình.
    Qua nhiều thế hệ, chọn lọc, lai ghép và đột biến để tìm lộ trình tốt hơn.

Ưu điểm:

- Phù hợp bài toán lớn.
- Có khả năng khám phá nhiều vùng nghiệm.

Nhược điểm:

- Không đảm bảo tối ưu tuyệt đối.
- Phụ thuộc tham số: population, generations, mutation rate, seed.

## 3.3. `services/`

Chứa các hàm phục vụ nghiệp vụ.

### `delivery_service.py`

Nhiệm vụ:

- Tính chi phí giao hàng.
- Tính ETA.
- Tạo bảng thời gian đến từng điểm.

### `road_routing_service.py`

Nhiệm vụ:

- Chuyển DataFrame thành tọa độ.
- Gọi OpenRouteService Matrix API.
- Gọi Directions API.
- Lấy tổng quãng đường và thời gian từ GeoJSON.

### `distance_service.py`

Có thể chứa công thức Haversine cũ.

Haversine tính khoảng cách “đường chim bay” giữa hai tọa độ trên Trái Đất.

Hiện tại khi đã dùng OpenRouteService, Haversine không còn là nguồn chính cho khoảng cách đường bộ.

## 3.4. `database/`

Chứa tầng lưu trữ SQLite.

### `history_repository.py`

Nhiệm vụ:

- Tạo database.
- Tạo bảng lịch sử.
- Lưu kết quả.
- Chống lưu trùng bằng hash.
- Đọc lịch sử.
- Xóa bản ghi.
- Xóa toàn bộ lịch sử.

## 3.5. `views/`

Chứa phần giao diện phụ.

### `history_dashboard.py`

Nhiệm vụ:

- Hiển thị lịch sử chạy thuật toán.
- Lọc theo thuật toán.
- Tính thống kê.
- Vẽ biểu đồ.
- Xuất CSV.
- Xóa dữ liệu lịch sử.

## 3.6. `utils/`

Chứa các hàm tiện ích.

### `validators.py`

Nhiệm vụ:

- Chuẩn hóa dữ liệu địa điểm.
- Kiểm tra thiếu cột.
- Kiểm tra ID trùng.
- Kiểm tra tọa độ sai.
- Kiểm tra thời gian phục vụ âm.

---

# 4. Giải thích các câu lệnh lõi trong `app.py`

## 4.1. Import

Ví dụ:

    import hashlib
    import json
    from datetime import datetime
    from io import BytesIO

    import folium
    import pandas as pd
    import streamlit as st
    from streamlit_folium import folium_static

Giải thích:

- `hashlib`: tạo mã băm để kiểm tra file CSV có thay đổi không.
- `json`: chuyển list/dict thành chuỗi để lưu SQLite.
- `datetime`: xử lý giờ xuất phát, giờ đến, giờ rời.
- `BytesIO`: đọc file upload từ bộ nhớ.
- `folium`: tạo bản đồ.
- `pandas as pd`: xử lý bảng dữ liệu.
- `streamlit as st`: tạo giao diện web.
- `folium_static`: nhúng bản đồ Folium vào Streamlit.

Câu hỏi có thể bị hỏi:

**Vì sao dùng Pandas?**

Trả lời:

> Vì dữ liệu địa điểm có dạng bảng gồm id, tên, latitude, longitude và service_time. Pandas giúp đọc CSV, chỉnh sửa bảng, lọc dòng, đổi tên cột, thống kê và hiển thị dữ liệu rất thuận tiện.

---

## 4.2. `st.set_page_config`

    st.set_page_config(
        page_title="TSP Delivery Optimizer",
        page_icon="🚚",
        layout="wide",
    )

Giải thích:

- Cấu hình trang Streamlit.
- `page_title`: tiêu đề tab trình duyệt.
- `page_icon`: icon tab.
- `layout="wide"`: dùng bố cục rộng, phù hợp dashboard và bản đồ.

Câu hỏi:

**Nếu bỏ `layout="wide"` thì sao?**

Trả lời:

> Giao diện sẽ hẹp hơn, bảng và bản đồ khó quan sát. Với bài toán có nhiều bảng, metric và bản đồ, layout rộng phù hợp hơn.

---

## 4.3. Danh sách thuật toán

    ALGORITHM_OPTIONS = [
        "Nearest Neighbor",
        "Nearest Neighbor + 2-opt",
        "Brute Force",
        "Genetic Algorithm",
        "Genetic Algorithm + 2-opt",
    ]

Giải thích:

- Đây là danh sách lựa chọn hiển thị trong `selectbox`.
- Người dùng chọn tên thuật toán.
- Tên được truyền vào `run_selected_algorithm()` để gọi đúng hàm.

Câu hỏi:

**Vì sao để tên thuật toán trong list thay vì viết cứng trong giao diện?**

Trả lời:

> Để dễ quản lý, dễ thêm/bớt thuật toán, tránh lặp code và giúp giao diện tự sinh từ danh sách.

---

## 4.4. Mapping phương tiện

    ROUTING_PROFILE_MAPPING = {
        "Xe giao hàng": "driving-car",
        "Xe đạp": "cycling-regular",
        "Đi bộ": "foot-walking",
    }

Giải thích:

- Bên trái là nhãn tiếng Việt hiển thị cho người dùng.
- Bên phải là profile mà OpenRouteService hiểu.
- Khi người dùng chọn “Xe giao hàng”, API nhận `driving-car`.

Câu hỏi:

**Tại sao cần mapping thay vì đưa thẳng `driving-car` cho người dùng?**

Trả lời:

> Vì `driving-car` là thuật ngữ kỹ thuật của API. Mapping giúp giao diện thân thiện hơn nhưng vẫn gửi đúng tham số cho dịch vụ định tuyến.

---

# 5. OpenRouteService và cache

## 5.1. Đọc API key

    def get_ors_api_key() -> str:
        try:
            return str(st.secrets["ORS_API_KEY"]).strip()
        except Exception:
            return ""

Giải thích:

- `st.secrets["ORS_API_KEY"]` đọc key từ `.streamlit/secrets.toml`.
- `str(...).strip()` ép về chuỗi và bỏ khoảng trắng đầu/cuối.
- Nếu không có key hoặc file lỗi, trả về chuỗi rỗng.

Câu hỏi:

**Vì sao không viết API key trực tiếp trong code?**

Trả lời:

> Vì API key là thông tin nhạy cảm. Nếu viết trực tiếp trong code và đẩy lên GitHub, người khác có thể sử dụng key trái phép. Dùng `secrets.toml` giúp giữ key ở máy cục bộ.

---

## 5.2. Cache ma trận đường bộ

    @st.cache_data(ttl=3600, show_spinner=False)
    def cached_build_road_matrices(
        coordinates: tuple[tuple[float, float], ...],
        api_key: str,
        profile: str,
    ):
        return build_road_matrices(
            coordinates=coordinates,
            api_key=api_key,
            profile=profile,
        )

Giải thích:

- `@st.cache_data` giúp Streamlit nhớ kết quả của hàm.
- Nếu input giống nhau, hàm không gọi API lại.
- `ttl=3600` nghĩa là cache tồn tại 3600 giây, tức 1 giờ.
- `show_spinner=False` tắt spinner tự động vì nhóm tự viết spinner/status riêng.

Tại sao `coordinates` dùng tuple thay vì list?

Vì dữ liệu đưa vào cache cần ổn định và hashable. Tuple ít bị thay đổi hơn list.

Câu hỏi:

**Cache giúp gì trong đồ án này?**

Trả lời:

> Vì Matrix API và Directions API là lời gọi mạng, có giới hạn và tốn thời gian. Cache giúp tránh gọi lại cùng một request khi dữ liệu không đổi, làm ứng dụng nhanh hơn và giảm nguy cơ vượt giới hạn API.

---

## 5.3. Cache GeoJSON tuyến đường

    @st.cache_data(ttl=3600, show_spinner=False)
    def cached_get_route_geojson(
        ordered_coordinates: tuple[tuple[float, float], ...],
        api_key: str,
        profile: str,
    ):
        return get_route_geojson(
            ordered_coordinates=ordered_coordinates,
            api_key=api_key,
            profile=profile,
        )

Giải thích:

- Ma trận chỉ cho biết khoảng cách giữa từng cặp điểm.
- GeoJSON cho biết hình dạng đường đi thực tế để vẽ lên bản đồ.
- `ordered_coordinates` là tọa độ đã được sắp xếp theo kết quả TSP.

Câu hỏi:

**Matrix API và Directions API khác nhau thế nào?**

Trả lời:

> Matrix API trả về ma trận khoảng cách và thời gian giữa mọi cặp điểm, dùng cho thuật toán tối ưu. Directions API trả về hình học tuyến đường theo một thứ tự cụ thể, dùng để vẽ lộ trình thực tế trên bản đồ.

---

# 6. Hàm hỗ trợ chung

## 6.1. `format_route`

    def format_route(display_route: list[int], locations: pd.DataFrame) -> str:
        if not display_route or locations.empty:
            return "Chưa có lộ trình"

        route_names = [
            str(locations.iloc[index]["name"])
            for index in display_route
        ]

        return " → ".join(route_names)

Giải thích từng phần:

    if not display_route or locations.empty:

- Nếu lộ trình rỗng hoặc bảng địa điểm rỗng, không thể hiển thị.

    locations.iloc[index]["name"]

- `iloc[index]` lấy dòng theo vị trí số thứ tự.
- `["name"]` lấy tên địa điểm của dòng đó.

Ví dụ:

    display_route = [0, 2, 1]

Nếu DataFrame có:

    0 = Kho
    1 = A
    2 = B

Thì:

    route_names = ["Kho", "B", "A"]

Câu lệnh:

    " → ".join(route_names)

sẽ tạo chuỗi:

    Kho → B → A

Câu hỏi:

**Vì sao dùng `iloc` thay vì lọc theo `id`?**

Trả lời:

> Vì thuật toán làm việc với chỉ số dòng trong ma trận. Ma trận khoảng cách có hàng/cột tương ứng với vị trí dòng trong DataFrame, nên dùng `iloc` đảm bảo truy cập đúng vị trí đã dùng trong thuật toán.

---

## 6.2. `format_duration`

    def format_duration(total_minutes: float) -> str:
        total_minutes = max(0.0, float(total_minutes))

        hours = int(total_minutes // 60)
        minutes = int(round(total_minutes % 60))

        if minutes == 60:
            hours += 1
            minutes = 0

        if hours == 0:
            return f"{minutes} phút"

        return f"{hours} giờ {minutes} phút"

Giải thích:

    total_minutes = max(0.0, float(total_minutes))

- Ép thời gian về số thực.
- Nếu âm thì lấy 0 để tránh hiển thị thời gian âm.

    hours = int(total_minutes // 60)

- `//` là chia lấy phần nguyên.
- Ví dụ `125 // 60 = 2`.

    minutes = int(round(total_minutes % 60))

- `%` lấy phần dư.
- Ví dụ `125 % 60 = 5`.

Nếu `round` làm phút thành 60, thì cộng thêm 1 giờ.

Câu hỏi:

**Tại sao cần xử lý `minutes == 60`?**

Trả lời:

> Vì làm tròn có thể khiến 59.7 phút thành 60 phút. Khi đó cần chuyển thành thêm 1 giờ và 0 phút để định dạng hợp lý.

---

# 7. Session State trong Streamlit

## 7.1. Hàm `initialize_session_state`

    def initialize_session_state() -> None:
        if "locations" not in st.session_state:
            st.session_state.locations = load_default_data()

        if "result" not in st.session_state:
            st.session_state.result = None

        if "uploaded_csv_hash" not in st.session_state:
            st.session_state.uploaded_csv_hash = None

        if "uploader_version" not in st.session_state:
            st.session_state.uploader_version = 0

        if "last_saved_history_id" not in st.session_state:
            st.session_state.last_saved_history_id = None

Giải thích:

Streamlit có đặc điểm:

    Mỗi lần người dùng bấm nút, chọn selectbox hoặc upload file, toàn bộ script chạy lại từ đầu.

Nếu không dùng `st.session_state`, dữ liệu sẽ bị mất sau mỗi lần rerun.

Các biến quan trọng:

| Biến | Ý nghĩa |
|---|---|
| `locations` | Bảng địa điểm hiện tại |
| `result` | Kết quả tối ưu gần nhất |
| `uploaded_csv_hash` | Mã băm của file CSV đã upload |
| `uploader_version` | Dùng để reset file uploader |
| `last_saved_history_id` | ID lịch sử vừa lưu |

Câu hỏi:

**Vì sao cần `session_state.result`?**

Trả lời:

> Vì sau khi chạy thuật toán, người dùng có thể cuộn bản đồ, chuyển tab hoặc tương tác giao diện. Streamlit sẽ rerun. Nếu không lưu kết quả trong `session_state`, kết quả vừa chạy sẽ biến mất.

---

# 8. Upload CSV và chống mất kết quả

## 8.1. File uploader

    uploaded_file = st.file_uploader(
        "Tải danh sách địa điểm từ CSV",
        type=["csv"],
        key=uploader_key,
    )

Giải thích:

- Cho người dùng upload file CSV.
- Chỉ cho phép đuôi `.csv`.
- `key` giúp Streamlit quản lý trạng thái widget.

## 8.2. Đọc bytes và tạo hash

    file_bytes = uploaded_file.getvalue()
    current_file_hash = hashlib.sha256(file_bytes).hexdigest()

Giải thích:

- `uploaded_file.getvalue()` lấy toàn bộ nội dung file dạng bytes.
- `hashlib.sha256(file_bytes)` tạo mã băm SHA-256.
- `.hexdigest()` đổi mã băm sang chuỗi dễ so sánh.

Mục đích:

    Nếu người dùng không upload file mới, không xử lý lại CSV.

Câu hỏi:

**Vì sao cần hash file CSV?**

Trả lời:

> Vì Streamlit rerun nhiều lần. Nếu cứ đọc lại file upload ở mỗi lần rerun, dữ liệu có thể bị reset và làm mất kết quả tối ưu. Hash giúp nhận biết file có thật sự thay đổi hay không.

## 8.3. Đọc CSV bằng Pandas

    uploaded_data = pd.read_csv(BytesIO(file_bytes))

Giải thích:

- `BytesIO(file_bytes)` biến bytes thành đối tượng giống file.
- `pd.read_csv(...)` đọc file CSV thành DataFrame.

## 8.4. Chuẩn hóa và kiểm tra

    uploaded_data = normalize_locations(uploaded_data)
    errors = validate_locations(uploaded_data)

Giải thích:

- `normalize_locations`: chuẩn hóa tên cột, kiểu dữ liệu, thứ tự cột.
- `validate_locations`: kiểm tra lỗi dữ liệu.

Ví dụ lỗi có thể có:

- Thiếu cột `latitude`.
- ID trùng.
- Tọa độ ngoài phạm vi.
- `service_time` âm.

## 8.5. Cập nhật dữ liệu hợp lệ

    st.session_state.locations = uploaded_data.reset_index(drop=True)
    st.session_state.result = None
    st.session_state.uploaded_csv_hash = current_file_hash

Giải thích:

- `reset_index(drop=True)` đặt lại index DataFrame từ 0, 1, 2,...
- `result = None` vì dữ liệu đã đổi, kết quả cũ không còn phù hợp.
- Lưu hash để tránh đọc lại file cũ.

Câu hỏi:

**Vì sao khi đổi dữ liệu phải xóa `result`?**

Trả lời:

> Vì kết quả tối ưu cũ được tính trên danh sách địa điểm cũ. Khi dữ liệu thay đổi, lộ trình cũ không còn đúng nữa nên cần đặt lại kết quả.

---

# 9. Thêm địa điểm mới

## 9.1. Form Streamlit

    with st.form("add_location_form", clear_on_submit=True):
        ...

Giải thích:

- `st.form` gom nhiều input thành một form.
- Người dùng nhập xong rồi nhấn submit.
- `clear_on_submit=True` xóa form sau khi thêm thành công.

## 9.2. Tạo ID mới

    new_id = (
        int(locations["id"].max()) + 1
        if not locations.empty
        else 0
    )

Giải thích:

- Nếu bảng không rỗng, lấy ID lớn nhất + 1.
- Nếu bảng rỗng, ID đầu tiên là 0.

Câu lệnh lõi:

    locations["id"].max()

- Lấy giá trị lớn nhất trong cột `id`.

Câu hỏi:

**Nếu xóa một địa điểm ở giữa thì ID mới có lấp vào chỗ trống không?**

Trả lời:

> Không. Cách hiện tại lấy ID lớn nhất cộng 1 để tránh trùng ID. Nó không cố lấp khoảng trống, vì mục tiêu là định danh ổn định và đơn giản.

## 9.3. Tạo dòng mới

    new_row = pd.DataFrame(
        [
            {
                "id": new_id,
                "name": name.strip(),
                "latitude": latitude,
                "longitude": longitude,
                "service_time": service_time,
            }
        ]
    )

Giải thích:

- Tạo DataFrame một dòng.
- Dữ liệu nằm trong list chứa một dictionary.
- `name.strip()` bỏ khoảng trắng dư ở đầu và cuối tên.

## 9.4. Ghép vào bảng cũ

    updated_locations = pd.concat(
        [locations, new_row],
        ignore_index=True,
    )

Giải thích:

- `pd.concat` ghép nhiều DataFrame lại.
- `ignore_index=True` đánh lại index liên tục từ 0.

Câu hỏi:

**Vì sao không dùng `append`?**

Trả lời:

> `DataFrame.append` đã bị loại bỏ trong các phiên bản Pandas mới. `pd.concat` là cách chính thức và ổn định hơn.

---

# 10. Chỉnh sửa địa điểm bằng `st.data_editor`

    edited_locations = st.data_editor(
        st.session_state.locations,
        use_container_width=True,
        num_rows="dynamic",
        column_config={...},
        key="location_editor",
    )

Giải thích:

- Hiển thị DataFrame dưới dạng bảng có thể chỉnh sửa.
- `num_rows="dynamic"` cho phép thêm hoặc xóa dòng.
- `column_config` quy định kiểu dữ liệu từng cột.

Ví dụ:

    "latitude": st.column_config.NumberColumn(
        "Vĩ độ",
        required=True,
        format="%.6f",
    )

Giải thích:

- Cột latitude là số.
- Bắt buộc nhập.
- Hiển thị 6 chữ số sau dấu phẩy.

Câu hỏi:

**Vì sao sau khi sửa bảng vẫn cần validate lại?**

Trả lời:

> Vì người dùng có thể nhập tọa độ sai, ID trùng hoặc thời gian phục vụ âm. Giao diện chỉ hỗ trợ nhập liệu, còn logic nghiệp vụ vẫn phải kiểm tra bằng validator.

---

# 11. Chạy thuật toán TSP

## 11.1. Hàm điều phối thuật toán

    def run_selected_algorithm(
        algorithm: str,
        distance_matrix,
        start_index: int,
        return_to_start: bool,
        ga_parameters: dict[str, int | float],
    ) -> dict:

Giải thích input:

| Tham số | Ý nghĩa |
|---|---|
| `algorithm` | Tên thuật toán người dùng chọn |
| `distance_matrix` | Ma trận khoảng cách đường bộ |
| `start_index` | Chỉ số điểm xuất phát |
| `return_to_start` | Có quay lại điểm đầu hay không |
| `ga_parameters` | Tham số Genetic Algorithm |

Hàm này giống một “bộ chia nhánh”:

    Nếu chọn Brute Force → gọi solve_brute_force
    Nếu chọn Nearest Neighbor → gọi solve_nearest_neighbor
    Nếu chọn GA → gọi solve_genetic_algorithm
    Nếu chọn + 2-opt → chạy thuật toán nền rồi cải thiện bằng 2-opt

---

## 11.2. Brute Force

    if algorithm == "Brute Force":
        return solve_brute_force(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
            max_locations=10,
        )

Giải thích:

- Brute Force thử tất cả thứ tự có thể.
- `max_locations=10` giới hạn số địa điểm để tránh treo ứng dụng.

Câu hỏi:

**Vì sao Brute Force bị giới hạn 10 địa điểm?**

Trả lời:

> Vì số hoán vị tăng theo giai thừa. Với 10 điểm, số lộ trình cần xét là 9! = 362.880 nếu cố định điểm xuất phát. Với 20 điểm, số hoán vị là 19!, quá lớn để chạy thực tế trong ứng dụng demo.

---

## 11.3. Nearest Neighbor

    if algorithm == "Nearest Neighbor":
        return solve_nearest_neighbor(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
        )

Ý tưởng:

    Từ điểm hiện tại, chọn điểm chưa thăm có khoảng cách nhỏ nhất.

Pseudo-code:

    current = start
    unvisited = tất cả điểm trừ start
    route = [start]

    while còn điểm chưa thăm:
        next = điểm trong unvisited có distance_matrix[current][next] nhỏ nhất
        route.append(next)
        unvisited.remove(next)
        current = next

    nếu return_to_start:
        route.append(start)

Câu hỏi:

**Nearest Neighbor có luôn tối ưu không?**

Trả lời:

> Không. Nearest Neighbor là heuristic tham lam. Nó chọn tốt nhất ở bước hiện tại nhưng không nhìn toàn cục, nên có thể dẫn đến lộ trình cuối chưa tối ưu.

---

## 11.4. Nearest Neighbor + 2-opt

    if algorithm == "Nearest Neighbor + 2-opt":
        base_result = solve_nearest_neighbor(...)

        result = solve_two_opt_from_result(
            base_result=base_result,
            distance_matrix=distance_matrix,
            algorithm_name="Nearest Neighbor + 2-opt",
        )

        result["base_evaluated_routes"] = base_result.get(
            "evaluated_routes"
        )

        return result

Giải thích:

- Đầu tiên chạy Nearest Neighbor để có lộ trình ban đầu.
- Sau đó dùng 2-opt để cải thiện.
- `base_result.get("evaluated_routes")` lấy số phương án đã đánh giá nếu có.
- `return result` bắt buộc để trả kết quả ra ngoài.

Câu hỏi:

**Vì sao không chạy 2-opt từ lộ trình ngẫu nhiên?**

Trả lời:

> Có thể chạy từ lộ trình ngẫu nhiên, nhưng Nearest Neighbor cho điểm khởi đầu tốt hơn và ổn định hơn. 2-opt sau đó đóng vai trò cải thiện cục bộ.

---

## 11.5. Genetic Algorithm

    if algorithm == "Genetic Algorithm":
        return solve_genetic_algorithm(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
            population_size=int(ga_parameters["population_size"]),
            generations=int(ga_parameters["generations"]),
            crossover_rate=float(ga_parameters["crossover_rate"]),
            mutation_rate=float(ga_parameters["mutation_rate"]),
            tournament_size=int(ga_parameters["tournament_size"]),
            elite_size=int(ga_parameters["elite_size"]),
            random_seed=int(ga_parameters["random_seed"]),
        )

Giải thích:

- Các tham số từ giao diện được ép kiểu rõ ràng.
- `int(...)`: ép về số nguyên.
- `float(...)`: ép về số thực.

Các tham số:

| Tham số | Ý nghĩa |
|---|---|
| `population_size` | Số cá thể trong mỗi thế hệ |
| `generations` | Số vòng tiến hóa |
| `crossover_rate` | Xác suất lai ghép |
| `mutation_rate` | Xác suất đột biến |
| `tournament_size` | Số cá thể tham gia chọn lọc |
| `elite_size` | Số cá thể tốt nhất được giữ lại |
| `random_seed` | Hạt giống ngẫu nhiên để tái lập kết quả |

Câu hỏi:

**Vì sao cần random seed?**

Trả lời:

> Genetic Algorithm có yếu tố ngẫu nhiên trong khởi tạo quần thể, lai ghép và đột biến. Random seed giúp kết quả có thể tái lập khi báo cáo hoặc kiểm thử.

---

# 12. Logic Brute Force

Một cách triển khai thường gặp:

    from itertools import permutations

    nodes = [i for i in range(n) if i != start_index]

    for permutation in permutations(nodes):
        route = [start_index, *permutation]

        if return_to_start:
            display_route = [*route, start_index]
        else:
            display_route = route

        distance = calculate_route_distance(display_route, distance_matrix)

Giải thích:

## 12.1. `range(n)`

    range(n)

Tạo dãy:

    0, 1, 2, ..., n-1

Nếu có 5 địa điểm:

    range(5) = 0, 1, 2, 3, 4

## 12.2. List comprehension

    nodes = [i for i in range(n) if i != start_index]

Giải thích:

- Duyệt mọi chỉ số địa điểm.
- Bỏ điểm xuất phát.
- Chỉ hoán vị các điểm còn lại.

Ví dụ:

    n = 5
    start_index = 0

Kết quả:

    nodes = [1, 2, 3, 4]

## 12.3. `permutations(nodes)`

    permutations([1, 2, 3])

Tạo:

    (1, 2, 3)
    (1, 3, 2)
    (2, 1, 3)
    (2, 3, 1)
    (3, 1, 2)
    (3, 2, 1)

Có 3! = 6 hoán vị.

Câu hỏi:

**Vì sao cố định điểm xuất phát làm giảm số phương án?**

Trả lời:

> Nếu không cố định điểm xuất phát thì có n! hoán vị. Khi cố định điểm xuất phát, chỉ cần hoán vị n-1 điểm còn lại nên còn (n-1)! phương án.

---

# 13. Logic tính tổng khoảng cách lộ trình

Công thức:

    total_distance = 0

    for i in range(len(route) - 1):
        from_index = route[i]
        to_index = route[i + 1]
        total_distance += distance_matrix[from_index][to_index]

Ví dụ:

    route = [0, 2, 1, 0]

Vòng lặp:

| i | from | to | cộng |
|---|---|---|---|
| 0 | 0 | 2 | D[0][2] |
| 1 | 2 | 1 | D[2][1] |
| 2 | 1 | 0 | D[1][0] |

Tổng:

    D[0][2] + D[2][1] + D[1][0]

Câu hỏi:

**Vì sao dùng `len(route) - 1`?**

Trả lời:

> Vì mỗi chặng cần lấy cặp điểm liên tiếp `route[i]` và `route[i+1]`. Nếu chạy tới phần tử cuối, `i+1` sẽ vượt ngoài danh sách.

---

# 14. Logic Nearest Neighbor

Pseudo-code:

    visited = {start_index}
    route = [start_index]
    current = start_index

    while len(visited) < n:
        nearest = None
        nearest_distance = infinity

        for candidate in range(n):
            if candidate in visited:
                continue

            distance = distance_matrix[current][candidate]

            if distance < nearest_distance:
                nearest_distance = distance
                nearest = candidate

        route.append(nearest)
        visited.add(nearest)
        current = nearest

Giải thích:

## 14.1. Set `visited`

    visited = {start_index}

`set` dùng để kiểm tra một điểm đã thăm chưa.

Ưu điểm:

    candidate in visited

rất nhanh.

## 14.2. Biến `current`

    current = start_index

Đại diện cho vị trí đang đứng.

Sau khi chọn điểm tiếp theo:

    current = nearest

## 14.3. `continue`

    if candidate in visited:
        continue

Nếu điểm đã thăm rồi thì bỏ qua, không xét nữa.

Câu hỏi:

**Nearest Neighbor có thể bị sai ở đâu?**

Trả lời:

> Nó không sai về mặt thuật toán, nhưng có thể cho nghiệm chưa tối ưu vì chỉ chọn điểm gần nhất ở hiện tại mà không xét hậu quả ở các bước sau.

---

# 15. Logic 2-opt

## 15.1. Ý tưởng

Nếu lộ trình có hai cạnh bắt chéo, đảo một đoạn giữa chúng có thể làm đường ngắn hơn.

Ví dụ:

    A → B → C → D → E

Chọn đoạn từ B đến D và đảo lại:

    A → D → C → B → E

## 15.2. Câu lệnh đảo đoạn

    new_route = route[:i] + route[i:j + 1][::-1] + route[j + 1:]

Giải thích:

Giả sử:

    route = [0, 1, 2, 3, 4]
    i = 1
    j = 3

Phân tích:

    route[:i] = [0]

    route[i:j + 1] = route[1:4] = [1, 2, 3]

    route[i:j + 1][::-1] = [3, 2, 1]

    route[j + 1:] = route[4:] = [4]

Ghép lại:

    [0] + [3, 2, 1] + [4]
    = [0, 3, 2, 1, 4]

Câu hỏi:

**`[::-1]` nghĩa là gì?**

Trả lời:

> Đây là slicing đảo ngược danh sách trong Python. Nó lấy toàn bộ đoạn nhưng bước nhảy là -1, tức đọc từ cuối về đầu.

## 15.3. Vòng lặp cải thiện

    improved = True

    while improved:
        improved = False

        for i in range(...):
            for j in range(...):
                new_route = ...
                if new_distance < best_distance:
                    route = new_route
                    best_distance = new_distance
                    improved = True

Giải thích:

- Biến `improved` cho biết vòng vừa rồi có cải thiện không.
- Nếu có cải thiện, tiếp tục tìm thêm.
- Nếu không còn cải thiện, dừng.

Câu hỏi:

**2-opt có đảm bảo tối ưu toàn cục không?**

Trả lời:

> Không. 2-opt chỉ đảm bảo không còn phép đảo hai cạnh nào làm tốt hơn trong phạm vi xét. Nó có thể dừng ở tối ưu cục bộ.

---

# 16. Logic Genetic Algorithm

## 16.1. Biểu diễn cá thể

Một cá thể là một lộ trình:

    chromosome = [0, 3, 1, 2, 4]

Nếu điểm xuất phát cố định, chromosome thường giữ start ở đầu hoặc chỉ mã hóa các điểm còn lại.

## 16.2. Quần thể

    population = [
        [0, 1, 2, 3],
        [0, 2, 1, 3],
        [0, 3, 2, 1],
        ...
    ]

Mỗi dòng là một phương án lộ trình.

## 16.3. Fitness

Vì bài toán cần khoảng cách nhỏ nhất, nhưng GA thường chọn fitness lớn nhất, nên thường dùng:

    fitness = 1 / distance

Khoảng cách càng nhỏ thì fitness càng lớn.

Câu hỏi:

**Vì sao không dùng trực tiếp distance làm fitness?**

Trả lời:

> Vì trong GA, cá thể có fitness cao thường được ưu tiên chọn. Trong TSP, distance nhỏ mới tốt, nên cần chuyển distance thành giá trị fitness ngược lại, ví dụ `1 / distance`.

## 16.4. Tournament selection

Ý tưởng:

    Chọn ngẫu nhiên k cá thể
    Lấy cá thể tốt nhất trong nhóm đó

Pseudo-code:

    candidates = random.sample(population, tournament_size)
    winner = min(candidates, key=route_distance)

Câu hỏi:

**Tournament size lớn thì ảnh hưởng gì?**

Trả lời:

> Tournament size lớn làm áp lực chọn lọc mạnh hơn, cá thể tốt dễ được chọn hơn. Tuy nhiên nếu quá lớn, quần thể có thể mất đa dạng sớm và dễ mắc kẹt ở nghiệm cục bộ.

## 16.5. Crossover cho TSP

Với TSP, crossover phải tránh trùng địa điểm.

Ví dụ Order Crossover:

    parent1 = [0, 1, 2, 3, 4]
    parent2 = [0, 3, 4, 1, 2]

Chọn một đoạn từ parent1:

    [1, 2]

Sau đó điền các điểm còn thiếu theo thứ tự parent2:

    3, 4

Con có thể là:

    [0, 1, 2, 3, 4]

Câu hỏi:

**Vì sao không crossover như chuỗi nhị phân bình thường?**

Trả lời:

> Vì trong TSP, mỗi địa điểm phải xuất hiện đúng một lần. Nếu cắt ghép tùy ý, con có thể bị trùng điểm hoặc thiếu điểm, làm lộ trình không hợp lệ.

## 16.6. Mutation

Một mutation đơn giản:

    Đổi chỗ hai vị trí trong route.

Ví dụ:

    [0, 1, 2, 3, 4]

Đổi vị trí 1 và 3:

    [0, 3, 2, 1, 4]

Câu hỏi:

**Mutation để làm gì?**

Trả lời:

> Mutation tạo biến đổi ngẫu nhiên để duy trì đa dạng quần thể, giúp thuật toán tránh bị kẹt quá sớm ở một vùng nghiệm.

## 16.7. Elitism

    elite = top cá thể tốt nhất
    new_population = elite + offspring

Giải thích:

- Giữ lại một số cá thể tốt nhất qua thế hệ sau.
- Tránh mất nghiệm tốt đã tìm được.

Câu hỏi:

**Elite size quá lớn có vấn đề gì?**

Trả lời:

> Nếu quá lớn, quần thể ít thay đổi, dễ mất đa dạng và giảm khả năng khám phá nghiệm mới.

---

# 17. ETA và chi phí trong `delivery_service.py`

## 17.1. Tính chi phí

    def calculate_delivery_cost(
        total_distance: float,
        cost_per_km: float,
    ) -> float:
        if total_distance < 0:
            raise ValueError("Tổng quãng đường không được âm.")

        if cost_per_km < 0:
            raise ValueError("Chi phí mỗi kilomet không được âm.")

        return float(total_distance * cost_per_km)

Giải thích:

- Kiểm tra đầu vào không âm.
- Nhân quãng đường với chi phí/km.
- Trả về số thực.

Câu hỏi:

**Vì sao phải kiểm tra giá trị âm?**

Trả lời:

> Vì quãng đường và chi phí/km không thể âm trong thực tế. Kiểm tra này giúp phát hiện dữ liệu lỗi sớm.

## 17.2. Tạo bảng ETA đường bộ

    eta_table, total_duration_minutes = build_road_eta_table(
        display_route=result["display_route"],
        locations=locations,
        distance_matrix_km=distance_matrix,
        duration_matrix_seconds=duration_matrix_seconds,
        departure_datetime=departure_datetime,
    )

Ý nghĩa:

- `display_route`: thứ tự đi.
- `locations`: bảng địa điểm.
- `distance_matrix_km`: khoảng cách giữa từng cặp điểm.
- `duration_matrix_seconds`: thời gian đi giữa từng cặp điểm.
- `departure_datetime`: giờ bắt đầu.

## 17.3. Kiểm tra kích thước ma trận

    expected_shape = (
        location_count,
        location_count,
    )

    if distance_matrix_km.shape != expected_shape:
        raise ValueError(...)

Giải thích:

Nếu có 5 địa điểm, ma trận phải có dạng:

    5 × 5

Tức:

    shape = (5, 5)

Câu hỏi:

**Vì sao ma trận phải là n × n?**

Trả lời:

> Vì cần biết khoảng cách từ mỗi điểm đến mọi điểm còn lại. Với n địa điểm, có n điểm xuất phát và n điểm đích, nên ma trận phải có n hàng và n cột.

## 17.4. Lấy thời gian từng chặng

    segment_duration_seconds = float(
        duration_matrix_seconds[
            previous_location_index
        ][location_index]
    )

Giải thích:

- Hàng là điểm trước.
- Cột là điểm hiện tại.
- Giá trị là thời gian đi từ điểm trước đến điểm hiện tại.

Ví dụ:

    duration_matrix_seconds[2][5]

nghĩa là thời gian đi từ điểm 2 đến điểm 5.

## 17.5. Chuyển giây sang phút

    travel_minutes = (
        segment_duration_seconds / 60.0
    )

Vì:

    1 phút = 60 giây

## 17.6. Cộng dồn thời gian

    elapsed_minutes += travel_minutes

Giải thích:

- Mỗi chặng đi mất một khoảng thời gian.
- `elapsed_minutes` là tổng thời gian đã trôi qua từ lúc xuất phát.

## 17.7. Tính giờ đến

    arrival_datetime = (
        departure_datetime
        + timedelta(minutes=elapsed_minutes)
    )

Giải thích:

- `departure_datetime` là giờ bắt đầu.
- `timedelta(minutes=elapsed_minutes)` là thời gian đã đi.
- Cộng lại ra giờ đến điểm hiện tại.

## 17.8. Không tính thời gian phục vụ khi quay lại kho

    is_return_to_start = (
        order == len(display_route) - 1
        and order > 0
        and location_index == first_location_index
    )

    service_time = (
        0.0
        if is_return_to_start
        else float(location["service_time"])
    )

Giải thích:

- Nếu điểm cuối là quay lại kho, không cần giao hàng nữa.
- Do đó service_time = 0.

Câu hỏi:

**Vì sao quay lại kho không tính thời gian phục vụ?**

Trả lời:

> Vì điểm quay lại kho chỉ để kết thúc lộ trình khép kín, không phải một điểm giao hàng mới. Do đó không cộng thêm thời gian phục vụ.

---

# 18. OpenRouteService và tọa độ

## 18.1. Latitude và longitude

Trong CSV, người dùng thường nhập:

    latitude, longitude

Ví dụ:

    latitude = 10.762622
    longitude = 106.660172

Nhưng nhiều API bản đồ, trong đó có OpenRouteService, dùng thứ tự:

    [longitude, latitude]

Tức:

    [106.660172, 10.762622]

Câu hỏi:

**Vì sao phải đổi thứ tự latitude/longitude?**

Trả lời:

> Vì dữ liệu người dùng thường đọc theo thứ tự latitude, longitude, nhưng OpenRouteService yêu cầu tọa độ theo chuẩn GeoJSON là longitude trước, latitude sau. Nếu truyền sai thứ tự, điểm có thể bị hiểu sai vị trí.

## 18.2. Matrix API

Input:

    locations = [
        [106.660172, 10.762622],
        [106.671200, 10.755500],
    ]

Output:

    distances = [
        [0, 1200],
        [1300, 0]
    ]

    durations = [
        [0, 240],
        [260, 0]
    ]

Trong đó:

- distances thường tính bằng mét.
- durations tính bằng giây.
- Dịch vụ có thể được chuyển sang km trong code.

## 18.3. Directions API

Input:

    ordered_coordinates = [
        tọa độ kho,
        tọa độ khách A,
        tọa độ khách B
    ]

Output:

- GeoJSON.
- Đường polyline thực tế.
- Summary gồm distance và duration.
- Có thể có bbox để fit bản đồ.

---

# 19. Tạo bản đồ bằng Folium

## 19.1. Tạo bản đồ

    route_map = folium.Map(
        location=[center_latitude, center_longitude],
        zoom_start=13,
        control_scale=True,
    )

Giải thích:

- `location`: tâm bản đồ.
- `zoom_start`: mức zoom ban đầu.
- `control_scale=True`: hiển thị thước tỷ lệ.

## 19.2. Tính tâm bản đồ

    center_latitude = float(locations["latitude"].mean())
    center_longitude = float(locations["longitude"].mean())

Giải thích:

- Lấy trung bình vĩ độ và kinh độ của các điểm.
- Tâm bản đồ nằm gần trung tâm cụm địa điểm.

Câu hỏi:

**Tâm bản đồ tính bằng trung bình có luôn chính xác không?**

Trả lời:

> Đây là cách đơn giản và đủ tốt cho dữ liệu nhỏ. Sau đó ứng dụng còn dùng `fit_bounds` để tự căn bản đồ theo toàn tuyến, nên tâm ban đầu không phải yếu tố quyết định.

## 19.3. Thêm marker

    folium.Marker(
        location=[
            float(location["latitude"]),
            float(location["longitude"]),
        ],
        popup=marker_text,
        tooltip=marker_text,
        icon=folium.Icon(...)
    ).add_to(route_map)

Giải thích:

- `location`: vị trí marker.
- `popup`: nội dung hiện khi bấm.
- `tooltip`: nội dung hiện khi rê chuột.
- `.add_to(route_map)`: thêm marker vào bản đồ.

## 19.4. Vẽ tuyến đường bằng GeoJSON

    folium.GeoJson(
        route_geojson,
        name="Lộ trình đường bộ",
        style_function=lambda feature: {
            "weight": 6,
            "opacity": 0.85,
        },
        tooltip="Lộ trình giao hàng",
    ).add_to(route_map)

Giải thích:

- `route_geojson` chứa hình học tuyến đường.
- `style_function` quy định kiểu vẽ.
- `lambda feature` là hàm ngắn nhận một feature GeoJSON rồi trả style.

Câu hỏi:

**Vì sao không dùng PolyLine nối thẳng các điểm?**

Trả lời:

> PolyLine nối thẳng chỉ biểu diễn khoảng cách hình học, có thể cắt qua nhà, sông hoặc đường cấm. GeoJSON từ Directions API biểu diễn tuyến đường thực tế theo mạng giao thông nên phù hợp hơn với bài toán giao hàng.

## 19.5. Fit bản đồ theo tuyến

    route_map.fit_bounds(
        [
            [min_latitude, min_longitude],
            [max_latitude, max_longitude],
        ]
    )

Giải thích:

- `fit_bounds` tự điều chỉnh zoom để toàn bộ tuyến nằm trong khung nhìn.
- Không cần người dùng tự zoom thủ công.

---

# 20. Hiển thị kết quả

## 20.1. Metric

    st.metric(
        "Tổng quãng đường đường bộ",
        f"{result['distance']:.3f} km",
    )

Giải thích:

- `st.metric` hiển thị chỉ số quan trọng.
- `:.3f` định dạng số thực với 3 chữ số sau dấu phẩy.

Ví dụ:

    12.34567 → 12.346

## 20.2. Định dạng tiền

    f"{result['delivery_cost']:,.0f} VNĐ"

Giải thích:

- `,` thêm dấu phân cách hàng nghìn.
- `.0f` không hiển thị phần thập phân.

Ví dụ:

    1250000 → 1,250,000 VNĐ

## 20.3. Bảng ETA

    eta_display = eta_table.rename(
        columns={
            "order": "Thứ tự",
            "location_id": "Mã",
            ...
        }
    )

Giải thích:

- `rename(columns={...})` đổi tên cột tiếng Anh sang tiếng Việt.
- Bản chất dữ liệu không đổi, chỉ đổi nhãn hiển thị.

## 20.4. Tạo bảng chi tiết lộ trình

    route_table = locations.iloc[
        result["display_route"]
    ][
        [
            "id",
            "name",
            "latitude",
            "longitude",
            "service_time",
        ]
    ].copy()

Giải thích:

- `locations.iloc[result["display_route"]]` lấy các dòng theo đúng thứ tự lộ trình.
- Sau đó chọn các cột cần hiển thị.
- `.copy()` tạo bản sao để tránh cảnh báo khi chỉnh sửa.

Câu hỏi:

**Vì sao `locations.iloc[result["display_route"]]` có thể lặp lại kho ở cuối?**

Trả lời:

> Vì `display_route` của lộ trình khép kín có điểm xuất phát được thêm lại ở cuối. Khi dùng `iloc` với danh sách đó, Pandas sẽ lấy lại dòng kho thêm một lần nữa để hiển thị đúng hành trình quay về.

---

# 21. Lưu lịch sử bằng SQLite

## 21.1. Tạo bản ghi lịch sử

    display_route = [int(index) for index in result["display_route"]]

Giải thích:

- Đảm bảo mọi index là số nguyên Python.
- Tránh lỗi khi lưu JSON nếu index là kiểu NumPy integer.

## 21.2. Lấy tên lộ trình

    route_names = [
        str(locations.iloc[index]["name"])
        for index in display_route
    ]

Giống `format_route`, nhưng dùng để lưu vào database.

## 21.3. Tạo snapshot dữ liệu địa điểm

    locations_snapshot = [
        {
            "id": int(row["id"]),
            "name": str(row["name"]),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "service_time": float(row["service_time"]),
        }
        for _, row in locations.iterrows()
    ]

Giải thích:

- `locations.iterrows()` duyệt từng dòng DataFrame.
- `_` là index dòng, không cần dùng.
- `row` là dữ liệu một dòng.
- Snapshot giúp biết lần chạy đó dựa trên danh sách địa điểm nào.

Câu hỏi:

**Vì sao phải lưu snapshot địa điểm?**

Trả lời:

> Vì sau này người dùng có thể sửa danh sách địa điểm. Nếu chỉ lưu route index, ta không biết kết quả cũ được tính trên dữ liệu nào. Snapshot giúp lịch sử có tính tái kiểm tra.

## 21.4. Lưu JSON

    "route_indices": json.dumps(display_route)

Giải thích:

- SQLite không có kiểu list Python.
- `json.dumps` chuyển list thành chuỗi JSON.

Ví dụ:

    [0, 2, 1, 0]

thành:

    "[0, 2, 1, 0]"

## 21.5. Nút lưu

    if st.button("Lưu kết quả vào lịch sử"):
        record = build_history_record(result, locations)
        created, record_id = save_history(record)

Giải thích:

- Khi bấm nút, tạo record.
- Gọi repository để lưu.
- `created` cho biết có thêm mới hay bị trùng.

Câu hỏi:

**Vì sao lưu lịch sử không viết SQL trực tiếp trong `app.py`?**

Trả lời:

> Để tách trách nhiệm. `app.py` chỉ lo giao diện và điều phối, còn `history_repository.py` lo database. Cách này giúp mã dễ bảo trì và kiểm thử hơn.

---

# 22. Logic SQLite trong `history_repository.py`

## 22.1. Kết nối database

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row

Giải thích:

- `sqlite3.connect(path)` mở kết nối tới file database.
- Nếu file chưa có, SQLite sẽ tạo mới.
- `row_factory = sqlite3.Row` giúp truy cập kết quả SQL như dictionary.

Ví dụ:

    row["id"]

thay vì:

    row[0]

## 22.2. Tạo bảng nếu chưa tồn tại

    CREATE TABLE IF NOT EXISTS optimization_history (...)

Giải thích:

- Nếu bảng chưa có thì tạo.
- Nếu đã có thì không tạo lại.
- Giúp ứng dụng khởi động an toàn nhiều lần.

## 22.3. Ràng buộc UNIQUE

    run_hash TEXT NOT NULL UNIQUE

Giải thích:

- `run_hash` là mã định danh một lần chạy.
- `UNIQUE` không cho phép hai dòng có cùng hash.
- Đây là cơ chế chống lưu trùng.

## 22.4. Tạo hash

    encoded = json.dumps(
        fingerprint_fields,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()

Giải thích:

- Lấy các trường quan trọng tạo thành fingerprint.
- `sort_keys=True` đảm bảo thứ tự key ổn định.
- `separators=(",", ":")` bỏ khoảng trắng thừa để chuỗi ổn định hơn.
- `.encode("utf-8")` chuyển sang bytes.
- SHA-256 tạo mã băm.

Câu hỏi:

**Tại sao không dùng thời điểm `created_at` trong hash?**

Trả lời:

> Vì nếu đưa `created_at` vào hash thì mỗi lần bấm lưu sẽ có thời điểm khác nhau, dẫn đến hash khác nhau và không chống trùng được. Hash chỉ nên dựa trên nội dung kết quả.

## 22.5. Insert or ignore

    INSERT OR IGNORE INTO optimization_history (...)
    VALUES (...)

Giải thích:

- Nếu record chưa có, SQLite insert.
- Nếu trùng `run_hash`, SQLite bỏ qua.
- Không làm chương trình crash.

## 22.6. `cursor.rowcount`

    created = cursor.rowcount == 1

Giải thích:

- Nếu insert thành công, `rowcount = 1`.
- Nếu bị ignore do trùng, `rowcount = 0`.

## 22.7. Đọc lịch sử bằng Pandas

    dataframe = pd.read_sql_query(query, connection, params=parameters)

Giải thích:

- Chạy SQL query.
- Trả kết quả trực tiếp thành DataFrame.
- Dễ hiển thị và thống kê bằng Pandas.

---

# 23. Dashboard lịch sử

## 23.1. Lọc theo thuật toán

    algorithm_options = ["Tất cả", *list_algorithms()]

Giải thích:

- `"Tất cả"` là lựa chọn mặc định.
- `*list_algorithms()` bung danh sách thuật toán ra.

Ví dụ:

    list_algorithms() = ["Brute Force", "Nearest Neighbor"]

Thì:

    ["Tất cả", *list_algorithms()]
    = ["Tất cả", "Brute Force", "Nearest Neighbor"]

## 23.2. Groupby thống kê

    comparison = (
        history.groupby("algorithm", as_index=False)
        .agg(
            so_lan_chay=("id", "count"),
            quang_duong_trung_binh=("distance_km", "mean"),
            quang_duong_tot_nhat=("distance_km", "min"),
            thoi_gian_xu_ly_trung_binh=(
                "execution_time_seconds",
                "mean",
            ),
            chi_phi_trung_binh=("delivery_cost", "mean"),
        )
        .sort_values("quang_duong_trung_binh")
    )

Giải thích:

- `groupby("algorithm")`: gom các dòng theo thuật toán.
- `.agg(...)`: tính nhiều chỉ số thống kê.
- `"count"`: đếm số lần chạy.
- `"mean"`: trung bình.
- `"min"`: giá trị nhỏ nhất.
- `.sort_values(...)`: sắp xếp theo quãng đường trung bình.

Câu hỏi:

**Vì sao so sánh thuật toán bằng quãng đường trung bình?**

Trả lời:

> Vì mỗi thuật toán có thể được chạy nhiều lần trên các cấu hình khác nhau. Trung bình giúp đánh giá xu hướng tổng quát, còn quãng đường tốt nhất cho biết kết quả tốt nhất từng đạt được.

## 23.3. Xuất CSV

    dataframe.to_csv(index=False).encode("utf-8-sig")

Giải thích:

- `to_csv(index=False)` chuyển DataFrame thành CSV và không ghi cột index.
- `utf-8-sig` giúp Excel trên Windows đọc tiếng Việt ít lỗi font hơn.

---

# 24. Công thức Haversine và lượng giác

Nếu file `distance_service.py` có dùng Haversine, đây là công thức thường gặp:

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)^2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)^2

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

Ý nghĩa:

- Trái Đất gần như hình cầu.
- Latitude/longitude là góc, không phải khoảng cách thẳng.
- Cần đổi độ sang radian.
- Haversine tính khoảng cách cung tròn giữa hai điểm trên mặt cầu.

Các hàm lượng giác:

| Hàm | Ý nghĩa |
|---|---|
| `sin` | sin của góc |
| `cos` | cos của góc |
| `sqrt` | căn bậc hai |
| `atan2` | arctangent có xét góc phần tư |
| `radians` | đổi độ sang radian |

Câu hỏi:

**Vì sao Haversine không còn đủ cho bài toán giao hàng?**

Trả lời:

> Haversine chỉ tính khoảng cách đường chim bay giữa hai tọa độ. Giao hàng phải đi theo đường giao thông thực tế, nên nhóm dùng OpenRouteService để lấy khoảng cách đường bộ và thời gian di chuyển phù hợp hơn.

---

# 25. Các câu hỏi phản biện khó và câu trả lời

## Câu 1: Vì sao bài toán này là TSP?

Trả lời:

> Vì bài toán yêu cầu một phương tiện xuất phát từ một điểm, đi qua mỗi địa điểm đúng một lần và tìm thứ tự di chuyển sao cho tổng quãng đường nhỏ nhất. Đây chính là cấu trúc của Traveling Salesman Problem.

## Câu 2: Tại sao không gọi là hệ thống giao hàng?

Trả lời:

> Vì phạm vi của nhóm chỉ là mô hình tối ưu thứ tự ghé thăm các địa điểm cho một phương tiện, không bao gồm phân công nhiều tài xế, tracking GPS, đơn hàng thời gian thực hay quản lý vận hành như các nền tảng lớn. Do đó gọi là ứng dụng minh họa bài toán TSP sẽ chính xác hơn.

## Câu 3: Nhóm tối ưu theo chi phí hay thời gian?

Trả lời:

> Nhóm tối ưu theo tổng quãng đường đường bộ. Vì chi phí được tính bằng tổng quãng đường nhân chi phí/km, nên giảm quãng đường sẽ giảm chi phí ước tính. Thời gian và ETA được tính để hỗ trợ đánh giá, chưa phải hàm mục tiêu chính.

## Câu 4: Vì sao dùng OpenRouteService thay vì Haversine?

Trả lời:

> Haversine chỉ tính khoảng cách đường chim bay. Bài toán giao hàng cần tuyến đường theo mạng giao thông thực tế. OpenRouteService cung cấp ma trận khoảng cách, thời gian và hình học tuyến đường bám theo đường bộ.

## Câu 5: Vì sao Brute Force đảm bảo tối ưu nhưng không dùng cho dữ liệu lớn?

Trả lời:

> Brute Force xét toàn bộ hoán vị nên chắc chắn tìm được nghiệm tốt nhất. Tuy nhiên số hoán vị tăng theo giai thừa, ví dụ 10 điểm đã có 9! = 362.880 phương án khi cố định điểm xuất phát. Với 20 điểm thì số phương án vượt xa khả năng xử lý thực tế.

## Câu 6: Nearest Neighbor có nhược điểm gì?

Trả lời:

> Nó chỉ chọn điểm gần nhất ở bước hiện tại, không xét toàn bộ tương lai của lộ trình. Vì vậy thuật toán nhanh nhưng có thể cho nghiệm chưa tối ưu.

## Câu 7: 2-opt cải thiện như thế nào?

Trả lời:

> 2-opt chọn hai cạnh trong lộ trình và đảo đoạn giữa chúng. Nếu tổng quãng đường sau khi đảo ngắn hơn thì chấp nhận. Quá trình lặp đến khi không còn cải thiện.

## Câu 8: Genetic Algorithm biểu diễn nghiệm ra sao?

Trả lời:

> Mỗi cá thể là một lộ trình, tức một hoán vị các địa điểm. Quần thể gồm nhiều lộ trình. Qua chọn lọc, lai ghép và đột biến, các lộ trình tốt hơn dần được giữ lại.

## Câu 9: Crossover trong TSP có thể gây lỗi gì?

Trả lời:

> Nếu lai ghép không kiểm soát, lộ trình con có thể bị trùng địa điểm hoặc thiếu địa điểm. Vì vậy TSP cần kiểu crossover bảo toàn hoán vị, ví dụ Order Crossover.

## Câu 10: Vì sao cần lưu lịch sử bằng SQLite?

Trả lời:

> SQLite giúp lưu kết quả chạy thuật toán bền vững sau khi tắt ứng dụng. Nhờ đó nhóm có thể so sánh các thuật toán, xuất CSV và báo cáo tiến độ dựa trên dữ liệu đã chạy.

## Câu 11: Vì sao cần chống lưu trùng?

Trả lời:

> Nếu người dùng bấm lưu nhiều lần trên cùng một kết quả, dashboard sẽ bị sai số liệu. Dùng `run_hash` kết hợp `UNIQUE` và `INSERT OR IGNORE` giúp ngăn trùng hiệu quả.

## Câu 12: Vì sao dùng `st.session_state`?

Trả lời:

> Streamlit rerun toàn bộ script khi người dùng tương tác. `session_state` giúp giữ lại dữ liệu địa điểm, kết quả tối ưu và trạng thái upload giữa các lần rerun.

## Câu 13: Vì sao dùng cache cho API?

Trả lời:

> Vì gọi API tốn thời gian và có giới hạn số request. Cache giúp tái sử dụng kết quả khi input không đổi, tăng tốc ứng dụng và giảm số lần gọi API.

## Câu 14: Ma trận khoảng cách có nhất thiết đối xứng không?

Trả lời:

> Không. Với đường bộ thực tế, đi từ A đến B và từ B về A có thể khác nhau do đường một chiều, cấm rẽ hoặc cấu trúc giao thông. Vì vậy ma trận đường bộ có thể bất đối xứng.

## Câu 15: Nếu API lỗi thì ứng dụng xử lý thế nào?

Trả lời:

> Ứng dụng bắt exception trong khối `try/except` khi chạy thuật toán và hiển thị thông báo lỗi cho người dùng. Các lỗi có thể đến từ thiếu API key, API quá giới hạn, tọa độ không tìm được đường hoặc mất mạng.

---

# 26. Cách tự học lại mã nguồn theo thứ tự

Không nên học từng dòng ngay từ đầu. Nên học theo 5 lớp.

## Lớp 1: Luồng dữ liệu

Nắm chắc:

    CSV → DataFrame → Coordinates → Matrix → Algorithm → Route → GeoJSON → ETA/Cost → Map → SQLite

## Lớp 2: Cấu trúc dữ liệu

Phải hiểu:

- DataFrame địa điểm.
- Ma trận khoảng cách.
- Ma trận thời gian.
- Route list.
- Result dictionary.
- History record.

## Lớp 3: Thuật toán

Học theo thứ tự:

    Brute Force
    → Nearest Neighbor
    → 2-opt
    → Genetic Algorithm

## Lớp 4: Giao diện và trạng thái

Học:

- `st.session_state`
- `st.cache_data`
- `st.tabs`
- `st.columns`
- `st.data_editor`
- `st.status`
- `st.rerun`

## Lớp 5: Lưu trữ và dashboard

Học:

- SQLite.
- `INSERT OR IGNORE`.
- SHA-256 hash.
- `pd.read_sql_query`.
- `groupby().agg()`.
- `to_csv()`.

---

# 27. Checklist phải tự giải thích được trước khi bảo vệ

Trước khi lên bảo vệ, mỗi thành viên cần tự trả lời được:

    [ ] TSP là gì?
    [ ] Input của bài toán là gì?
    [ ] Output của bài toán là gì?
    [ ] Hàm mục tiêu là gì?
    [ ] Vì sao tối ưu quãng đường liên quan chi phí?
    [ ] Vì sao thời gian chưa phải mục tiêu tối ưu chính?
    [ ] DataFrame địa điểm có những cột nào?
    [ ] Ma trận khoảng cách là gì?
    [ ] `distance_matrix[i][j]` nghĩa là gì?
    [ ] Vì sao dùng OpenRouteService?
    [ ] Matrix API khác Directions API thế nào?
    [ ] Brute Force chạy ra sao?
    [ ] Nearest Neighbor chạy ra sao?
    [ ] 2-opt cải thiện thế nào?
    [ ] Genetic Algorithm gồm những bước nào?
    [ ] Fitness được tính thế nào?
    [ ] Mutation để làm gì?
    [ ] Crossover phải tránh lỗi gì?
    [ ] ETA được tính như thế nào?
    [ ] Chi phí được tính như thế nào?
    [ ] SQLite lưu những trường gì?
    [ ] Vì sao cần run_hash?
    [ ] Vì sao dùng session_state?
    [ ] Vì sao dùng cache_data?
    [ ] Vì sao không commit secrets.toml?

---

# 28. Kịch bản giải thích 1 phút trước hội đồng

Có thể nói:

> Đồ án của nhóm tập trung vào bài toán tối ưu lộ trình giao hàng chặng cuối bằng mô hình Traveling Salesman Problem. Dữ liệu đầu vào là danh sách địa điểm gồm tọa độ và thời gian phục vụ. Ứng dụng dùng OpenRouteService để lấy ma trận khoảng cách và thời gian đường bộ giữa các điểm. Sau đó, các thuật toán như Brute Force, Nearest Neighbor, Genetic Algorithm và 2-opt được dùng để tìm thứ tự ghé thăm các địa điểm sao cho tổng quãng đường nhỏ nhất. Kết quả được bổ sung ETA, chi phí ước tính, bản đồ tuyến đường thực tế và lưu vào SQLite để thống kê, so sánh thuật toán. Mục tiêu chính hiện tại là tối ưu tổng quãng đường, từ đó giảm chi phí vận hành ước tính; thời gian di chuyển được dùng như chỉ số đánh giá bổ sung.

---

# 29. Kết luận kỹ thuật

Đồ án hiện tại có thể được hiểu theo ba tầng:

## Tầng bài toán

    TSP một phương tiện, nhiều địa điểm, tối ưu tổng quãng đường.

## Tầng thuật toán

    Brute Force: tối ưu tuyệt đối nhưng chậm.
    Nearest Neighbor: nhanh nhưng tham lam.
    2-opt: cải thiện cục bộ.
    Genetic Algorithm: tìm kiếm tiến hóa cho không gian nghiệm lớn.

## Tầng ứng dụng

    Streamlit giao diện
    Pandas xử lý dữ liệu
    NumPy xử lý ma trận
    OpenRouteService định tuyến đường bộ
    Folium hiển thị bản đồ
    SQLite lưu lịch sử
    Dashboard so sánh kết quả

Nếu nắm được ba tầng này, nhóm có thể bảo vệ đồ án một cách chủ động và không bị phụ thuộc vào việc học thuộc từng dòng code.
