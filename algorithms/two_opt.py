from __future__ import annotations

from time import perf_counter
from typing import Any

import numpy as np

from services.distance_service import calculate_route_distance


def improve_route_two_opt(
    route: list[int],
    distance_matrix: np.ndarray,
    return_to_start: bool = True,
    max_passes: int | None = None,
) -> dict[str, Any]:
    """
    Cải thiện một lộ trình bằng 2-opt.

    Điểm đầu tiên được giữ cố định.
    Thuật toán đảo các đoạn của lộ trình để tìm khoảng cách nhỏ hơn.
    """

    if len(route) < 2:
        raise ValueError("Lộ trình phải có ít nhất hai địa điểm.")

    if len(set(route)) != len(route):
        raise ValueError(
            "Route đầu vào không được chứa địa điểm trùng."
        )

    best_route = route.copy()

    best_distance = calculate_route_distance(
        route=best_route,
        distance_matrix=distance_matrix,
        return_to_start=return_to_start,
    )

    original_distance = best_distance

    improvement_found = True
    pass_count = 0
    evaluated_routes = 0

    start_time = perf_counter()

    while improvement_found:
        improvement_found = False
        pass_count += 1

        if max_passes is not None and pass_count > max_passes:
            break

        # i bắt đầu từ 1 để giữ cố định điểm xuất phát.
        for i in range(1, len(best_route) - 1):
            for j in range(i + 1, len(best_route)):
                candidate_route = best_route.copy()

                candidate_route[i : j + 1] = reversed(
                    candidate_route[i : j + 1]
                )

                candidate_distance = calculate_route_distance(
                    route=candidate_route,
                    distance_matrix=distance_matrix,
                    return_to_start=return_to_start,
                )

                evaluated_routes += 1

                if candidate_distance < best_distance - 1e-12:
                    best_route = candidate_route
                    best_distance = candidate_distance
                    improvement_found = True

                    # First improvement:
                    # tìm thấy lời giải tốt hơn thì bắt đầu lại.
                    break

            if improvement_found:
                break

    execution_time = perf_counter() - start_time

    improvement_distance = original_distance - best_distance

    if original_distance > 0:
        improvement_percentage = (
            improvement_distance / original_distance
        ) * 100
    else:
        improvement_percentage = 0.0

    display_route = best_route.copy()

    if return_to_start:
        display_route.append(best_route[0])

    return {
        "route": best_route,
        "display_route": display_route,
        "distance": float(best_distance),
        "original_distance": float(original_distance),
        "improvement_distance": float(improvement_distance),
        "improvement_percentage": float(
            improvement_percentage
        ),
        "execution_time": execution_time,
        "evaluated_routes": evaluated_routes,
        "pass_count": pass_count,
        "return_to_start": return_to_start,
    }


def solve_two_opt_from_result(
    base_result: dict[str, Any],
    distance_matrix: np.ndarray,
    algorithm_name: str | None = None,
) -> dict[str, Any]:
    """
    Nhận kết quả của Nearest Neighbor hoặc GA,
    sau đó cải thiện bằng 2-opt.
    """

    improved_result = improve_route_two_opt(
        route=base_result["route"],
        distance_matrix=distance_matrix,
        return_to_start=base_result["return_to_start"],
    )

    base_algorithm = str(base_result["algorithm"])

    improved_result["algorithm"] = (
        algorithm_name
        if algorithm_name is not None
        else f"{base_algorithm} + 2-opt"
    )

    improved_result["base_algorithm"] = base_algorithm

    improved_result["base_execution_time"] = float(
        base_result["execution_time"]
    )

    improved_result["execution_time"] += float(
        base_result["execution_time"]
    )

    improved_result["history"] = base_result.get(
        "history",
        [],
    )

    improved_result["parameters"] = base_result.get(
        "parameters",
        {},
    )

    return improved_result