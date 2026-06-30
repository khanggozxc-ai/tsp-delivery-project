from __future__ import annotations

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from algorithms.brute_force import solve_brute_force
from algorithms.nearest_neighbor import solve_nearest_neighbor
from services.distance_service import build_distance_matrix
from utils.validators import normalize_locations, validate_locations

st.set_page_config(
    page_title="TSP Delivery Optimizer",
    page_icon="🚚",
    layout="wide",
)

DEFAULT_DATA_PATH = "data/locations_5.csv"

def format_route(display_route: list[int], locations: pd.DataFrame) -> str:
    """
    Biến danh sách số (ví dụ: [0, 2, 1, 0]) thành chuỗi tên địa điểm trực quan
    bằng các mũi tên (ví dụ: Kho trung tâm ➔ Cửa hàng A ➔ Cửa hàng B).
    """
    if not display_route or locations.empty:
        return "Chưa có lộ trình"
    
    route_names = [locations.iloc[idx]["name"] for idx in display_route]
    return " ➔ ".join(route_names)

def load_default_data() -> pd.DataFrame:
    return pd.read_csv(DEFAULT_DATA_PATH)


def initialize_session_state() -> None:
    if "locations" not in st.session_state:
        st.session_state.locations = load_default_data()

    if "result" not in st.session_state:
        st.session_state.result = None


def render_sidebar() -> None:
    st.sidebar.title("Điều hướng")

    st.sidebar.markdown(
        """
        **Ngày 1**

        - Quản lý địa điểm
        - Brute Force
        - Nearest Neighbor
        - Bản đồ lộ trình
        """
    )


def render_data_import() -> None:
    st.subheader("1. Nhập dữ liệu")

    uploaded_file = st.file_uploader(
        "Tải danh sách địa điểm từ CSV",
        type=["csv"],
    )

    if uploaded_file is not None:
        try:
            uploaded_data = pd.read_csv(uploaded_file)
            uploaded_data = normalize_locations(uploaded_data)

            errors = validate_locations(uploaded_data)

            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state.locations = uploaded_data
                st.session_state.result = None
                st.success("Đã tải dữ liệu CSV thành công.")

        except Exception as error:
            st.error(f"Không thể đọc file CSV: {error}")

    if st.button("Khôi phục dữ liệu mẫu"):
        st.session_state.locations = load_default_data()
        st.session_state.result = None
        st.rerun()


def render_add_location_form() -> None:
    st.subheader("2. Thêm địa điểm")

    with st.form("add_location_form", clear_on_submit=True):
        column_1, column_2 = st.columns(2)

        with column_1:
            name = st.text_input("Tên địa điểm")
            latitude = st.number_input(
                "Vĩ độ",
                min_value=-90.0,
                max_value=90.0,
                value=10.762622,
                format="%.6f",
            )

        with column_2:
            longitude = st.number_input(
                "Kinh độ",
                min_value=-180.0,
                max_value=180.0,
                value=106.660172,
                format="%.6f",
            )

            service_time = st.number_input(
                "Thời gian phục vụ (phút)",
                min_value=0,
                value=5,
                step=1,
            )

        submitted = st.form_submit_button("Thêm địa điểm")

    if not submitted:
        return

    if not name.strip():
        st.error("Tên địa điểm không được để trống.")
        return

    locations = st.session_state.locations.copy()

    new_id = (
        int(locations["id"].max()) + 1
        if not locations.empty
        else 0
    )

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

    updated_locations = pd.concat(
        [locations, new_row],
        ignore_index=True,
    )

    updated_locations = normalize_locations(updated_locations)
    errors = validate_locations(updated_locations)

    if errors:
        for error in errors:
            st.error(error)
        return

    st.session_state.locations = updated_locations
    st.session_state.result = None
    st.success("Đã thêm địa điểm.")
    st.rerun()


def render_location_editor() -> None:
    st.subheader("3. Danh sách địa điểm")

    edited_locations = st.data_editor(
        st.session_state.locations,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn(
                "Mã",
                required=True,
                step=1,
            ),
            "name": st.column_config.TextColumn(
                "Tên địa điểm",
                required=True,
            ),
            "latitude": st.column_config.NumberColumn(
                "Vĩ độ",
                required=True,
                format="%.6f",
            ),
            "longitude": st.column_config.NumberColumn(
                "Kinh độ",
                required=True,
                format="%.6f",
            ),
            "service_time": st.column_config.NumberColumn(
                "Thời gian phục vụ",
                required=True,
                min_value=0,
                step=1,
            ),
        },
        key="location_editor",
    )

    if st.button("Lưu thay đổi danh sách"):
        edited_locations = normalize_locations(edited_locations)
        errors = validate_locations(edited_locations)

        if errors:
            for error in errors:
                st.error(error)
            return

        st.session_state.locations = edited_locations.reset_index(
            drop=True
        )
        st.session_state.result = None
        st.success("Đã lưu danh sách địa điểm.")
        st.rerun()


def render_algorithm_controls() -> None:
    st.subheader("4. Cấu hình lộ trình")

    locations = st.session_state.locations
    errors = validate_locations(locations)

    if errors:
        for error in errors:
            st.error(error)
        return

    location_options = {
        index: f"{row['name']} — ID {int(row['id'])}"
        for index, row in locations.iterrows()
    }

    column_1, column_2, column_3 = st.columns(3)

    with column_1:
        start_index = st.selectbox(
            "Điểm xuất phát",
            options=list(location_options.keys()),
            format_func=lambda index: location_options[index],
        )

    with column_2:
        algorithm = st.selectbox(
            "Thuật toán",
            options=[
                "Nearest Neighbor",
                "Brute Force",
            ],
        )

    with column_3:
        route_type = st.radio(
            "Loại lộ trình",
            options=[
                "Khép kín — quay về kho",
                "Mở — không quay về kho",
            ],
        )

    return_to_start = route_type.startswith("Khép kín")

    if st.button(
        "Tối ưu lộ trình",
        type="primary",
        use_container_width=True,
    ):
        try:
            distance_matrix = build_distance_matrix(locations)

            if algorithm == "Brute Force":
                result = solve_brute_force(
                    distance_matrix=distance_matrix,
                    start_index=start_index,
                    return_to_start=return_to_start,
                    max_locations=10,
                )
            else:
                result = solve_nearest_neighbor(
                    distance_matrix=distance_matrix,
                    start_index=start_index,
                    return_to_start=return_to_start,
                )

            st.session_state.result = result
            st.success("Đã hoàn thành tối ưu lộ trình.")

        except Exception as error:
            st.error(f"Không thể chạy thuật toán: {error}")


def create_route_map(
    locations: pd.DataFrame,
    display_route: list[int],
) -> folium.Map:
    route_locations = locations.iloc[display_route]

    center_latitude = float(locations["latitude"].mean())
    center_longitude = float(locations["longitude"].mean())

    route_map = folium.Map(
        location=[center_latitude, center_longitude],
        zoom_start=13,
        control_scale=True,
    )

    first_index = display_route[0]

    for order, location_index in enumerate(display_route):
        # Không vẽ lại marker kho ở cuối lộ trình khép kín.
        if order == len(display_route) - 1 and location_index == first_index:
            continue

        location = locations.iloc[location_index]
        is_start = order == 0

        marker_text = (
            f"Kho: {location['name']}"
            if is_start
            else f"Điểm {order}: {location['name']}"
        )

        folium.Marker(
            location=[
                float(location["latitude"]),
                float(location["longitude"]),
            ],
            popup=marker_text,
            tooltip=marker_text,
            icon=folium.Icon(
                color="red" if is_start else "blue",
                icon="home" if is_start else "info-sign",
            ),
        ).add_to(route_map)

    route_coordinates = [
        [
            float(row["latitude"]),
            float(row["longitude"]),
        ]
        for _, row in route_locations.iterrows()
    ]

    folium.PolyLine(
        route_coordinates,
        weight=5,
        opacity=0.8,
        tooltip="Lộ trình đề xuất",
    ).add_to(route_map)

    return route_map


def render_result() -> None:
    result = st.session_state.result

    if result is None:
        st.info("Hãy chọn thuật toán và nhấn “Tối ưu lộ trình”.")
        return

    locations = st.session_state.locations

    st.subheader("5. Kết quả")

    metric_1, metric_2, metric_3 = st.columns(3)

    with metric_1:
        st.metric(
            "Thuật toán",
            result["algorithm"],
        )

    with metric_2:
        st.metric(
            "Tổng quãng đường",
            f"{result['distance']:.3f} km",
        )

    with metric_3:
        st.metric(
            "Thời gian xử lý",
            f"{result['execution_time']:.6f} giây",
        )

    route_text = format_route(
        result["display_route"],
        locations,
    )

    st.markdown("#### Thứ tự di chuyển")
    st.success(route_text)

    if result["evaluated_routes"] is not None:
        st.write(
            "Số lộ trình đã đánh giá:",
            result["evaluated_routes"],
        )

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

    route_table.insert(
        0,
        "order",
        range(len(route_table)),
    )

    st.dataframe(
        route_table,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Bản đồ lộ trình")

    route_map = create_route_map(
        locations,
        result["display_route"],
    )

    st_folium(
        route_map,
        use_container_width=True,
        height=550,
    )


def main() -> None:
    initialize_session_state()
    render_sidebar()

    st.title("🚚 Hệ thống tối ưu lộ trình giao hàng")
    st.caption(
        "Travelling Salesman Problem — phiên bản ngày 1"
    )

    tab_data, tab_optimization = st.tabs(
        [
            "Quản lý địa điểm",
            "Tối ưu lộ trình",
        ]
    )

    with tab_data:
        render_data_import()
        st.divider()
        render_add_location_form()
        st.divider()
        render_location_editor()

    with tab_optimization:
        render_algorithm_controls()
        st.divider()
        render_result()


if __name__ == "__main__":
    main()
