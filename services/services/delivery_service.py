from __future__ import annotations

from datetime import datetime, timedelta
from typing import Sequence

import numpy as np
import pandas as pd


def calculate_delivery_cost(
    total_distance: float,
    cost_per_km: float,
) -> float:
    """Tính chi phí giao hàng theo tổng quãng đường."""

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
    Tạo bảng thời gian đến dự kiến tại từng địa điểm.

    Trả về:
    - DataFrame ETA.
    - Tổng thời gian của chuyến đi theo phút.
    """

    if not display_route:
        raise ValueError("Lộ trình đang trống.")

    if average_speed_kmh <= 0:
        raise ValueError(
            "Tốc độ trung bình phải lớn hơn 0."
        )

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
            ) * 60

            elapsed_minutes += travel_minutes

        arrival_datetime = (
            departure_datetime
            + timedelta(minutes=elapsed_minutes)
        )

        is_return_to_depot = (
            order == len(display_route) - 1
            and order > 0
            and location_index == first_location_index
        )

        service_time = (
            0.0
            if is_return_to_depot
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

    eta_table = pd.DataFrame(rows)

    return eta_table, elapsed_minutes
