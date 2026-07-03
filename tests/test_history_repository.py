from __future__ import annotations

from database.history_repository import (
    delete_all_history,
    delete_history_record,
    fetch_history,
    initialize_database,
    save_history,
)


def sample_record() -> dict:
    return {
        "created_at": "2026-07-03T20:00:00",
        "algorithm": "Nearest Neighbor",
        "route_type": "Khép kín",
        "start_location_id": 0,
        "start_location_name": "Kho trung tâm",
        "location_count": 3,
        "route_indices": "[0, 1, 2, 0]",
        "route_names": "Kho → A → B → Kho",
        "distance_km": 12.5,
        "matrix_distance_km": 12.4,
        "execution_time_seconds": 0.002,
        "delivery_cost": 25000.0,
        "total_duration_minutes": 55.0,
        "road_duration_seconds": 1800.0,
        "average_speed_kmh": 25.0,
        "cost_per_km": 2000.0,
        "vehicle_label": "Xe giao hàng",
        "routing_profile": "driving-car",
        "departure_time": "2026-07-03T08:00:00",
        "evaluated_routes": 2,
        "improvement_distance": None,
        "improvement_percentage": None,
        "ga_parameters": "{}",
        "locations_snapshot": "[]",
    }


def test_save_and_prevent_duplicate(tmp_path):
    database_path = tmp_path / "history.db"
    initialize_database(database_path)

    created_1, record_id_1 = save_history(sample_record(), database_path)
    created_2, record_id_2 = save_history(sample_record(), database_path)

    assert created_1 is True
    assert created_2 is False
    assert record_id_1 == record_id_2
    assert len(fetch_history(database_path=database_path)) == 1


def test_filter_and_delete(tmp_path):
    database_path = tmp_path / "history.db"

    first = sample_record()
    _, first_id = save_history(first, database_path)

    second = sample_record()
    second["algorithm"] = "Brute Force"
    second["distance_km"] = 11.0
    save_history(second, database_path)

    filtered = fetch_history(
        algorithm="Brute Force",
        database_path=database_path,
    )
    assert len(filtered) == 1
    assert filtered.iloc[0]["algorithm"] == "Brute Force"

    assert delete_history_record(first_id, database_path) is True
    assert len(fetch_history(database_path=database_path)) == 1

    assert delete_all_history(database_path) == 1
    assert fetch_history(database_path=database_path).empty
 #
