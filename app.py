from __future__ import annotations

from datetime import datetime

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from algorithms.brute_force import solve_brute_force
from algorithms.genetic_algorithm import solve_genetic_algorithm
from algorithms.nearest_neighbor import solve_nearest_neighbor
from algorithms.two_opt import solve_two_opt_from_result
from services.delivery_service import (
    build_eta_table,
    calculate_delivery_cost,
)
from services.distance_service import build_distance_matrix
from utils.validators import (
    normalize_locations,
    validate_locations,
)


st.set_page_config(
    page_title="TSP Delivery Optimizer",
    page_icon="🚚",
    layout="wide",
)


DEFAULT_DATA_PATH = "data/locations_5.csv"

ALGORITHM_OPTIONS = [
    "Nearest Neighbor",
    "Nearest Neighbor + 2-opt",
    "Brute Force",
    "Genetic Algorithm",
    "Genetic Algorithm + 2-opt",
]


def format_route(
    display_route: list[int],
    locations: pd.DataFrame,
) -> str:
    """
    Chuyển danh sách chỉ số địa điểm thành chuỗi tên.
    """

    if not display_route or locations.empty:
        return "Chưa có lộ trình"

    route_names = [
        str(locations.iloc[index]["name"])
        for index in display_route
    ]

    return " → ".join(route_names)


def format_duration(total_minutes: float) -> str:
    """
    Định dạng thời gian từ số phút sang giờ và phút.
    """

    total_minutes = max(0.0, float(total_minutes))

    hours = int(total_minutes // 60)
    minutes = int(round(total_minutes % 60))

    if minutes == 60:
        hours += 1
        minutes = 0

    if hours == 0:
        return f"{minutes} phút"

    return f"{hours} giờ {minutes} phút"


def load_default_data() -> pd.DataFrame:
    """
    Đọc bộ dữ liệu mẫu mặc định.
    """

    return pd.read_csv(DEFAULT_DATA_PATH)


def initialize_session_state() -> None:
    """
    Khởi tạo dữ liệu dùng xuyên suốt phiên Streamlit.
    """

    if "locations" not in st.session_state:
        st.session_state.locations = load_default_data()

    if "result" not in st.session_state:
        st.session_state.result = None


def render_sidebar() -> None:
    """
    Hiển thị thanh điều hướng bên trái.
    """

    st.sidebar.title("Điều hướng")

    st.sidebar.markdown(
        """
        **Ngày 1**

        - Quản lý địa điểm
        - Brute Force
        - Nearest Neighbor
        - Bản đồ lộ trình

        **Ngày 2**

        - Genetic Algorithm
        - 2-opt
        - ETA
        - Chi phí giao hàng
        - Biểu đồ hội tụ
        """
    )


def render_data_import() -> None:
    """
    Nhập dữ liệu từ file CSV.
    """

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

                st.success(
                    "Đã tải dữ liệu CSV thành công."
                )

        except Exception as error:
            st.error(
                f"Không thể đọc file CSV: {error}"
            )

    if st.button("Khôi phục dữ liệu mẫu"):
        st.session_state.locations = load_default_data()
        st.session_state.result = None
        st.rerun()


def render_add_location_form() -> None:
    """
    Form thêm một địa điểm mới.
    """

    st.subheader("2. Thêm địa điểm")

    with st.form(
        "add_location_form",
        clear_on_submit=True,
    ):
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

        submitted = st.form_submit_button(
            "Thêm địa điểm"
        )

    if not submitted:
        return

    if not name.strip():
        st.error(
            "Tên địa điểm không được để trống."
        )
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

    updated_locations = normalize_locations(
        updated_locations
    )

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
    """
    Bảng cho phép sửa và xóa địa điểm.
    """

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
            "latitude": (
                st.column_config.NumberColumn(
                    "Vĩ độ",
                    required=True,
                    format="%.6f",
                )
            ),
            "longitude": (
                st.column_config.NumberColumn(
                    "Kinh độ",
                    required=True,
                    format="%.6f",
                )
            ),
            "service_time": (
                st.column_config.NumberColumn(
                    "Thời gian phục vụ",
                    required=True,
                    min_value=0,
                    step=1,
                )
            ),
        },
        key="location_editor",
    )

    if st.button("Lưu thay đổi danh sách"):
        edited_locations = normalize_locations(
            edited_locations
        )

        errors = validate_locations(
            edited_locations
        )

        if errors:
            for error in errors:
                st.error(error)
            return

        st.session_state.locations = (
            edited_locations.reset_index(drop=True)
        )

        st.session_state.result = None

        st.success(
            "Đã lưu danh sách địa điểm."
        )

        st.rerun()


def run_selected_algorithm(
    algorithm: str,
    distance_matrix,
    start_index: int,
    return_to_start: bool,
    ga_parameters: dict[str, int | float],
) -> dict:
    """
    Chạy thuật toán mà người dùng lựa chọn.
    """

    if algorithm == "Brute Force":
        return solve_brute_force(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
            max_locations=10,
        )

    if algorithm == "Nearest Neighbor":
        return solve_nearest_neighbor(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
        )

    if algorithm == "Nearest Neighbor + 2-opt":
        base_result = solve_nearest_neighbor(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
        )

        result = solve_two_opt_from_result(
            base_result=base_result,
            distance_matrix=distance_matrix,
            algorithm_name=(
                "Nearest Neighbor + 2-opt"
            ),
        )

        result["base_evaluated_routes"] = (
            base_result.get("evaluated_routes")
        )

        return result

    if algorithm == "Genetic Algorithm":
        return solve_genetic_algorithm(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
            population_size=int(
                ga_parameters["population_size"]
            ),
            generations=int(
                ga_parameters["generations"]
            ),
            crossover_rate=float(
                ga_parameters["crossover_rate"]
            ),
            mutation_rate=float(
                ga_parameters["mutation_rate"]
            ),
            tournament_size=int(
                ga_parameters["tournament_size"]
            ),
            elite_size=int(
                ga_parameters["elite_size"]
            ),
            random_seed=int(
                ga_parameters["random_seed"]
            ),
        )

    if algorithm == "Genetic Algorithm + 2-opt":
        base_result = solve_genetic_algorithm(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
            population_size=int(
                ga_parameters["population_size"]
            ),
            generations=int(
                ga_parameters["generations"]
            ),
            crossover_rate=float(
                ga_parameters["crossover_rate"]
            ),
            mutation_rate=float(
                ga_parameters["mutation_rate"]
            ),
            tournament_size=int(
                ga_parameters["tournament_size"]
            ),
            elite_size=int(
                ga_parameters["elite_size"]
            ),
            random_seed=int(
                ga_parameters["random_seed"]
            ),
        )

        result = solve_two_opt_from_result(
            base_result=base_result,
            distance_matrix=distance_matrix,
            algorithm_name=(
                "Genetic Algorithm + 2-opt"
            ),
        )

        result["base_evaluated_routes"] = (
            base_result.get("evaluated_routes")
        )

        return result

    raise ValueError(
        f"Thuật toán không được hỗ trợ: {algorithm}"
    )


def enrich_result_with_delivery_information(
    result: dict,
    locations: pd.DataFrame,
    distance_matrix,
    departure_datetime: datetime,
    average_speed_kmh: float,
    cost_per_km: float,
) -> dict:
    """
    Bổ sung ETA, tổng thời gian và chi phí vào kết quả.
    """

    eta_table, total_duration_minutes = (
        build_eta_table(
            display_route=result["display_route"],
            locations=locations,
            distance_matrix=distance_matrix,
            departure_datetime=departure_datetime,
            average_speed_kmh=average_speed_kmh,
        )
    )

    delivery_cost = calculate_delivery_cost(
        total_distance=result["distance"],
        cost_per_km=cost_per_km,
    )

    enriched_result = result.copy()

    enriched_result["eta_table"] = eta_table

    enriched_result["total_duration_minutes"] = (
        total_duration_minutes
    )

    enriched_result["delivery_cost"] = (
        delivery_cost
    )

    enriched_result["average_speed_kmh"] = (
        average_speed_kmh
    )

    enriched_result["cost_per_km"] = (
        cost_per_km
    )

    enriched_result["departure_datetime"] = (
        departure_datetime
    )

    return enriched_result


def render_algorithm_controls() -> None:
    """
    Hiển thị toàn bộ cấu hình tối ưu.
    """

    st.subheader("4. Cấu hình lộ trình")

    locations = st.session_state.locations

    errors = validate_locations(locations)

    if errors:
        for error in errors:
            st.error(error)
        return

    location_options = {
        index: (
            f"{row['name']} — ID {int(row['id'])}"
        )
        for index, row in locations.iterrows()
    }

    option_indices = list(location_options.keys())

    default_start_position = 0

    depot_rows = locations.index[
        locations["id"] == 0
    ].tolist()

    if depot_rows:
        depot_index = depot_rows[0]

        if depot_index in option_indices:
            default_start_position = (
                option_indices.index(depot_index)
            )

    column_1, column_2, column_3 = st.columns(3)

    with column_1:
        start_index = st.selectbox(
            "Điểm xuất phát",
            options=option_indices,
            index=default_start_position,
            format_func=lambda index: (
                location_options[index]
            ),
        )

    with column_2:
        algorithm = st.selectbox(
            "Thuật toán",
            options=ALGORITHM_OPTIONS,
        )

    with column_3:
        route_type = st.radio(
            "Loại lộ trình",
            options=[
                "Khép kín — quay về điểm đầu",
                "Mở — không quay về điểm đầu",
            ],
        )

    return_to_start = route_type.startswith(
        "Khép kín"
    )

    st.markdown("#### Thông tin vận hành")

    operation_column_1, operation_column_2, (
        operation_column_3
    ) = st.columns(3)

    with operation_column_1:
        average_speed_kmh = st.number_input(
            "Tốc độ trung bình (km/h)",
            min_value=1.0,
            max_value=150.0,
            value=30.0,
            step=1.0,
        )

    with operation_column_2:
        cost_per_km = st.number_input(
            "Chi phí mỗi kilomet (VNĐ)",
            min_value=0.0,
            value=2000.0,
            step=500.0,
        )

    with operation_column_3:
        departure_time = st.time_input(
            "Giờ xuất phát",
            value=datetime.now().time().replace(
                second=0,
                microsecond=0,
            ),
        )

    ga_parameters: dict[str, int | float] = {
        "population_size": 100,
        "generations": 300,
        "crossover_rate": 0.8,
        "mutation_rate": 0.05,
        "tournament_size": 5,
        "elite_size": 2,
        "random_seed": 42,
    }

    if "Genetic Algorithm" in algorithm:
        with st.expander(
            "Cấu hình Genetic Algorithm",
            expanded=True,
        ):
            ga_column_1, ga_column_2, (
                ga_column_3
            ) = st.columns(3)

            with ga_column_1:
                population_size = st.number_input(
                    "Kích thước quần thể",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    step=10,
                )

                generations = st.number_input(
                    "Số thế hệ",
                    min_value=10,
                    max_value=5000,
                    value=300,
                    step=50,
                )

            with ga_column_2:
                crossover_rate = st.number_input(
                    "Tỷ lệ lai ghép",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.8,
                    step=0.05,
                    format="%.2f",
                )

                mutation_rate = st.number_input(
                    "Tỷ lệ đột biến",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.05,
                    step=0.01,
                    format="%.2f",
                )

            with ga_column_3:
                tournament_size = st.number_input(
                    "Tournament size",
                    min_value=2,
                    max_value=int(
                        population_size
                    ),
                    value=min(
                        5,
                        int(population_size),
                    ),
                    step=1,
                )

                elite_size = st.number_input(
                    "Số cá thể ưu tú",
                    min_value=0,
                    max_value=max(
                        0,
                        int(population_size) - 1,
                    ),
                    value=min(
                        2,
                        int(population_size) - 1,
                    ),
                    step=1,
                )

                random_seed = st.number_input(
                    "Random seed",
                    min_value=0,
                    value=42,
                    step=1,
                )

            ga_parameters = {
                "population_size": int(
                    population_size
                ),
                "generations": int(generations),
                "crossover_rate": float(
                    crossover_rate
                ),
                "mutation_rate": float(
                    mutation_rate
                ),
                "tournament_size": int(
                    tournament_size
                ),
                "elite_size": int(elite_size),
                "random_seed": int(random_seed),
            }

    st.caption(
        "Khoảng cách hiện được ước tính theo "
        "đường chim bay giữa các tọa độ."
    )

    if st.button(
        "Tối ưu lộ trình",
        type="primary",
        use_container_width=True,
    ):
        try:
            distance_matrix = (
                build_distance_matrix(locations)
            )

            result = run_selected_algorithm(
                algorithm=algorithm,
                distance_matrix=distance_matrix,
                start_index=start_index,
                return_to_start=return_to_start,
                ga_parameters=ga_parameters,
            )

            departure_datetime = datetime.combine(
                datetime.now().date(),
                departure_time,
            )

            result = (
                enrich_result_with_delivery_information(
                    result=result,
                    locations=locations,
                    distance_matrix=distance_matrix,
                    departure_datetime=(
                        departure_datetime
                    ),
                    average_speed_kmh=float(
                        average_speed_kmh
                    ),
                    cost_per_km=float(
                        cost_per_km
                    ),
                )
            )

            st.session_state.result = result

            st.success(
                "Đã hoàn thành tối ưu lộ trình."
            )

        except Exception as error:
            st.error(
                f"Không thể chạy thuật toán: {error}"
            )


def create_route_map(
    locations: pd.DataFrame,
    display_route: list[int],
) -> folium.Map:
    """
    Tạo bản đồ lộ trình bằng Folium.
    """

    route_locations = locations.iloc[
        display_route
    ]

    center_latitude = float(
        locations["latitude"].mean()
    )

    center_longitude = float(
        locations["longitude"].mean()
    )

    route_map = folium.Map(
        location=[
            center_latitude,
            center_longitude,
        ],
        zoom_start=13,
        control_scale=True,
    )

    first_index = display_route[0]

    for order, location_index in enumerate(
        display_route
    ):
        is_return_marker = (
            order == len(display_route) - 1
            and order > 0
            and location_index == first_index
        )

        if is_return_marker:
            continue

        location = locations.iloc[
            location_index
        ]

        is_start = order == 0

        marker_text = (
            f"Điểm xuất phát: {location['name']}"
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
                color=(
                    "red"
                    if is_start
                    else "blue"
                ),
                icon=(
                    "home"
                    if is_start
                    else "info-sign"
                ),
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

    if route_coordinates:
        route_map.fit_bounds(
            route_coordinates
        )

    return route_map


def render_convergence_chart(result: dict) -> None:
    """
    Hiển thị biểu đồ hội tụ của GA.
    """

    history = result.get("history", [])

    if not history:
        return

    st.markdown(
        "#### Biểu đồ hội tụ"
    )

    convergence_data = pd.DataFrame(
        {
            "Thế hệ": range(
                1,
                len(history) + 1,
            ),
            "Khoảng cách tốt nhất (km)": (
                history
            ),
        }
    )

    convergence_data = (
        convergence_data.set_index("Thế hệ")
    )

    st.line_chart(
        convergence_data,
        use_container_width=True,
    )

    st.caption(
        "Đường biểu diễn giá trị tốt nhất "
        "được tìm thấy qua từng thế hệ."
    )


def render_two_opt_information(
    result: dict,
) -> None:
    """
    Hiển thị mức cải thiện của 2-opt.
    """

    if "improvement_percentage" not in result:
        return

    st.markdown(
        "#### Hiệu quả cải thiện của 2-opt"
    )

    column_1, column_2, column_3 = (
        st.columns(3)
    )

    with column_1:
        st.metric(
            "Trước 2-opt",
            (
                f"{result['original_distance']:.3f} km"
            ),
        )

    with column_2:
        st.metric(
            "Sau 2-opt",
            f"{result['distance']:.3f} km",
        )

    with column_3:
        st.metric(
            "Tỷ lệ cải thiện",
            (
                f"{result['improvement_percentage']:.2f}%"
            ),
            delta=(
                f"-{result['improvement_distance']:.3f} km"
            ),
        )


def render_eta_information(
    result: dict,
) -> None:
    """
    Hiển thị bảng thời gian đến dự kiến.
    """

    eta_table = result.get("eta_table")

    if eta_table is None:
        return

    st.markdown(
        "#### Thời gian giao hàng dự kiến"
    )

    eta_display = eta_table.rename(
        columns={
            "order": "Thứ tự",
            "location_id": "Mã",
            "location_name": "Địa điểm",
            "segment_distance_km": (
                "Quãng đường chặng (km)"
            ),
            "travel_time_minutes": (
                "Di chuyển (phút)"
            ),
            "arrival_time": "Đến dự kiến",
            "service_time_minutes": (
                "Phục vụ (phút)"
            ),
            "departure_time": "Rời đi",
        }
    )

    st.dataframe(
        eta_display,
        use_container_width=True,
        hide_index=True,
    )


def render_result() -> None:
    """
    Hiển thị kết quả tối ưu.
    """

    result = st.session_state.result

    if result is None:
        st.info(
            "Hãy chọn thuật toán và nhấn "
            "“Tối ưu lộ trình”."
        )
        return

    locations = st.session_state.locations

    st.subheader("5. Kết quả")

    metric_1, metric_2, metric_3, (
        metric_4
    ) = st.columns(4)

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
            (
                f"{result['execution_time']:.6f} giây"
            ),
        )

    with metric_4:
        st.metric(
            "Chi phí dự kiến",
            (
                f"{result['delivery_cost']:,.0f} VNĐ"
            ),
        )

    duration_column, speed_column, (
        departure_column
    ) = st.columns(3)

    with duration_column:
        st.metric(
            "Tổng thời gian dự kiến",
            format_duration(
                result["total_duration_minutes"]
            ),
        )

    with speed_column:
        st.metric(
            "Tốc độ giả định",
            (
                f"{result['average_speed_kmh']:.1f} km/h"
            ),
        )

    with departure_column:
        departure_datetime = result[
            "departure_datetime"
        ]

        st.metric(
            "Giờ xuất phát",
            departure_datetime.strftime(
                "%H:%M"
            ),
        )

    route_text = format_route(
        result["display_route"],
        locations,
    )

    st.markdown("#### Thứ tự di chuyển")
    st.success(route_text)

    evaluated_routes = result.get(
        "evaluated_routes"
    )

    if evaluated_routes is not None:
        st.write(
            "Số phương án đã đánh giá:",
            f"{int(evaluated_routes):,}",
        )

    parameters = result.get("parameters")

    if parameters:
        with st.expander(
            "Tham số Genetic Algorithm"
        ):
            parameter_table = pd.DataFrame(
                [
                    {
                        "Tham số": key,
                        "Giá trị": value,
                    }
                    for key, value
                    in parameters.items()
                ]
            )

            st.dataframe(
                parameter_table,
                use_container_width=True,
                hide_index=True,
            )

    render_two_opt_information(result)
    render_convergence_chart(result)
    render_eta_information(result)

    st.markdown("#### Chi tiết lộ trình")

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

    route_table = route_table.rename(
        columns={
            "order": "Thứ tự",
            "id": "Mã",
            "name": "Tên địa điểm",
            "latitude": "Vĩ độ",
            "longitude": "Kinh độ",
            "service_time": (
                "Thời gian phục vụ"
            ),
        }
    )

    st.dataframe(
        route_table,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Bản đồ lộ trình")

    route_map = create_route_map(
        locations=locations,
        display_route=result[
            "display_route"
        ],
    )

    st_folium(
        route_map,
        use_container_width=True,
        height=550,
    )


def main() -> None:
    initialize_session_state()
    render_sidebar()

    st.title(
        "🚚 Hệ thống tối ưu lộ trình giao hàng"
    )

    st.caption(
        "Travelling Salesman Problem — "
        "Genetic Algorithm và 2-opt"
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