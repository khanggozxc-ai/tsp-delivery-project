from __future__ import annotations

from time import perf_counter
from typing import Any

import numpy as np

from services.distance_service import calculate_route_distance


def solve_nearest_neighbor(
    distance_matrix: np.ndarray,
    start_index: int = 0,
    return_to_start: bool = True,
) -> dict[str, Any]:
    """
    Từ điểm hiện tại, luôn chọn địa điểm chưa thăm gần nhất.
    """

    location_count = len(distance_matrix)

    if location_count < 2:
        raise ValueError("Cần ít nhất hai địa điểm.")

    if start_index < 0 or start_index >= location_count:
        raise ValueError("Điểm xuất phát không hợp lệ.")

    start_time = perf_counter()

    unvisited = set(range(location_count))
    unvisited.remove(start_index)

    route = [start_index]
    current_location = start_index

    while unvisited:
        next_location = min(
            unvisited,
            key=lambda location: distance_matrix[
                current_location
            ][location],
        )

        route.append(next_location)
        unvisited.remove(next_location)
        current_location = next_location

    total_distance = calculate_route_distance(
        route,
        distance_matrix,
        return_to_start=return_to_start,
    )

    execution_time = perf_counter() - start_time

    display_route = route.copy()

    if return_to_start:
        display_route.append(start_index)

    return {
        "algorithm": "Nearest Neighbor",
        "route": route,
        "display_route": display_route,
        "distance": total_distance,
        "execution_time": execution_time,
        "evaluated_routes": None,
        "return_to_start": return_to_start,
    }
