from __future__ import annotations

from datetime import datetime, timedelta
from typing import Sequence

import numpy as np
import pandas as pd


def calculate_delivery_cost(
    total_distance: float,
    cost_per_km: float,
) -> float:
    """
    Tính chi phí giao hàng theo tổng quãng đường.
    """

    if total_distance < 0:
        raise ValueError("Tổng quãng đường không được âm.")

    if cost_per_km < 0:
        raise ValueError("Chi phí mỗi kilomet không được âm.")

    return float(total_distance * cost_per_km)


def build_eta_table(
    display_route: Sequence[int],
    locations: pd.DataFrame,
    distance_matrix: np.ndarray,
    departure_datetime: datetime,
    average_speed_kmh: float,
) -> tuple[pd.DataFrame, float]:
    """
    Hàm ETA cũ, giữ lại để tương thích với các phần code trước đây.

    Thời gian di chuyển được ước tính bằng:
        khoảng cách / tốc độ trung bình
    """

    if not display_route:
        raise ValueError("Lộ trình đang trống.")

    if average_speed_kmh <= 0:
        raise ValueError("Tốc độ trung bình phải lớn hơn 0.")

    rows: list[dict[str, object]] = []
    elapsed_minutes = 0.0
    first_location_index = display_route[0]

    for order, location_index in enumerate(display_route):
        location = locations.iloc[location_index]

        if order == 0:
            segment_distance = 0.0
            travel_minutes = 0.0
        else:
            previous_location_index = display_route[order - 1]

            segment_distance = float(
                distance_matrix[
                    previous_location_index
                ][location_index]
            )

            travel_minutes = (
                segment_distance / average_speed_kmh
            ) * 60.0

            elapsed_minutes += travel_minutes

        arrival_datetime = (
            departure_datetime
            + timedelta(minutes=elapsed_minutes)
        )

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

        departure_from_location = (
            arrival_datetime
            + timedelta(minutes=service_time)
        )

        rows.append(
            {
                "order": order,
                "location_id": int(location["id"]),
                "location_name": str(location["name"]),
                "segment_distance_km": round(
                    segment_distance,
                    3,
                ),
                "travel_time_minutes": round(
                    travel_minutes,
                    2,
                ),
                "arrival_time": arrival_datetime.strftime(
                    "%H:%M:%S"
                ),
                "service_time_minutes": service_time,
                "departure_time": (
                    departure_from_location.strftime(
                        "%H:%M:%S"
                    )
                ),
            }
        )

        elapsed_minutes += service_time

    return pd.DataFrame(rows), float(elapsed_minutes)


def build_road_eta_table(
    display_route: Sequence[int],
    locations: pd.DataFrame,
    distance_matrix_km: np.ndarray,
    duration_matrix_seconds: np.ndarray,
    departure_datetime: datetime,
) -> tuple[pd.DataFrame, float]:
    """
    Tạo bảng ETA dựa trên khoảng cách và thời gian đường bộ.

    distance_matrix_km:
        Ma trận khoảng cách đường bộ, đơn vị kilomet.

    duration_matrix_seconds:
        Ma trận thời gian đường bộ, đơn vị giây.

    Kết quả:
        - DataFrame chi tiết ETA.
        - Tổng thời gian chuyến đi theo phút, gồm thời gian di chuyển
          và thời gian phục vụ.
    """

    if not display_route:
        raise ValueError("Lộ trình đang trống.")

    location_count = len(locations)

    expected_shape = (
        location_count,
        location_count,
    )

    if distance_matrix_km.shape != expected_shape:
        raise ValueError(
            "Kích thước ma trận khoảng cách không phù hợp "
            "với số lượng địa điểm."
        )

    if duration_matrix_seconds.shape != expected_shape:
        raise ValueError(
            "Kích thước ma trận thời gian không phù hợp "
            "với số lượng địa điểm."
        )

    rows: list[dict[str, object]] = []
    elapsed_minutes = 0.0
    first_location_index = int(display_route[0])

    for order, raw_location_index in enumerate(display_route):
        location_index = int(raw_location_index)

        if (
            location_index < 0
            or location_index >= location_count
        ):
            raise IndexError(
                f"Chỉ số địa điểm {location_index} không hợp lệ."
            )

        location = locations.iloc[location_index]

        if order == 0:
            segment_distance_km = 0.0
            travel_minutes = 0.0
        else:
            previous_location_index = int(
                display_route[order - 1]
            )

            segment_distance_km = float(
                distance_matrix_km[
                    previous_location_index
                ][location_index]
            )

            segment_duration_seconds = float(
                duration_matrix_seconds[
                    previous_location_index
                ][location_index]
            )

            if np.isnan(segment_distance_km):
                raise ValueError(
                    "Không xác định được khoảng cách đường bộ "
                    "giữa hai địa điểm."
                )

            if np.isnan(segment_duration_seconds):
                raise ValueError(
                    "Không xác định được thời gian đường bộ "
                    "giữa hai địa điểm."
                )

            travel_minutes = (
                segment_duration_seconds / 60.0
            )

            elapsed_minutes += travel_minutes

        arrival_datetime = (
            departure_datetime
            + timedelta(minutes=elapsed_minutes)
        )

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

        if service_time < 0:
            raise ValueError(
                "Thời gian phục vụ không được âm."
            )

        departure_from_location = (
            arrival_datetime
            + timedelta(minutes=service_time)
        )

        rows.append(
            {
                "order": order,
                "location_id": int(location["id"]),
                "location_name": str(location["name"]),
                "segment_distance_km": round(
                    segment_distance_km,
                    3,
                ),
                "travel_time_minutes": round(
                    travel_minutes,
                    2,
                ),
                "arrival_time": arrival_datetime.strftime(
                    "%H:%M:%S"
                ),
                "service_time_minutes": service_time,
                "departure_time": (
                    departure_from_location.strftime(
                        "%H:%M:%S"
                    )
                ),
            }
        )

        elapsed_minutes += service_time

    return pd.DataFrame(rows), float(elapsed_minutes)
