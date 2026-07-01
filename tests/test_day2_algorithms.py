import pandas as pd

from algorithms.genetic_algorithm import (
    solve_genetic_algorithm,
)
from algorithms.nearest_neighbor import (
    solve_nearest_neighbor,
)
from algorithms.two_opt import (
    improve_route_two_opt,
    solve_two_opt_from_result,
)
from services.distance_service import build_distance_matrix


def sample_locations() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": 0,
                "name": "Kho",
                "latitude": 10.762622,
                "longitude": 106.660172,
                "service_time": 0,
            },
            {
                "id": 1,
                "name": "A",
                "latitude": 10.772500,
                "longitude": 106.657800,
                "service_time": 10,
            },
            {
                "id": 2,
                "name": "B",
                "latitude": 10.755500,
                "longitude": 106.671200,
                "service_time": 8,
            },
            {
                "id": 3,
                "name": "C",
                "latitude": 10.748900,
                "longitude": 106.655600,
                "service_time": 12,
            },
            {
                "id": 4,
                "name": "D",
                "latitude": 10.768300,
                "longitude": 106.680100,
                "service_time": 7,
            },
        ]
    )


def test_genetic_algorithm_returns_valid_route() -> None:
    matrix = build_distance_matrix(sample_locations())

    result = solve_genetic_algorithm(
        distance_matrix=matrix,
        start_index=0,
        return_to_start=True,
        population_size=30,
        generations=50,
        random_seed=42,
    )

    assert result["route"][0] == 0
    assert len(result["route"]) == 5
    assert len(set(result["route"])) == 5
    assert result["display_route"][-1] == 0
    assert result["distance"] > 0


def test_genetic_algorithm_history_is_valid() -> None:
    matrix = build_distance_matrix(sample_locations())

    result = solve_genetic_algorithm(
        distance_matrix=matrix,
        start_index=0,
        population_size=20,
        generations=25,
        random_seed=42,
    )

    assert len(result["history"]) == 25

    # Best-so-far không được tăng qua các thế hệ.
    for previous, current in zip(
        result["history"],
        result["history"][1:],
    ):
        assert current <= previous


def test_genetic_algorithm_reproducible_with_seed() -> None:
    matrix = build_distance_matrix(sample_locations())

    result_1 = solve_genetic_algorithm(
        distance_matrix=matrix,
        start_index=0,
        population_size=30,
        generations=50,
        random_seed=123,
    )

    result_2 = solve_genetic_algorithm(
        distance_matrix=matrix,
        start_index=0,
        population_size=30,
        generations=50,
        random_seed=123,
    )

    assert result_1["route"] == result_2["route"]
    assert result_1["distance"] == result_2["distance"]


def test_two_opt_does_not_make_route_worse() -> None:
    matrix = build_distance_matrix(sample_locations())

    initial_route = [0, 1, 3, 2, 4]

    result = improve_route_two_opt(
        route=initial_route,
        distance_matrix=matrix,
        return_to_start=True,
    )

    assert result["distance"] <= result["original_distance"]
    assert len(result["route"]) == 5
    assert len(set(result["route"])) == 5


def test_nearest_neighbor_plus_two_opt() -> None:
    matrix = build_distance_matrix(sample_locations())

    nearest_result = solve_nearest_neighbor(
        distance_matrix=matrix,
        start_index=0,
        return_to_start=True,
    )

    improved_result = solve_two_opt_from_result(
        base_result=nearest_result,
        distance_matrix=matrix,
    )

    assert (
        improved_result["distance"]
        <= nearest_result["distance"]
    )

    assert improved_result["algorithm"] == (
        "Nearest Neighbor + 2-opt"
    )