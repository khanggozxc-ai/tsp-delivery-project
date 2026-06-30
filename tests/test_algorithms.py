import pandas as pd

from algorithms.brute_force import solve_brute_force
from algorithms.nearest_neighbor import solve_nearest_neighbor
from services.distance_service import (
    build_distance_matrix,
    calculate_route_distance,
    haversine_distance,
)


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
        ]
    )


def test_same_coordinate_distance_is_zero() -> None:
    distance = haversine_distance(
        10.762622,
        106.660172,
        10.762622,
        106.660172,
    )

    assert distance == 0.0


def test_distance_matrix_is_symmetric() -> None:
    matrix = build_distance_matrix(sample_locations())

    assert matrix.shape == (4, 4)
    assert matrix[0][1] == matrix[1][0]
    assert matrix[2][3] == matrix[3][2]


def test_closed_route_longer_or_equal_open_route() -> None:
    matrix = build_distance_matrix(sample_locations())
    route = [0, 1, 2, 3]

    open_distance = calculate_route_distance(
        route,
        matrix,
        return_to_start=False,
    )

    closed_distance = calculate_route_distance(
        route,
        matrix,
        return_to_start=True,
    )

    assert closed_distance >= open_distance


def test_brute_force_returns_valid_route() -> None:
    matrix = build_distance_matrix(sample_locations())

    result = solve_brute_force(
        matrix,
        start_index=0,
        return_to_start=True,
    )

    assert result["route"][0] == 0
    assert len(result["route"]) == 4
    assert len(set(result["route"])) == 4
    assert result["distance"] > 0


def test_nearest_neighbor_returns_valid_route() -> None:
    matrix = build_distance_matrix(sample_locations())

    result = solve_nearest_neighbor(
        matrix,
        start_index=0,
        return_to_start=True,
    )

    assert result["route"][0] == 0
    assert len(result["route"]) == 4
    assert len(set(result["route"])) == 4
    assert result["distance"] > 0


def test_brute_force_not_worse_than_nearest_neighbor() -> None:
    matrix = build_distance_matrix(sample_locations())

    brute_force_result = solve_brute_force(
        matrix,
        start_index=0,
        return_to_start=True,
    )

    nearest_neighbor_result = solve_nearest_neighbor(
        matrix,
        start_index=0,
        return_to_start=True,
    )

    assert (
        brute_force_result["distance"]
        <= nearest_neighbor_result["distance"]
    )
