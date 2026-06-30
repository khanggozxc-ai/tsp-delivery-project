from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Sequence

import numpy as np
import pandas as pd


EARTH_RADIUS_KM = 6371.0088


def haversine_distance(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """
    Tính khoảng cách đường chim bay giữa hai tọa độ địa lý.

    Kết quả trả về theo kilomet.
    """

    lat1 = radians(float(latitude_1))
    lon1 = radians(float(longitude_1))
    lat2 = radians(float(latitude_2))
    lon2 = radians(float(longitude_2))

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )

    # min giúp tránh sai số số thực làm a lớn hơn 1 một lượng rất nhỏ.
    c = 2 * asin(sqrt(min(1.0, a)))

    return EARTH_RADIUS_KM * c


def build_distance_matrix(locations: pd.DataFrame) -> np.ndarray:
    """
    Tạo ma trận khoảng cách NxN từ DataFrame địa điểm.

    DataFrame bắt buộc có:
    - latitude
    - longitude
    """

    required_columns = {"latitude", "longitude"}
    missing_columns = required_columns - set(locations.columns)

    if missing_columns:
        raise ValueError(
            f"Thiếu các cột bắt buộc: {sorted(missing_columns)}"
        )

    location_count = len(locations)

    if location_count == 0:
        return np.empty((0, 0), dtype=float)

    matrix = np.zeros((location_count, location_count), dtype=float)

    for i in range(location_count):
        for j in range(i + 1, location_count):
            distance = haversine_distance(
                locations.iloc[i]["latitude"],
                locations.iloc[i]["longitude"],
                locations.iloc[j]["latitude"],
                locations.iloc[j]["longitude"],
            )

            matrix[i][j] = distance
            matrix[j][i] = distance

    return matrix


def calculate_route_distance(
    route: Sequence[int],
    distance_matrix: np.ndarray,
    return_to_start: bool = True,
) -> float:
    """
    Tính tổng quãng đường của một lộ trình.

    Ví dụ route = [0, 2, 1, 3]

    Nếu return_to_start=True:
        0 -> 2 -> 1 -> 3 -> 0

    Nếu return_to_start=False:
        0 -> 2 -> 1 -> 3
    """

    if len(route) <= 1:
        return 0.0

    matrix_size = len(distance_matrix)

    for location_index in route:
        if location_index < 0 or location_index >= matrix_size:
            raise IndexError(
                f"Chỉ số địa điểm {location_index} nằm ngoài ma trận."
            )

    total_distance = 0.0

    for current_position in range(len(route) - 1):
        current_location = route[current_position]
        next_location = route[current_position + 1]

        total_distance += distance_matrix[current_location][next_location]

    if return_to_start:
        total_distance += distance_matrix[route[-1]][route[0]]

    return float(total_distance)
