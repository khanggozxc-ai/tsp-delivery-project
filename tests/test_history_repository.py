from datetime import datetime

import pandas as pd

from database.history_repository import (
    clear_optimization_history,
    count_history_records,
    delete_history_record,
    get_optimization_history,
    initialize_database,
    save_optimization_result,
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


def sample_result() -> dict:
    return {
        "algorithm": "Genetic Algorithm + 2-opt",
        "route": [0, 2, 1],
        "display_route": [0, 2, 1, 0],
        "distance": 5.25,
        "execution_time": 0.48,
        "total_duration_minutes": 42.5,
        "delivery_cost": 10500.0,
        "average_speed_kmh": 30.0,
        "cost_per_km": 2000.0,
        "return_to_start": True,
        "improvement_distance": 0.75,
        "improvement_percentage": 12.5,
        "evaluated_routes": 30000,
        "departure_datetime": datetime(
            2026,
            7,
            2,
            8,
            0,
        ),
        "parameters": {
            "population_size": 100,
            "generations": 300,
            "mutation_rate": 0.05,
        },
        "history": [7.2, 6.8, 5.9, 5.25],
    }


def test_initialize_database(tmp_path) -> None:
    database_path = tmp_path / "history.db"

    initialize_database(database_path)

    assert database_path.exists()


def test_save_and_read_history(tmp_path) -> None:
    database_path = tmp_path / "history.db"

    record_id = save_optimization_result(
        result=sample_result(),
        locations=sample_locations(),
        database_path=database_path,
    )

    history = get_optimization_history(
        database_path=database_path
    )

    assert record_id == 1
    assert len(history) == 1
    assert history.iloc[0]["algorithm"] == (
        "Genetic Algorithm + 2-opt"
    )
    assert history.iloc[0]["total_distance"] == 5.25
    assert history.iloc[0]["route_type"] == "Khép kín"


def test_count_history(tmp_path) -> None:
    database_path = tmp_path / "history.db"

    assert count_history_records(
        database_path
    ) == 0

    save_optimization_result(
        result=sample_result(),
        locations=sample_locations(),
        database_path=database_path,
    )

    assert count_history_records(
        database_path
    ) == 1


def test_delete_one_record(tmp_path) -> None:
    database_path = tmp_path / "history.db"

    record_id = save_optimization_result(
        result=sample_result(),
        locations=sample_locations(),
        database_path=database_path,
    )

    deleted = delete_history_record(
        record_id=record_id,
        database_path=database_path,
    )

    assert deleted is True
    assert count_history_records(
        database_path
    ) == 0


def test_clear_history(tmp_path) -> None:
    database_path = tmp_path / "history.db"

    save_optimization_result(
        result=sample_result(),
        locations=sample_locations(),
        database_path=database_path,
    )

    save_optimization_result(
        result=sample_result(),
        locations=sample_locations(),
        database_path=database_path,
    )

    deleted_count = clear_optimization_history(
        database_path=database_path
    )

    assert deleted_count == 2
    assert count_history_records(
        database_path
    ) == 0