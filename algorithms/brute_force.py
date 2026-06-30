from __future__ import annotations

from itertools import permutations
from time import perf_counter
from typing import Any

import numpy as np

from services.distance_service import calculate_route_distance


def solve_brute_force(
    distance_matrix: np.ndarray,
    start_index: int = 0,
    return_to_start: bool = True,
    max_locations: int = 10,
) -> dict[str, Any]:
    """
    Tìm lộ trình tốt nhất bằng cách thử mọi hoán vị.

    Chỉ nên dùng với số địa điểm nhỏ.
    """

    location_count = len(distance_matrix)

    if location_count < 2:
        raise ValueError("Cần ít nhất hai địa điểm.")

    if start_index < 0 or start_index >= location_count:
        raise ValueError("Điểm xuất phát không hợp lệ.")

    if location_count > max_locations:
        raise ValueError(
            f"Brute Force chỉ cho phép tối đa {max_locations} địa điểm."
        )

    remaining_locations = [
        index
        for index in range(location_count)
        if index != start_index
    ]

    best_route: list[int] | None = None
    best_distance = float("inf")
    evaluated_routes = 0

    start_time = perf_counter()

    for candidate_order in permutations(remaining_locations):
        candidate_route = [start_index, *candidate_order]

        candidate_distance = calculate_route_distance(
            candidate_route,
            distance_matrix,
            return_to_start=return_to_start,
        )

        evaluated_routes += 1

        if candidate_distance < best_distance:
            best_distance = candidate_distance
            best_route = list(candidate_route)

    execution_time = perf_counter() - start_time

    if best_route is None:
        raise RuntimeError("Không tìm được lộ trình.")

    display_route = best_route.copy()

    if return_to_start:
        display_route.append(start_index)

    return {
        "algorithm": "Brute Force",
        "route": best_route,
        "display_route": display_route,
        "distance": best_distance,
        "execution_time": execution_time,
        "evaluated_routes": evaluated_routes,
        "return_to_start": return_to_start,
    }
