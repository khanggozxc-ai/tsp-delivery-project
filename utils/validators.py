from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "id",
    "name",
    "latitude",
    "longitude",
    "service_time",
]


def normalize_locations(locations: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hóa kiểu dữ liệu và loại bỏ khoảng trắng không cần thiết.
    """

    normalized = locations.copy()

    normalized.columns = [
        str(column).strip().lower() for column in normalized.columns
    ]

    if "name" in normalized.columns:
        normalized["name"] = normalized["name"].astype(str).str.strip()

    numeric_columns = [
        "id",
        "latitude",
        "longitude",
        "service_time",
    ]

    for column in numeric_columns:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(
                normalized[column],
                errors="coerce",
            )

    return normalized


def validate_locations(locations: pd.DataFrame) -> list[str]:
    """
    Trả về danh sách lỗi.
    Danh sách rỗng nghĩa là dữ liệu hợp lệ.
    """

    errors: list[str] = []

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in locations.columns
    ]

    if missing_columns:
        errors.append(
            "Thiếu cột bắt buộc: " + ", ".join(missing_columns)
        )
        return errors

    if locations.empty:
        errors.append("Danh sách địa điểm đang trống.")
        return errors

    if locations[REQUIRED_COLUMNS].isnull().any().any():
        errors.append("Dữ liệu có ô bị trống hoặc không đúng kiểu số.")

    if locations["id"].duplicated().any():
        errors.append("Mã địa điểm bị trùng.")

    if locations["name"].str.lower().duplicated().any():
        errors.append("Tên địa điểm bị trùng.")

    duplicated_coordinates = locations.duplicated(
        subset=["latitude", "longitude"]
    )

    if duplicated_coordinates.any():
        errors.append("Có nhiều địa điểm sử dụng cùng một tọa độ.")

    invalid_latitude = ~locations["latitude"].between(-90, 90)

    if invalid_latitude.any():
        errors.append("Vĩ độ phải nằm trong khoảng từ -90 đến 90.")

    invalid_longitude = ~locations["longitude"].between(-180, 180)

    if invalid_longitude.any():
        errors.append("Kinh độ phải nằm trong khoảng từ -180 đến 180.")

    if (locations["service_time"] < 0).any():
        errors.append("Thời gian phục vụ không được âm.")

    if len(locations) < 2:
        errors.append("Cần ít nhất hai địa điểm để tạo lộ trình.")

    return errors
