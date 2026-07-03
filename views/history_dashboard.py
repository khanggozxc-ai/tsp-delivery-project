from __future__ import annotations

import pandas as pd
import streamlit as st

from database.history_repository import (
    delete_all_history,
    delete_history_record,
    fetch_history,
    list_algorithms,
)


def _format_history_table(history: pd.DataFrame) -> pd.DataFrame:
    display_columns = {
        "id": "ID",
        "created_at": "Thời điểm lưu",
        "algorithm": "Thuật toán",
        "route_type": "Loại lộ trình",
        "location_count": "Số địa điểm",
        "route_names": "Lộ trình",
        "distance_km": "Quãng đường (km)",
        "execution_time_seconds": "Thời gian xử lý (giây)",
        "delivery_cost": "Chi phí (VNĐ)",
        "total_duration_minutes": "Tổng thời gian (phút)",
        "vehicle_label": "Phương tiện",
    }

    available_columns = [
        column for column in display_columns if column in history.columns
    ]

    formatted = history[available_columns].copy()
    formatted = formatted.rename(columns=display_columns)

    if "Quãng đường (km)" in formatted:
        formatted["Quãng đường (km)"] = formatted[
            "Quãng đường (km)"
        ].round(3)

    if "Thời gian xử lý (giây)" in formatted:
        formatted["Thời gian xử lý (giây)"] = formatted[
            "Thời gian xử lý (giây)"
        ].round(6)

    if "Chi phí (VNĐ)" in formatted:
        formatted["Chi phí (VNĐ)"] = formatted["Chi phí (VNĐ)"].round(0)

    if "Tổng thời gian (phút)" in formatted:
        formatted["Tổng thời gian (phút)"] = formatted[
            "Tổng thời gian (phút)"
        ].round(2)

    return formatted


def _to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8-sig")


def render_history_dashboard() -> None:
    """Hiển thị lịch sử, thống kê, biểu đồ, xuất và xóa dữ liệu."""

    st.subheader("Lịch sử và thống kê kết quả")
    st.caption(
        "Dữ liệu được lưu cục bộ bằng SQLite và vẫn còn sau khi "
        "khởi động lại ứng dụng."
    )

    algorithm_options = ["Tất cả", *list_algorithms()]

    selected_algorithm = st.selectbox(
        "Lọc theo thuật toán",
        options=algorithm_options,
        key="history_algorithm_filter",
    )

    history = fetch_history(selected_algorithm)

    if history.empty:
        st.info("Chưa có kết quả nào được lưu trong lịch sử.")
        return

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

    metric_1.metric("Số lần chạy", f"{len(history):,}")
    metric_2.metric(
        "Quãng đường tốt nhất",
        f"{history['distance_km'].min():.3f} km",
    )
    metric_3.metric(
        "Chi phí trung bình",
        f"{history['delivery_cost'].mean():,.0f} VNĐ",
    )
    metric_4.metric(
        "Thời gian xử lý nhanh nhất",
        f"{history['execution_time_seconds'].min():.6f} giây",
    )

    st.markdown("#### Danh sách lịch sử")
    st.dataframe(
        _format_history_table(history),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### So sánh thuật toán")

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

    comparison_display = comparison.rename(
        columns={
            "algorithm": "Thuật toán",
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
    comparison_display[numeric_columns] = comparison_display[
        numeric_columns
    ].round(4)

    st.dataframe(
        comparison_display,
        use_container_width=True,
        hide_index=True,
    )

    chart_column_1, chart_column_2 = st.columns(2)

    with chart_column_1:
        st.markdown("**Quãng đường trung bình**")
        distance_chart = comparison.set_index("algorithm")[[
            "quang_duong_trung_binh"
        ]]
        st.bar_chart(distance_chart)

    with chart_column_2:
        st.markdown("**Thời gian xử lý trung bình**")
        execution_chart = comparison.set_index("algorithm")[[
            "thoi_gian_xu_ly_trung_binh"
        ]]
        st.bar_chart(execution_chart)

    st.markdown("#### Xuất dữ liệu")
    st.download_button(
        "Tải lịch sử dạng CSV",
        data=_to_csv_bytes(history),
        file_name="tsp_optimization_history.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("#### Quản lý dữ liệu lịch sử")

    delete_column_1, delete_column_2 = st.columns(2)

    with delete_column_1:
        record_options = {
            int(row["id"]): (
                f"ID {int(row['id'])} — {row['algorithm']} — "
                f"{float(row['distance_km']):.3f} km"
            )
            for _, row in history.iterrows()
        }

        selected_record_id = st.selectbox(
            "Chọn bản ghi cần xóa",
            options=list(record_options.keys()),
            format_func=lambda record_id: record_options[record_id],
            key="history_record_to_delete",
        )

        if st.button(
            "Xóa bản ghi đã chọn",
            use_container_width=True,
        ):
            deleted = delete_history_record(int(selected_record_id))

            if deleted:
                st.success("Đã xóa bản ghi lịch sử.")
                st.rerun()
            else:
                st.warning("Không tìm thấy bản ghi cần xóa.")

    with delete_column_2:
        confirm_delete_all = st.checkbox(
            "Tôi xác nhận muốn xóa toàn bộ lịch sử",
            key="confirm_delete_all_history",
        )

        if st.button(
            "Xóa toàn bộ lịch sử",
            type="secondary",
            use_container_width=True,
            disabled=not confirm_delete_all,
        ):
            deleted_count = delete_all_history()
            st.success(f"Đã xóa {deleted_count} bản ghi lịch sử.")
            st.rerun()
