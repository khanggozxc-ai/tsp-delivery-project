from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_DATABASE_PATH = Path("database") / "tsp_history.db"


def _prepare_database_path(
    database_path: str | Path,
) -> Path:
    """
    Chuẩn hóa đường dẫn và tạo thư mục chứa database nếu chưa tồn tại.
    """

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    return path


def _connect(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> sqlite3.Connection:
    """
    Tạo một kết nối SQLite mới.

    Mỗi thao tác mở và đóng kết nối riêng để phù hợp với Streamlit.
    """

    path = _prepare_database_path(database_path)

    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> None:
    """
    Tạo bảng lịch sử nếu bảng chưa tồn tại.
    """

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS optimization_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        created_at TEXT NOT NULL,
        departure_time TEXT,

        algorithm TEXT NOT NULL,
        location_count INTEGER NOT NULL,

        start_location TEXT NOT NULL,
        route_type TEXT NOT NULL,

        route_text TEXT NOT NULL,
        route_indices_json TEXT NOT NULL,

        total_distance REAL NOT NULL,
        execution_time REAL NOT NULL,
        total_duration_minutes REAL NOT NULL,
        delivery_cost REAL NOT NULL,

        average_speed_kmh REAL NOT NULL,
        cost_per_km REAL NOT NULL,

        improvement_distance REAL,
        improvement_percentage REAL,

        evaluated_routes INTEGER,

        parameters_json TEXT,
        convergence_history_json TEXT
    );
    """

    with _connect(database_path) as connection:
        connection.execute(create_table_sql)
        connection.commit()


def _serialize_datetime(value: Any) -> str | None:
    """
    Chuyển datetime thành chuỗi ISO.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat(timespec="minutes")

    return str(value)


def save_optimization_result(
    result: dict[str, Any],
    locations: pd.DataFrame,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> int:
    """
    Lưu một kết quả tối ưu vào SQLite.

    Trả về ID của bản ghi vừa được tạo.
    """

    initialize_database(database_path)

    display_route = list(result["display_route"])

    if not display_route:
        raise ValueError("Không thể lưu một lộ trình trống.")

    route_names: list[str] = []

    for location_index in display_route:
        if (
            location_index < 0
            or location_index >= len(locations)
        ):
            raise IndexError(
                f"Chỉ số địa điểm {location_index} không hợp lệ."
            )

        route_names.append(
            str(locations.iloc[location_index]["name"])
        )

    route_text = " → ".join(route_names)

    start_location_index = display_route[0]

    start_location_name = str(
        locations.iloc[start_location_index]["name"]
    )

    return_to_start = bool(
        result.get("return_to_start", False)
    )

    route_type = (
        "Khép kín"
        if return_to_start
        else "Mở"
    )

    parameters_json = json.dumps(
        result.get("parameters", {}),
        ensure_ascii=False,
    )

    history_values = [
        float(value)
        for value in result.get("history", [])
    ]

    convergence_history_json = json.dumps(
        history_values,
        ensure_ascii=False,
    )

    route_indices_json = json.dumps(
        [int(index) for index in display_route],
        ensure_ascii=False,
    )

    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    departure_time = _serialize_datetime(
        result.get("departure_datetime")
    )

    insert_sql = """
    INSERT INTO optimization_history (
        created_at,
        departure_time,
        algorithm,
        location_count,
        start_location,
        route_type,
        route_text,
        route_indices_json,
        total_distance,
        execution_time,
        total_duration_minutes,
        delivery_cost,
        average_speed_kmh,
        cost_per_km,
        improvement_distance,
        improvement_percentage,
        evaluated_routes,
        parameters_json,
        convergence_history_json
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    values = (
        created_at,
        departure_time,
        str(result["algorithm"]),
        int(len(locations)),
        start_location_name,
        route_type,
        route_text,
        route_indices_json,
        float(result["distance"]),
        float(result["execution_time"]),
        float(result["total_duration_minutes"]),
        float(result["delivery_cost"]),
        float(result["average_speed_kmh"]),
        float(result["cost_per_km"]),
        (
            float(result["improvement_distance"])
            if result.get("improvement_distance") is not None
            else None
        ),
        (
            float(result["improvement_percentage"])
            if result.get("improvement_percentage") is not None
            else None
        ),
        (
            int(result["evaluated_routes"])
            if result.get("evaluated_routes") is not None
            else None
        ),
        parameters_json,
        convergence_history_json,
    )

    with _connect(database_path) as connection:
        cursor = connection.execute(
            insert_sql,
            values,
        )

        connection.commit()

        record_id = cursor.lastrowid

    if record_id is None:
        raise RuntimeError(
            "Không lấy được ID của bản ghi vừa lưu."
        )

    return int(record_id)


def get_optimization_history(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Đọc lịch sử tối ưu, bản ghi mới nhất hiển thị trước.
    """

    initialize_database(database_path)

    query = """
    SELECT
        id,
        created_at,
        departure_time,
        algorithm,
        location_count,
        start_location,
        route_type,
        route_text,
        total_distance,
        execution_time,
        total_duration_minutes,
        delivery_cost,
        average_speed_kmh,
        cost_per_km,
        improvement_distance,
        improvement_percentage,
        evaluated_routes,
        parameters_json,
        convergence_history_json
    FROM optimization_history
    ORDER BY id DESC
    """

    parameters: tuple[Any, ...] = ()

    if limit is not None:
        if limit < 1:
            raise ValueError("Limit phải lớn hơn 0.")

        query += " LIMIT ?"
        parameters = (int(limit),)

    with _connect(database_path) as connection:
        history = pd.read_sql_query(
            query,
            connection,
            params=parameters,
        )

    return history


def delete_history_record(
    record_id: int,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> bool:
    """
    Xóa một bản ghi theo ID.

    Trả về True nếu có bản ghi được xóa.
    """

    initialize_database(database_path)

    with _connect(database_path) as connection:
        cursor = connection.execute(
            """
            DELETE FROM optimization_history
            WHERE id = ?;
            """,
            (int(record_id),),
        )

        connection.commit()

        return cursor.rowcount > 0


def clear_optimization_history(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> int:
    """
    Xóa toàn bộ lịch sử.

    Trả về số bản ghi đã xóa.
    """

    initialize_database(database_path)

    with _connect(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM optimization_history;"
        )

        deleted_count = cursor.rowcount
        connection.commit()

    return int(deleted_count)


def count_history_records(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> int:
    """
    Đếm tổng số bản ghi.
    """

    initialize_database(database_path)

    with _connect(database_path) as connection:
        cursor = connection.execute(
            """
            SELECT COUNT(*)
            FROM optimization_history;
            """
        )

        result = cursor.fetchone()

    if result is None:
        return 0

    return int(result[0])