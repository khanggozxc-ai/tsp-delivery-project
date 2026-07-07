from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from database.history_repository import (
    delete_all_history,
    delete_history_record,
    fetch_history,
)


def _to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8-sig")


def _parse_ga_parameters(value: Any) -> dict[str, Any]:
    if value is None or value == "":
        return {}

    if isinstance(value, dict):
        return value

    try:
        parsed = json.loads(str(value))
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        return {}

    return {}


def _enrich_with_ga_parameters(history: pd.DataFrame) -> pd.DataFrame:
    data = history.copy()

    parameter_rows = [
        _parse_ga_parameters(value)
        for value in data.get("ga_parameters", [])
    ]

    parameter_frame = pd.DataFrame(parameter_rows)

    expected_columns = [
        "population_size",
        "generations",
        "crossover_rate",
        "mutation_rate",
        "tournament_size",
        "elite_size",
        "random_seed",
    ]

    for column in expected_columns:
        if column not in parameter_frame.columns:
            parameter_frame[column] = None

    for column in expected_columns:
        data[column] = pd.to_numeric(
            parameter_frame[column],
            errors="coerce",
        )

    return data


def _format_history_table(history: pd.DataFrame) -> pd.DataFrame:
    display_columns = {
        "id": "ID",
        "created_at": "Thời điểm lưu",
        "location_count": "Số điểm",
        "route_type": "Loại lộ trình",
        "distance_km": "Quãng đường (km)",
        "matrix_distance_km": "Quãng đường ma trận (km)",
        "execution_time_seconds": "Thời gian xử lý (giây)",
        "delivery_cost": "Chi phí (VNĐ)",
        "population_size": "Population",
        "generations": "Generations",
        "crossover_rate": "Crossover",
        "mutation_rate": "Mutation",
        "tournament_size": "Tournament",
        "elite_size": "Elite",
        "random_seed": "Seed",
        "vehicle_label": "Phương tiện",
    }

    columns = [
        column for column in display_columns
        if column in history.columns
    ]

    formatted = history[columns].copy()
    formatted = formatted.rename(columns=display_columns)

    round_rules = {
        "Quãng đường (km)": 3,
        "Quãng đường ma trận (km)": 3,
        "Thời gian xử lý (giây)": 6,
        "Chi phí (VNĐ)": 0,
        "Crossover": 2,
        "Mutation": 2,
    }

    for column, decimals in round_rules.items():
        if column in formatted.columns:
            formatted[column] = formatted[column].round(decimals)

    return formatted


def _build_group_summary(
    history: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    if group_column not in history.columns:
        return pd.DataFrame()

    valid = history.dropna(subset=[group_column]).copy()

    if valid.empty:
        return pd.DataFrame()

    summary = (
        valid.groupby(group_column, as_index=False)
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
        .sort_values(group_column)
    )

    return summary


def _render_parameter_summary(
    history: pd.DataFrame,
    group_column: str,
    title: str,
    explanation: str,
) -> None:
    st.markdown(f"#### {title}")
    st.caption(explanation)

    summary = _build_group_summary(history, group_column)

    if summary.empty:
        st.info("Chưa đủ dữ liệu để thống kê tham số này.")
        return

    display = summary.rename(
        columns={
            group_column: "Giá trị tham số",
            "so_lan_chay": "Số lần chạy",
            "quang_duong_trung_binh": "Quãng đường TB (km)",
            "quang_duong_tot_nhat": "Quãng đường tốt nhất (km)",
            "thoi_gian_xu_ly_trung_binh": "Thời gian xử lý TB (giây)",
            "chi_phi_trung_binh": "Chi phí TB (VNĐ)",
        }
    )

    numeric_columns = [
        "Quãng đường TB (km)",
        "Quãng đường tốt nhất (km)",
        "Thời gian xử lý TB (giây)",
        "Chi phí TB (VNĐ)",
    ]

    for column in numeric_columns:
        if column in display.columns:
            display[column] = display[column].round(4)

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
    )

    chart_data = summary.set_index(group_column)[[
        "quang_duong_tot_nhat",
        "thoi_gian_xu_ly_trung_binh",
    ]]

    chart_col_1, chart_col_2 = st.columns(2)

    with chart_col_1:
        st.markdown("**Quãng đường tốt nhất theo tham số**")
        st.bar_chart(chart_data[["quang_duong_tot_nhat"]])

    with chart_col_2:
        st.markdown("**Thời gian xử lý trung bình theo tham số**")
        st.bar_chart(chart_data[["thoi_gian_xu_ly_trung_binh"]])


def render_ga_experiment_dashboard() -> None:
    """Dashboard khảo sát ảnh hưởng siêu tham số của Genetic Algorithm."""

    st.subheader("Khảo sát thực nghiệm Genetic Algorithm")
    st.caption(
        "Tab này dùng lịch sử chạy được lưu bằng SQLite để phân tích ảnh hưởng "
        "của các siêu tham số GA đến chất lượng nghiệm và thời gian tính toán."
    )

    history = fetch_history("Genetic Algorithm")

    if history.empty:
        st.info(
            "Chưa có kết quả GA nào trong lịch sử. Hãy chạy Genetic Algorithm "
            "với vài cấu hình khác nhau và lưu kết quả để khảo sát thực nghiệm."
        )
        return

    history = _enrich_with_ga_parameters(history)

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Số lần chạy GA", f"{len(history):,}")
    metric_2.metric(
        "Quãng đường tốt nhất",
        f"{history['distance_km'].min():.3f} km",
    )
    metric_3.metric(
        "Thời gian xử lý TB",
        f"{history['execution_time_seconds'].mean():.6f} giây",
    )
    metric_4.metric(
        "Số cấu hình đã thử",
        f"{history['ga_parameters'].nunique():,}",
    )

    st.markdown("#### Bảng lịch sử chạy Genetic Algorithm")
    st.dataframe(
        _format_history_table(history),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Trade-off giữa chất lượng nghiệm và thời gian tính toán")
    st.caption(
        "Trong AI, tăng số thế hệ hoặc kích thước quần thể thường làm thời gian "
        "xử lý tăng, nhưng có thể giúp khảo sát không gian nghiệm kỹ hơn và tìm "
        "lộ trình ngắn hơn. Đây là đánh đổi giữa chi phí tính toán và chất lượng nghiệm."
    )

    tradeoff_data = history[[
        "execution_time_seconds",
        "distance_km",
        "population_size",
        "generations",
    ]].dropna()

    if not tradeoff_data.empty:
        st.scatter_chart(
            tradeoff_data,
            x="execution_time_seconds",
            y="distance_km",
            size="population_size",
            color="generations",
            use_container_width=True,
        )
    else:
        st.info("Chưa đủ dữ liệu để vẽ trade-off chart.")

    _render_parameter_summary(
        history=history,
        group_column="population_size",
        title="Ảnh hưởng của kích thước quần thể",
        explanation=(
            "Population size lớn hơn giúp GA duy trì nhiều lộ trình ứng viên hơn "
            "trong mỗi thế hệ, nhưng làm tăng số phép đánh giá fitness."
        ),
    )

    _render_parameter_summary(
        history=history,
        group_column="generations",
        title="Ảnh hưởng của số thế hệ",
        explanation=(
            "Số thế hệ càng lớn, quá trình tiến hóa có thêm thời gian hội tụ, "
            "nhưng tổng thời gian xử lý cũng tăng."
        ),
    )

    _render_parameter_summary(
        history=history,
        group_column="mutation_rate",
        title="Ảnh hưởng của tỷ lệ đột biến",
        explanation=(
            "Mutation rate điều khiển mức đa dạng di truyền. Tỷ lệ quá thấp có thể "
            "dễ kẹt local optimum, còn quá cao có thể làm quá trình hội tụ kém ổn định."
        ),
    )

    st.markdown("#### Xuất dữ liệu thực nghiệm")
    st.download_button(
        "Tải lịch sử GA dạng CSV",
        data=_to_csv_bytes(history),
        file_name="ga_experiment_history.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("#### Quản lý dữ liệu thực nghiệm")
    delete_column_1, delete_column_2 = st.columns(2)

    with delete_column_1:
        record_options = {
            int(row["id"]): (
                f"ID {int(row['id'])} — "
                f"pop={int(row['population_size']) if pd.notna(row['population_size']) else 'NA'} — "
                f"gen={int(row['generations']) if pd.notna(row['generations']) else 'NA'} — "
                f"{float(row['distance_km']):.3f} km"
            )
            for _, row in history.iterrows()
        }

        selected_record_id = st.selectbox(
            "Chọn bản ghi cần xóa",
            options=list(record_options.keys()),
            format_func=lambda record_id: record_options[record_id],
            key="ga_experiment_record_to_delete",
        )

        if st.button("Xóa bản ghi đã chọn", use_container_width=True):
            deleted = delete_history_record(int(selected_record_id))

            if deleted:
                st.success("Đã xóa bản ghi thực nghiệm.")
                st.rerun()
            else:
                st.warning("Không tìm thấy bản ghi cần xóa.")

    with delete_column_2:
        confirm_delete_all = st.checkbox(
            "Tôi xác nhận muốn xóa toàn bộ lịch sử GA",
            key="ga_experiment_confirm_delete_all",
        )

        if st.button(
            "Xóa toàn bộ lịch sử",
            use_container_width=True,
            disabled=not confirm_delete_all,
        ):
            deleted_count = delete_all_history()
            st.success(f"Đã xóa {deleted_count} bản ghi lịch sử.")
            st.rerun()
