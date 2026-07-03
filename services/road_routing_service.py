from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
import requests


ORS_BASE_URL = "https://api.openrouteservice.org"
DEFAULT_TIMEOUT_SECONDS = 60


class RoutingServiceError(RuntimeError):
    """Lỗi xảy ra khi gọi dịch vụ định tuyến đường bộ."""


def locations_to_coordinates(
    locations: pd.DataFrame,
) -> list[list[float]]:
    """
    Chuyển DataFrame địa điểm sang danh sách tọa độ ORS.

    openrouteservice yêu cầu:
        [longitude, latitude]

    Không phải:
        [latitude, longitude]
    """

    required_columns = {"latitude", "longitude"}
    missing_columns = required_columns - set(locations.columns)

    if missing_columns:
        raise ValueError(
            "Thiếu các cột tọa độ: "
            + ", ".join(sorted(missing_columns))
        )

    coordinates: list[list[float]] = []

    for _, row in locations.iterrows():
        longitude = float(row["longitude"])
        latitude = float(row["latitude"])

        if not -180 <= longitude <= 180:
            raise ValueError(
                f"Kinh độ không hợp lệ: {longitude}"
            )

        if not -90 <= latitude <= 90:
            raise ValueError(
                f"Vĩ độ không hợp lệ: {latitude}"
            )

        coordinates.append(
            [longitude, latitude]
        )

    return coordinates


def _post_json(
    url: str,
    api_key: str,
    payload: dict,
) -> dict:
    """
    Gửi POST request đến openrouteservice.
    """

    if not api_key.strip():
        raise ValueError(
            "Chưa cấu hình ORS_API_KEY."
        )

    headers = {
        "Authorization": api_key,
        "Accept": "application/json, application/geo+json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.Timeout as error:
        raise RoutingServiceError(
            "Dịch vụ định tuyến phản hồi quá lâu."
        ) from error
    except requests.RequestException as error:
        raise RoutingServiceError(
            "Không thể kết nối đến dịch vụ định tuyến."
        ) from error

    if response.status_code != 200:
        try:
            error_data = response.json()
        except ValueError:
            error_data = response.text

        raise RoutingServiceError(
            "openrouteservice trả về lỗi "
            f"{response.status_code}: {error_data}"
        )

    try:
        return response.json()
    except ValueError as error:
        raise RoutingServiceError(
            "Phản hồi từ dịch vụ không phải JSON hợp lệ."
        ) from error


def build_road_matrices(
    coordinates: Sequence[Sequence[float]],
    api_key: str,
    profile: str = "driving-car",
) -> tuple[np.ndarray, np.ndarray]:
    """
    Lấy hai ma trận:

    1. Ma trận khoảng cách đường bộ, đơn vị kilomet.
    2. Ma trận thời gian đường bộ, đơn vị giây.
    """

    if len(coordinates) < 2:
        raise ValueError(
            "Cần ít nhất hai tọa độ."
        )

    url = (
        f"{ORS_BASE_URL}/v2/matrix/{profile}"
    )

    payload = {
        "locations": [
            [float(longitude), float(latitude)]
            for longitude, latitude in coordinates
        ],
        "metrics": [
            "distance",
            "duration",
        ],
    }

    data = _post_json(
        url=url,
        api_key=api_key,
        payload=payload,
    )

    distances = data.get("distances")
    durations = data.get("durations")

    if distances is None:
        raise RoutingServiceError(
            "Phản hồi không có ma trận khoảng cách."
        )

    if durations is None:
        raise RoutingServiceError(
            "Phản hồi không có ma trận thời gian."
        )

    # API trả khoảng cách theo mét.
    distance_matrix_km = (
        np.asarray(distances, dtype=float)
        / 1000.0
    )

    # Thời gian được trả về theo giây.
    duration_matrix_seconds = np.asarray(
        durations,
        dtype=float,
    )

    expected_shape = (
        len(coordinates),
        len(coordinates),
    )

    if distance_matrix_km.shape != expected_shape:
        raise RoutingServiceError(
            "Kích thước ma trận khoảng cách không hợp lệ."
        )

    if duration_matrix_seconds.shape != expected_shape:
        raise RoutingServiceError(
            "Kích thước ma trận thời gian không hợp lệ."
        )

    if np.isnan(distance_matrix_km).any():
        raise RoutingServiceError(
            "Có cặp địa điểm không tìm được đường đi."
        )

    if np.isnan(duration_matrix_seconds).any():
        raise RoutingServiceError(
            "Có cặp địa điểm không tính được thời gian."
        )

    return (
        distance_matrix_km,
        duration_matrix_seconds,
    )


def get_route_geojson(
    ordered_coordinates: Sequence[
        Sequence[float]
    ],
    api_key: str,
    profile: str = "driving-car",
) -> dict:
    """
    Lấy GeoJSON của tuyến đường theo đúng thứ tự TSP.

    ordered_coordinates phải có dạng:
        [[longitude, latitude], ...]
    """

    if len(ordered_coordinates) < 2:
        raise ValueError(
            "Lộ trình cần ít nhất hai tọa độ."
        )

    url = (
        f"{ORS_BASE_URL}"
        f"/v2/directions/{profile}/geojson"
    )

    payload = {
        "coordinates": [
            [float(longitude), float(latitude)]
            for longitude, latitude
            in ordered_coordinates
        ],
        "instructions": False,
        "preference": "fastest",
    }

    route_geojson = _post_json(
        url=url,
        api_key=api_key,
        payload=payload,
    )

    features = route_geojson.get(
        "features",
        [],
    )

    if not features:
        raise RoutingServiceError(
            "Không tìm thấy tuyến đường giao thông."
        )

    return route_geojson


def get_route_summary(
    route_geojson: dict,
) -> tuple[float, float]:
    """
    Lấy tổng khoảng cách và thời gian từ GeoJSON.

    Trả về:
    - Khoảng cách kilomet.
    - Thời gian giây.
    """

    features = route_geojson.get(
        "features",
        [],
    )

    if not features:
        raise RoutingServiceError(
            "GeoJSON không có tuyến đường."
        )

    properties = features[0].get(
        "properties",
        {},
    )

    summary = properties.get(
        "summary",
        {},
    )

    distance_meters = float(
        summary.get("distance", 0.0)
    )

    duration_seconds = float(
        summary.get("duration", 0.0)
    )

    return (
        distance_meters / 1000.0,
        duration_seconds,
    )
    