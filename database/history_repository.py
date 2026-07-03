from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_DATABASE_PATH = Path("data/optimization_history.db")


HISTORY_COLUMNS = [
    "id",
    "created_at",
    "run_hash",
    "algorithm",
    "route_type",
    "start_location_id",
    "start_location_name",
    "location_count",
    "route_indices",
    "route_names",
    "distance_km",
    "matrix_distance_km",
    "execution_time_seconds",
    "delivery_cost",
    "total_duration_minutes",
    "road_duration_seconds",
    "average_speed_kmh",
    "cost_per_km",
    "vehicle_label",
    "routing_profile",
    "departure_time",
    "evaluated_routes",
    "improvement_distance",
    "improvement_percentage",
    "ga_parameters",
    "locations_snapshot",
]


def _connect(database_path: str | Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
    """Tạo bảng lịch sử nếu cơ sở dữ liệu chưa tồn tại."""

    with _connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS optimization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                run_hash TEXT NOT NULL UNIQUE,
                algorithm TEXT NOT NULL,
                route_type TEXT NOT NULL,
                start_location_id INTEGER NOT NULL,
                start_location_name TEXT NOT NULL,
                location_count INTEGER NOT NULL,
                route_indices TEXT NOT NULL,
                route_names TEXT NOT NULL,
                distance_km REAL NOT NULL,
                matrix_distance_km REAL,
                execution_time_seconds REAL NOT NULL,
                delivery_cost REAL NOT NULL,
                total_duration_minutes REAL NOT NULL,
                road_duration_seconds REAL NOT NULL,
                average_speed_kmh REAL NOT NULL,
                cost_per_km REAL NOT NULL,
                vehicle_label TEXT NOT NULL,
                routing_profile TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                evaluated_routes INTEGER,
                improvement_distance REAL,
                improvement_percentage REAL,
                ga_parameters TEXT NOT NULL,
                locations_snapshot TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_history_algorithm
            ON optimization_history(algorithm)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_history_created_at
            ON optimization_history(created_at DESC)
            """
        )
        connection.commit()


def build_run_hash(payload: dict[str, Any]) -> str:
    """Tạo mã nhận diện để ngăn lưu lặp cùng một kết quả."""

    fingerprint_fields = {
        "algorithm": payload.get("algorithm"),
        "route_type": payload.get("route_type"),
        "start_location_id": payload.get("start_location_id"),
        "route_indices": payload.get("route_indices"),
        "distance_km": round(float(payload.get("distance_km", 0.0)), 6),
        "matrix_distance_km": round(
            float(payload.get("matrix_distance_km") or 0.0), 6
        ),
        "cost_per_km": round(float(payload.get("cost_per_km", 0.0)), 2),
        "vehicle_label": payload.get("vehicle_label"),
        "routing_profile": payload.get("routing_profile"),
        "departure_time": payload.get("departure_time"),
        "ga_parameters": payload.get("ga_parameters"),
        "locations_snapshot": payload.get("locations_snapshot"),
    }

    encoded = json.dumps(
        fingerprint_fields,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def save_history(
    record: dict[str, Any],
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> tuple[bool, int]:
    """
    Lưu một lần chạy.

    Returns:
        (created, record_id): created=True nếu vừa thêm mới; False nếu bị trùng.
    """

    initialize_database(database_path)

    payload = record.copy()
    payload["run_hash"] = payload.get("run_hash") or build_run_hash(payload)

    insert_columns = [column for column in HISTORY_COLUMNS if column != "id"]
    placeholders = ", ".join("?" for _ in insert_columns)
    column_sql = ", ".join(insert_columns)
    values = [payload.get(column) for column in insert_columns]

    with _connect(database_path) as connection:
        cursor = connection.execute(
            f"""
            INSERT OR IGNORE INTO optimization_history ({column_sql})
            VALUES ({placeholders})
            """,
            values,
        )
        connection.commit()

        created = cursor.rowcount == 1

        row = connection.execute(
            """
            SELECT id
            FROM optimization_history
            WHERE run_hash = ?
            """,
            (payload["run_hash"],),
        ).fetchone()

    if row is None:
        raise RuntimeError("Không thể xác định bản ghi lịch sử vừa lưu.")

    return created, int(row["id"])


def fetch_history(
    algorithm: str | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> pd.DataFrame:
    """Đọc lịch sử, có thể lọc theo thuật toán."""

    initialize_database(database_path)

    query = "SELECT * FROM optimization_history"
    parameters: tuple[Any, ...] = ()

    if algorithm and algorithm != "Tất cả":
        query += " WHERE algorithm = ?"
        parameters = (algorithm,)

    query += " ORDER BY datetime(created_at) DESC, id DESC"

    with _connect(database_path) as connection:
        dataframe = pd.read_sql_query(query, connection, params=parameters)

    return dataframe


def list_algorithms(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[str]:
    """Lấy danh sách thuật toán đã xuất hiện trong lịch sử."""

    initialize_database(database_path)

    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT algorithm
            FROM optimization_history
            ORDER BY algorithm
            """
        ).fetchall()

    return [str(row["algorithm"]) for row in rows]


def delete_history_record(
    record_id: int,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> bool:
    """Xóa một bản ghi theo ID."""

    initialize_database(database_path)

    with _connect(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM optimization_history WHERE id = ?",
            (int(record_id),),
        )
        connection.commit()

    return cursor.rowcount == 1


def delete_all_history(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> int:
    """Xóa toàn bộ lịch sử và trả về số bản ghi đã xóa."""

    initialize_database(database_path)

    with _connect(database_path) as connection:
        cursor = connection.execute("DELETE FROM optimization_history")
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = 'optimization_history'"
        )
        connection.commit()

    return max(int(cursor.rowcount), 0)
