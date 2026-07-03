from datetime import datetime

import pandas as pd

from services.delivery_service import (
    build_eta_table,
    calculate_delivery_cost,
)
from services.distance_service import (
    build_distance_matrix,
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
                "name": "Khách A",
                "latitude": 10.772500,
                "longitude": 106.657800,
                "service_time": 10,
            },
            {
                "id": 2,
                "name": "Khách B",
                "latitude": 10.755500,
                "longitude": 106.671200,
                "service_time": 8,
            },
        ]
    )


def test_calculate_delivery_cost() -> None:
    cost = calculate_delivery_cost(
        total_distance=10.0,
        cost_per_km=2000.0,
    )

    assert cost == 20000.0


def test_eta_table_has_correct_number_of_rows() -> None:
    locations = sample_locations()

    matrix = build_distance_matrix(
        locations
    )

    display_route = [0, 1, 2, 0]

    eta_table, total_minutes = (
        build_eta_table(
            display_route=display_route,
            locations=locations,
            distance_matrix=matrix,
            departure_datetime=datetime(
                2026,
                7,
                1,
                8,
                0,
            ),
            average_speed_kmh=30.0,
        )
    )

    assert len(eta_table) == 4
    assert total_minutes > 0


def test_return_to_depot_has_zero_service_time() -> None:
    locations = sample_locations()

    matrix = build_distance_matrix(
        locations
    )

    eta_table, _ = build_eta_table(
        display_route=[0, 1, 2, 0],
        locations=locations,
        distance_matrix=matrix,
        departure_datetime=datetime(
            2026,
            7,
            1,
            8,
            0,
        ),
        average_speed_kmh=30.0,
    )

    last_row = eta_table.iloc[-1]

    assert (
        last_row["service_time_minutes"]
        == 0
    )