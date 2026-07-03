from __future__ import annotations

import hashlib
import json
from datetime import datetime
from io import BytesIO

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static

from algorithms.brute_force import solve_brute_force
from algorithms.genetic_algorithm import solve_genetic_algorithm
from algorithms.nearest_neighbor import solve_nearest_neighbor
from algorithms.two_opt import solve_two_opt_from_result
from services.delivery_service import (
    build_road_eta_table,
    calculate_delivery_cost,
)
from database.history_repository import (
    initialize_database,
    save_history,
)
from services.road_routing_service import (
    build_road_matrices,
    get_route_geojson,
    get_route_summary,
    locations_to_coordinates,
)
from views.history_dashboard import render_history_dashboard
from utils.validators import (
    normalize_locations,
    validate_locations,
)


st.set_page_config(
    page_title="TSP Delivery Optimizer",
    page_icon="🚚",
    layout="wide",
)


DEFAULT_DATA_PATH = "data/locations_5.csv"

ALGORITHM_OPTIONS = [
    "Nearest Neighbor",
    "Nearest Neighbor + 2-opt",
    "Brute Force",
    "Genetic Algorithm",
    "Genetic Algorithm + 2-opt",
]

ROUTING_PROFILE_MAPPING = {
    "Xe giao hàng": "driving-car",
    "Xe đạp": "cycling-regular",
    "Đi bộ": "foot-walking",
}



# =========================================================
# GIAO DIỆN VÀ PHONG CÁCH HIỂN THỊ
# =========================================================

def apply_custom_ui() -> None:
    """Áp dụng giao diện logistics-tech và hiệu ứng tương tác."""

    st.markdown(
        """
        <style>
        :root {
            --primary: #075985;
            --primary-2: #0284c7;
            --accent: #06b6d4;
            --success: #10b981;
            --surface: rgba(255, 255, 255, 0.86);
            --surface-strong: rgba(255, 255, 255, 0.96);
            --border: rgba(7, 89, 133, 0.12);
            --text-main: #0f172a;
            --text-muted: #475569;
            --shadow: 0 12px 30px rgba(15, 89, 125, 0.10);
            --shadow-hover: 0 18px 38px rgba(15, 89, 125, 0.18);
        }

        html {
            scroll-behavior: smooth;
        }

        .stApp {
            color: var(--text-main);
            background:
                radial-gradient(
                    circle at 8% 2%,
                    rgba(14, 165, 233, 0.22),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 92% 12%,
                    rgba(16, 185, 129, 0.16),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 52% 95%,
                    rgba(6, 182, 212, 0.11),
                    transparent 34%
                ),
                linear-gradient(
                    135deg,
                    #f8fcff 0%,
                    #eef8fd 45%,
                    #eefbf6 100%
                );
            background-attachment: fixed;
        }

        [data-testid="stAppViewContainer"] > .main {
            background:
                linear-gradient(
                    rgba(255, 255, 255, 0.05),
                    rgba(255, 255, 255, 0.05)
                );
        }

        [data-testid="stHeader"] {
            background: rgba(248, 252, 255, 0.72);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid rgba(7, 89, 133, 0.06);
        }

        .block-container {
            max-width: 1240px;
            padding-top: 1.45rem;
            padding-bottom: 3rem;
        }

        /* Hero */
        .hero-banner {
            position: relative;
            overflow: hidden;
            padding: 30px 32px;
            margin-bottom: 22px;
            border-radius: 26px;
            color: white;
            background:
                linear-gradient(
                    120deg,
                    rgba(3, 105, 161, 0.98) 0%,
                    rgba(2, 132, 199, 0.96) 52%,
                    rgba(6, 182, 212, 0.92) 100%
                );
            box-shadow: 0 20px 50px rgba(2, 84, 125, 0.24);
            isolation: isolate;
            animation: hero-enter 0.55s ease-out both;
        }

        .hero-banner::before,
        .hero-banner::after {
            content: "";
            position: absolute;
            border-radius: 999px;
            z-index: -1;
        }

        .hero-banner::before {
            width: 230px;
            height: 230px;
            top: -105px;
            right: 5%;
            background: rgba(255, 255, 255, 0.10);
        }

        .hero-banner::after {
            width: 165px;
            height: 165px;
            right: -45px;
            bottom: -80px;
            border: 26px solid rgba(255, 255, 255, 0.09);
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 13px;
            margin-bottom: 12px;
            border: 1px solid rgba(255, 255, 255, 0.28);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.14);
            backdrop-filter: blur(10px);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .hero-title {
            max-width: 940px;
            margin: 0;
            font-size: clamp(1.8rem, 4vw, 2.65rem);
            font-weight: 850;
            line-height: 1.15;
            letter-spacing: -0.025em;
        }

        .hero-subtitle {
            max-width: 900px;
            margin-top: 11px;
            font-size: 1rem;
            line-height: 1.7;
            color: rgba(255, 255, 255, 0.92);
        }

        .hero-features {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 18px;
        }

        .hero-feature {
            padding: 8px 12px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.13);
            border: 1px solid rgba(255, 255, 255, 0.17);
            font-size: 0.86rem;
            font-weight: 650;
            transition:
                transform 0.22s ease,
                background 0.22s ease;
        }

        .hero-feature:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.21);
        }

        /* Section heading */
        .section-heading {
            display: flex;
            gap: 14px;
            align-items: flex-start;
            padding: 17px 18px;
            margin: 6px 0 15px;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: var(--surface);
            box-shadow: 0 9px 25px rgba(15, 89, 125, 0.07);
            backdrop-filter: blur(14px);
            transition:
                transform 0.25s ease,
                box-shadow 0.25s ease,
                border-color 0.25s ease;
        }

        .section-heading:hover {
            transform: translateY(-3px);
            border-color: rgba(2, 132, 199, 0.25);
            box-shadow: var(--shadow-hover);
        }

        .section-icon {
            display: grid;
            place-items: center;
            flex: 0 0 43px;
            width: 43px;
            height: 43px;
            border-radius: 14px;
            background: linear-gradient(135deg, #e0f2fe, #cffafe);
            font-size: 1.3rem;
            box-shadow: inset 0 0 0 1px rgba(2, 132, 199, 0.08);
        }

        .section-title {
            margin: 0;
            color: var(--primary);
            font-size: 1.1rem;
            font-weight: 800;
            line-height: 1.3;
        }

        .section-description {
            margin-top: 4px;
            color: var(--text-muted);
            font-size: 0.88rem;
            line-height: 1.55;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background:
                radial-gradient(
                    circle at 30% 0%,
                    rgba(14, 165, 233, 0.19),
                    transparent 28%
                ),
                linear-gradient(180deg, #f5fbff 0%, #edf8f4 100%);
            border-right: 1px solid rgba(7, 89, 133, 0.08);
        }

        [data-testid="stSidebarContent"] {
            padding-top: 1.05rem;
        }

        .sidebar-brand {
            padding: 18px;
            margin-bottom: 15px;
            border-radius: 20px;
            color: white;
            background: linear-gradient(145deg, #075985, #0891b2);
            box-shadow: 0 14px 30px rgba(7, 89, 133, 0.20);
        }

        .sidebar-brand-title {
            font-size: 1.15rem;
            font-weight: 850;
        }

        .sidebar-brand-subtitle {
            margin-top: 5px;
            color: rgba(255, 255, 255, 0.82);
            font-size: 0.8rem;
            line-height: 1.45;
        }

        .roadmap-card {
            padding: 13px 14px;
            margin: 9px 0;
            border: 1px solid var(--border);
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.74);
            transition:
                transform 0.22s ease,
                box-shadow 0.22s ease,
                background 0.22s ease;
        }

        .roadmap-card:hover {
            transform: translateX(4px);
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 10px 24px rgba(7, 89, 133, 0.10);
        }

        .roadmap-title {
            color: var(--primary);
            font-size: 0.9rem;
            font-weight: 800;
        }

        .roadmap-content {
            margin-top: 4px;
            color: var(--text-muted);
            font-size: 0.79rem;
            line-height: 1.55;
        }

        /* Tabs */
        div[data-baseweb="tab-list"] {
            gap: 9px;
            padding: 6px;
            border: 1px solid rgba(7, 89, 133, 0.09);
            border-radius: 17px;
            background: rgba(255, 255, 255, 0.58);
            box-shadow: 0 8px 22px rgba(7, 89, 133, 0.06);
            backdrop-filter: blur(14px);
        }

        button[data-baseweb="tab"] {
            min-height: 46px;
            padding: 0 18px;
            border-radius: 12px;
            color: #334155;
            font-weight: 720;
            transition:
                transform 0.22s ease,
                background 0.22s ease,
                color 0.22s ease,
                box-shadow 0.22s ease;
        }

        button[data-baseweb="tab"]:hover {
            transform: translateY(-2px);
            color: var(--primary);
            background: #e8f7fd;
            box-shadow: 0 8px 17px rgba(7, 89, 133, 0.10);
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: white !important;
            background: linear-gradient(
                135deg,
                var(--primary),
                var(--primary-2)
            ) !important;
            box-shadow: 0 9px 20px rgba(2, 132, 199, 0.23);
        }

        div[data-baseweb="tab-highlight"] {
            display: none;
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {
            min-height: 43px;
            border: 1px solid rgba(2, 132, 199, 0.14);
            border-radius: 13px;
            color: #075985;
            background: linear-gradient(135deg, #f8fdff, #e7f7fc);
            font-weight: 750;
            box-shadow: 0 7px 17px rgba(7, 89, 133, 0.08);
            transition:
                transform 0.22s ease,
                box-shadow 0.22s ease,
                filter 0.22s ease,
                border-color 0.22s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px);
            border-color: rgba(2, 132, 199, 0.33);
            box-shadow: 0 13px 26px rgba(7, 89, 133, 0.17);
            filter: brightness(1.015);
        }

        .stButton > button:active,
        .stDownloadButton > button:active,
        [data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(0) scale(0.985);
        }

        button[kind="primary"] {
            color: white !important;
            border: 0 !important;
            background: linear-gradient(
                135deg,
                #075985 0%,
                #0284c7 58%,
                #06b6d4 100%
            ) !important;
            box-shadow: 0 12px 25px rgba(2, 132, 199, 0.24) !important;
        }

        button[kind="primary"]:hover {
            box-shadow: 0 17px 32px rgba(2, 132, 199, 0.31) !important;
        }

        /* Inputs */
        div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stTextArea"] textarea {
            border-color: rgba(7, 89, 133, 0.15) !important;
            border-radius: 12px !important;
            background: rgba(255, 255, 255, 0.90) !important;
            transition:
                border-color 0.22s ease,
                box-shadow 0.22s ease,
                background 0.22s ease;
        }

        div[data-baseweb="select"] > div:hover,
        [data-testid="stTextInput"] input:hover,
        [data-testid="stNumberInput"] input:hover,
        [data-testid="stTimeInput"] input:hover,
        [data-testid="stTextArea"] textarea:hover {
            border-color: rgba(2, 132, 199, 0.48) !important;
            background: white !important;
            box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.09);
        }

        div[data-baseweb="select"] > div:focus-within,
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTimeInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: #0ea5e9 !important;
            box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.13) !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: var(--surface);
            box-shadow: 0 8px 22px rgba(7, 89, 133, 0.06);
            transition:
                transform 0.23s ease,
                box-shadow 0.23s ease;
        }

        [data-testid="stFileUploader"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }

        [data-testid="stFileUploaderDropzone"] {
            border: 1.5px dashed rgba(2, 132, 199, 0.28);
            border-radius: 14px;
            background: linear-gradient(135deg, #f8fdff, #f0fbfb);
        }

        /* Metrics */
        [data-testid="stMetric"] {
            height: 100%;
            padding: 15px 15px 14px;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: var(--surface);
            box-shadow: var(--shadow);
            backdrop-filter: blur(14px);
            transition:
                transform 0.24s ease,
                box-shadow 0.24s ease,
                border-color 0.24s ease,
                background 0.24s ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            border-color: rgba(2, 132, 199, 0.24);
            background: var(--surface-strong);
            box-shadow: var(--shadow-hover);
        }

        [data-testid="stMetricLabel"] {
            color: #475569;
            font-weight: 650;
        }

        [data-testid="stMetricValue"] {
            color: #075985;
            font-weight: 850;
        }

        /* Data, forms and expanders */
        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"],
        [data-testid="stForm"],
        [data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 9px 24px rgba(7, 89, 133, 0.07);
            overflow: hidden;
            transition:
                transform 0.22s ease,
                box-shadow 0.22s ease,
                border-color 0.22s ease;
        }

        [data-testid="stDataFrame"]:hover,
        [data-testid="stDataEditor"]:hover,
        [data-testid="stForm"]:hover,
        [data-testid="stExpander"]:hover {
            border-color: rgba(2, 132, 199, 0.22);
            box-shadow: 0 14px 29px rgba(7, 89, 133, 0.12);
        }

        [data-testid="stForm"] {
            padding: 16px;
        }

        /* Alerts */
        [data-testid="stAlert"] {
            border-radius: 15px;
            border: 1px solid rgba(7, 89, 133, 0.10);
            box-shadow: 0 8px 19px rgba(7, 89, 133, 0.06);
        }

        /* Charts and maps */
        [data-testid="stVegaLiteChart"],
        [data-testid="stArrowVegaLiteChart"],
        iframe {
            border-radius: 18px !important;
            box-shadow: 0 13px 30px rgba(7, 89, 133, 0.12);
        }

        iframe {
            border: 1px solid rgba(7, 89, 133, 0.10) !important;
        }

        /* Titles and dividers */
        h1, h2, h3, h4 {
            color: #0f4c6e;
        }

        h4 {
            margin-top: 1.3rem !important;
            padding-left: 10px;
            border-left: 4px solid #06b6d4;
        }

        hr {
            margin: 1.35rem 0 !important;
            border-color: rgba(7, 89, 133, 0.10) !important;
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: #edf7fb;
        }

        ::-webkit-scrollbar-thumb {
            border: 2px solid #edf7fb;
            border-radius: 999px;
            background: linear-gradient(#38bdf8, #0e7490);
        }

        @keyframes hero-enter {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero-banner {
                padding: 24px 20px;
                border-radius: 21px;
            }

            .hero-features {
                gap: 7px;
            }

            button[data-baseweb="tab"] {
                padding: 0 10px;
                font-size: 0.82rem;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                scroll-behavior: auto !important;
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero_header() -> None:
    """Hiển thị phần giới thiệu chính của bài toán."""

    st.markdown(
        """
        <section class="hero-banner">
            <div class="hero-badge">
                AI PROJECT · LOGISTICS OPTIMIZATION
            </div>
            <h1 class="hero-title">
                Bài toán tối ưu lộ trình giao hàng bằng TSP
            </h1>
            <div class="hero-subtitle">
                Ứng dụng minh họa các thuật toán giải Traveling Salesman
                Problem để đề xuất thứ tự giao hàng, giảm tổng quãng đường
                và hỗ trợ ước tính chi phí, thời gian di chuyển trên mạng
                lưới đường giao thông thực tế.
            </div>
            <div class="hero-features">
                <div class="hero-feature">🧠 5 phương pháp tối ưu</div>
                <div class="hero-feature">🗺️ Định tuyến đường bộ</div>
                <div class="hero-feature">⏱️ ETA theo từng chặng</div>
                <div class="hero-feature">📊 Lịch sử và thống kê</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(
    icon: str,
    title: str,
    description: str,
) -> None:
    """Hiển thị tiêu đề khu vực dưới dạng thẻ thông tin."""

    st.markdown(
        f"""
        <div class="section-heading">
            <div class="section-icon">{icon}</div>
            <div>
                <div class="section-title">{title}</div>
                <div class="section-description">{description}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# OPENROUTESERVICE
# =========================================================

def get_ors_api_key() -> str:
    """Đọc API key OpenRouteService từ .streamlit/secrets.toml."""

    try:
        return str(st.secrets["ORS_API_KEY"]).strip()
    except Exception:
        return ""


@st.cache_data(ttl=3600, show_spinner=False)
def cached_build_road_matrices(
    coordinates: tuple[tuple[float, float], ...],
    api_key: str,
    profile: str,
):
    """Lấy và cache ma trận khoảng cách, thời gian đường bộ trong 1 giờ."""

    return build_road_matrices(
        coordinates=coordinates,
        api_key=api_key,
        profile=profile,
    )


@st.cache_data(ttl=3600, show_spinner=False)
def cached_get_route_geojson(
    ordered_coordinates: tuple[tuple[float, float], ...],
    api_key: str,
    profile: str,
):
    """Lấy và cache GeoJSON tuyến đường theo đúng thứ tự TSP."""

    return get_route_geojson(
        ordered_coordinates=ordered_coordinates,
        api_key=api_key,
        profile=profile,
    )


# =========================================================
# HÀM HỖ TRỢ CHUNG
# =========================================================

def format_route(
    display_route: list[int],
    locations: pd.DataFrame,
) -> str:
    """Chuyển danh sách chỉ số địa điểm thành chuỗi tên."""

    if not display_route or locations.empty:
        return "Chưa có lộ trình"

    route_names = [
        str(locations.iloc[index]["name"])
        for index in display_route
    ]

    return " → ".join(route_names)


def format_duration(total_minutes: float) -> str:
    """Định dạng thời gian từ số phút sang giờ và phút."""

    total_minutes = max(0.0, float(total_minutes))

    hours = int(total_minutes // 60)
    minutes = int(round(total_minutes % 60))

    if minutes == 60:
        hours += 1
        minutes = 0

    if hours == 0:
        return f"{minutes} phút"

    return f"{hours} giờ {minutes} phút"


def load_default_data() -> pd.DataFrame:
    """Đọc bộ dữ liệu mẫu mặc định."""

    return pd.read_csv(DEFAULT_DATA_PATH)


def initialize_session_state() -> None:
    """Khởi tạo dữ liệu dùng xuyên suốt phiên Streamlit."""

    if "locations" not in st.session_state:
        st.session_state.locations = load_default_data()

    if "result" not in st.session_state:
        st.session_state.result = None

    if "uploaded_csv_hash" not in st.session_state:
        st.session_state.uploaded_csv_hash = None

    if "uploader_version" not in st.session_state:
        st.session_state.uploader_version = 0

    if "last_saved_history_id" not in st.session_state:
        st.session_state.last_saved_history_id = None


# =========================================================
# THANH BÊN VÀ QUẢN LÝ DỮ LIỆU
# =========================================================

def render_sidebar() -> None:
    """Hiển thị thanh điều hướng bên trái."""

    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">🚚 TSP Delivery Lab</div>
            <div class="sidebar-brand-subtitle">
                Không gian thử nghiệm thuật toán tối ưu lộ trình giao hàng
                chặng cuối.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """
        <div class="roadmap-card">
            <div class="roadmap-title">Ngày 1 · Nền tảng</div>
            <div class="roadmap-content">
                Quản lý địa điểm · Brute Force · Nearest Neighbor
            </div>
        </div>
        <div class="roadmap-card">
            <div class="roadmap-title">Ngày 2 · Tối ưu nâng cao</div>
            <div class="roadmap-content">
                Genetic Algorithm · 2-opt · ETA · Chi phí · Bản đồ đường bộ
            </div>
        </div>
        <div class="roadmap-card">
            <div class="roadmap-title">Ngày 3 · Phân tích kết quả</div>
            <div class="roadmap-content">
                SQLite · Dashboard · So sánh thuật toán · Xuất CSV
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("#### Trạng thái kết nối")

    if get_ors_api_key():
        st.sidebar.success("OpenRouteService đã sẵn sàng.")
    else:
        st.sidebar.warning(
            "Chưa tìm thấy ORS_API_KEY trong "
            ".streamlit/secrets.toml."
        )

    st.sidebar.caption(
        "Khoảng cách và thời gian sử dụng dữ liệu định tuyến đường bộ, "
        "không phản ánh giao thông thời gian thực."
    )

def render_data_import() -> None:
    """
    Nhập dữ liệu từ CSV.

    File chỉ được xử lý khi nội dung mới khác file đã tải trước đó,
    tránh làm mất kết quả khi Streamlit rerun.
    """

    render_section_title(
        "📥",
        "1. Nhập dữ liệu",
        "Tải danh sách địa điểm từ CSV hoặc khôi phục bộ dữ liệu mẫu.",
    )

    uploader_key = (
        f"locations_csv_uploader_"
        f"{st.session_state.uploader_version}"
    )

    uploaded_file = st.file_uploader(
        "Tải danh sách địa điểm từ CSV",
        type=["csv"],
        key=uploader_key,
    )

    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.getvalue()
            current_file_hash = hashlib.sha256(file_bytes).hexdigest()

            if current_file_hash != st.session_state.uploaded_csv_hash:
                uploaded_data = pd.read_csv(BytesIO(file_bytes))
                uploaded_data = normalize_locations(uploaded_data)
                errors = validate_locations(uploaded_data)

                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    st.session_state.locations = (
                        uploaded_data.reset_index(drop=True)
                    )
                    st.session_state.result = None
                    st.session_state.uploaded_csv_hash = current_file_hash
                    st.success("Đã tải dữ liệu CSV thành công.")

        except Exception as error:
            st.error(f"Không thể đọc file CSV: {error}")

    if st.button(
        "↻ Khôi phục dữ liệu mẫu",
        key="restore_default_data_button",
    ):
        st.session_state.locations = load_default_data()
        st.session_state.result = None
        st.session_state.uploaded_csv_hash = None
        st.session_state.uploader_version += 1
        st.rerun()


def render_add_location_form() -> None:
    """Form thêm một địa điểm mới."""

    render_section_title(
        "➕",
        "2. Thêm địa điểm",
        "Bổ sung điểm giao hàng mới cùng tọa độ và thời gian phục vụ.",
    )

    with st.form(
        "add_location_form",
        clear_on_submit=True,
    ):
        column_1, column_2 = st.columns(2)

        with column_1:
            name = st.text_input("Tên địa điểm")
            latitude = st.number_input(
                "Vĩ độ",
                min_value=-90.0,
                max_value=90.0,
                value=10.762622,
                format="%.6f",
            )

        with column_2:
            longitude = st.number_input(
                "Kinh độ",
                min_value=-180.0,
                max_value=180.0,
                value=106.660172,
                format="%.6f",
            )
            service_time = st.number_input(
                "Thời gian phục vụ (phút)",
                min_value=0,
                value=5,
                step=1,
            )

        submitted = st.form_submit_button("➕ Thêm địa điểm")

    if not submitted:
        return

    if not name.strip():
        st.error("Tên địa điểm không được để trống.")
        return

    locations = st.session_state.locations.copy()

    new_id = (
        int(locations["id"].max()) + 1
        if not locations.empty
        else 0
    )

    new_row = pd.DataFrame(
        [
            {
                "id": new_id,
                "name": name.strip(),
                "latitude": latitude,
                "longitude": longitude,
                "service_time": service_time,
            }
        ]
    )

    updated_locations = pd.concat(
        [locations, new_row],
        ignore_index=True,
    )
    updated_locations = normalize_locations(updated_locations)
    errors = validate_locations(updated_locations)

    if errors:
        for error in errors:
            st.error(error)
        return

    st.session_state.locations = updated_locations
    st.session_state.result = None
    st.success("Đã thêm địa điểm.")
    st.rerun()


def render_location_editor() -> None:
    """Bảng cho phép sửa và xóa địa điểm."""

    render_section_title(
        "📍",
        "3. Danh sách địa điểm",
        "Chỉnh sửa trực tiếp dữ liệu đầu vào trước khi chạy thuật toán.",
    )

    edited_locations = st.data_editor(
        st.session_state.locations,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn(
                "Mã",
                required=True,
                step=1,
            ),
            "name": st.column_config.TextColumn(
                "Tên địa điểm",
                required=True,
            ),
            "latitude": st.column_config.NumberColumn(
                "Vĩ độ",
                required=True,
                format="%.6f",
            ),
            "longitude": st.column_config.NumberColumn(
                "Kinh độ",
                required=True,
                format="%.6f",
            ),
            "service_time": st.column_config.NumberColumn(
                "Thời gian phục vụ",
                required=True,
                min_value=0,
                step=1,
            ),
        },
        key="location_editor",
    )

    if st.button("💾 Lưu thay đổi danh sách"):
        edited_locations = normalize_locations(edited_locations)
        errors = validate_locations(edited_locations)

        if errors:
            for error in errors:
                st.error(error)
            return

        st.session_state.locations = edited_locations.reset_index(
            drop=True
        )
        st.session_state.result = None
        st.success("Đã lưu danh sách địa điểm.")
        st.rerun()


# =========================================================
# THUẬT TOÁN
# =========================================================

def run_selected_algorithm(
    algorithm: str,
    distance_matrix,
    start_index: int,
    return_to_start: bool,
    ga_parameters: dict[str, int | float],
) -> dict:
    """Chạy thuật toán mà người dùng lựa chọn."""

    if algorithm == "Brute Force":
        return solve_brute_force(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
            max_locations=10,
        )

    if algorithm == "Nearest Neighbor":
        return solve_nearest_neighbor(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
        )

    if algorithm == "Nearest Neighbor + 2-opt":
        base_result = solve_nearest_neighbor(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
        )

        result = solve_two_opt_from_result(
            base_result=base_result,
            distance_matrix=distance_matrix,
            algorithm_name="Nearest Neighbor + 2-opt",
        )
        result["base_evaluated_routes"] = base_result.get(
            "evaluated_routes"
        )

        # File cũ bị thiếu return tại nhánh này.
        return result

    if algorithm == "Genetic Algorithm":
        return solve_genetic_algorithm(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
            population_size=int(ga_parameters["population_size"]),
            generations=int(ga_parameters["generations"]),
            crossover_rate=float(ga_parameters["crossover_rate"]),
            mutation_rate=float(ga_parameters["mutation_rate"]),
            tournament_size=int(ga_parameters["tournament_size"]),
            elite_size=int(ga_parameters["elite_size"]),
            random_seed=int(ga_parameters["random_seed"]),
        )

    if algorithm == "Genetic Algorithm + 2-opt":
        base_result = solve_genetic_algorithm(
            distance_matrix=distance_matrix,
            start_index=start_index,
            return_to_start=return_to_start,
            population_size=int(ga_parameters["population_size"]),
            generations=int(ga_parameters["generations"]),
            crossover_rate=float(ga_parameters["crossover_rate"]),
            mutation_rate=float(ga_parameters["mutation_rate"]),
            tournament_size=int(ga_parameters["tournament_size"]),
            elite_size=int(ga_parameters["elite_size"]),
            random_seed=int(ga_parameters["random_seed"]),
        )

        result = solve_two_opt_from_result(
            base_result=base_result,
            distance_matrix=distance_matrix,
            algorithm_name="Genetic Algorithm + 2-opt",
        )
        result["base_evaluated_routes"] = base_result.get(
            "evaluated_routes"
        )

        return result

    raise ValueError(f"Thuật toán không được hỗ trợ: {algorithm}")


def enrich_result_with_delivery_information(
    result: dict,
    locations: pd.DataFrame,
    distance_matrix,
    duration_matrix_seconds,
    departure_datetime: datetime,
    cost_per_km: float,
) -> dict:
    """Bổ sung ETA và chi phí dựa trên dữ liệu đường giao thông."""

    eta_table, total_duration_minutes = build_road_eta_table(
        display_route=result["display_route"],
        locations=locations,
        distance_matrix_km=distance_matrix,
        duration_matrix_seconds=duration_matrix_seconds,
        departure_datetime=departure_datetime,
    )

    delivery_cost = calculate_delivery_cost(
        total_distance=float(result["distance"]),
        cost_per_km=cost_per_km,
    )

    enriched_result = result.copy()
    enriched_result["eta_table"] = eta_table
    enriched_result["total_duration_minutes"] = float(
        total_duration_minutes
    )
    enriched_result["delivery_cost"] = float(delivery_cost)
    enriched_result["cost_per_km"] = float(cost_per_km)
    enriched_result["departure_datetime"] = departure_datetime

    road_duration_seconds = float(
        result.get("road_duration_seconds", 0.0)
    )

    if road_duration_seconds > 0:
        average_speed_kmh = float(result["distance"]) / (
            road_duration_seconds / 3600.0
        )
    else:
        average_speed_kmh = 0.0

    enriched_result["average_speed_kmh"] = average_speed_kmh

    return enriched_result


# =========================================================
# GIAO DIỆN CẤU HÌNH VÀ CHẠY TỐI ƯU
# =========================================================

def render_algorithm_controls() -> None:
    """Hiển thị toàn bộ cấu hình tối ưu."""

    render_section_title(
        "⚙️",
        "4. Cấu hình lộ trình",
        "Chọn điểm xuất phát, thuật toán, phương tiện và thông số vận hành.",
    )

    locations = st.session_state.locations
    errors = validate_locations(locations)

    if errors:
        for error in errors:
            st.error(error)
        return

    location_options = {
        index: f"{row['name']} — ID {int(row['id'])}"
        for index, row in locations.iterrows()
    }

    option_indices = list(location_options.keys())
    default_start_position = 0

    depot_rows = locations.index[locations["id"] == 0].tolist()

    if depot_rows:
        depot_index = depot_rows[0]
        if depot_index in option_indices:
            default_start_position = option_indices.index(depot_index)

    column_1, column_2, column_3 = st.columns(3)

    with column_1:
        start_index = st.selectbox(
            "Điểm xuất phát",
            options=option_indices,
            index=default_start_position,
            format_func=lambda index: location_options[index],
        )

    with column_2:
        algorithm = st.selectbox(
            "Thuật toán",
            options=ALGORITHM_OPTIONS,
        )

    with column_3:
        route_type = st.radio(
            "Loại lộ trình",
            options=[
                "Khép kín — quay về điểm đầu",
                "Mở — không quay về điểm đầu",
            ],
        )

    return_to_start = route_type.startswith("Khép kín")

    st.markdown("#### Thông tin vận hành")

    operation_column_1, operation_column_2, operation_column_3 = (
        st.columns(3)
    )

    with operation_column_1:
        profile_label = st.selectbox(
            "Phương tiện định tuyến",
            options=list(ROUTING_PROFILE_MAPPING.keys()),
            index=0,
        )

    with operation_column_2:
        cost_per_km = st.number_input(
            "Chi phí mỗi kilomet (VNĐ)",
            min_value=0.0,
            value=2000.0,
            step=500.0,
        )

    with operation_column_3:
        departure_time = st.time_input(
            "Giờ xuất phát",
            value=datetime.now().time().replace(
                second=0,
                microsecond=0,
            ),
        )

    routing_profile = ROUTING_PROFILE_MAPPING[profile_label]

    ga_parameters: dict[str, int | float] = {
        "population_size": 100,
        "generations": 300,
        "crossover_rate": 0.8,
        "mutation_rate": 0.05,
        "tournament_size": 5,
        "elite_size": 2,
        "random_seed": 42,
    }

    if "Genetic Algorithm" in algorithm:
        with st.expander(
            "Cấu hình Genetic Algorithm",
            expanded=True,
        ):
            ga_column_1, ga_column_2, ga_column_3 = st.columns(3)

            with ga_column_1:
                population_size = st.number_input(
                    "Kích thước quần thể",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    step=10,
                )
                generations = st.number_input(
                    "Số thế hệ",
                    min_value=10,
                    max_value=5000,
                    value=300,
                    step=50,
                )

            with ga_column_2:
                crossover_rate = st.number_input(
                    "Tỷ lệ lai ghép",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.8,
                    step=0.05,
                    format="%.2f",
                )
                mutation_rate = st.number_input(
                    "Tỷ lệ đột biến",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.05,
                    step=0.01,
                    format="%.2f",
                )

            with ga_column_3:
                tournament_size = st.number_input(
                    "Tournament size",
                    min_value=2,
                    max_value=int(population_size),
                    value=min(5, int(population_size)),
                    step=1,
                )
                elite_size = st.number_input(
                    "Số cá thể ưu tú",
                    min_value=0,
                    max_value=max(0, int(population_size) - 1),
                    value=min(2, int(population_size) - 1),
                    step=1,
                )
                random_seed = st.number_input(
                    "Random seed",
                    min_value=0,
                    value=42,
                    step=1,
                )

            ga_parameters = {
                "population_size": int(population_size),
                "generations": int(generations),
                "crossover_rate": float(crossover_rate),
                "mutation_rate": float(mutation_rate),
                "tournament_size": int(tournament_size),
                "elite_size": int(elite_size),
                "random_seed": int(random_seed),
            }

    st.caption(
        "Khoảng cách, thời gian và hình học lộ trình được tính theo "
        "mạng lưới đường giao thông OpenStreetMap. Dữ liệu này không "
        "phải tình trạng giao thông thời gian thực."
    )

    if st.button(
        "🚀 Tối ưu lộ trình",
        type="primary",
        use_container_width=True,
    ):
        try:
            api_key = get_ors_api_key()

            if not api_key:
                raise ValueError(
                    "Chưa cấu hình ORS_API_KEY trong "
                    ".streamlit/secrets.toml."
                )

            coordinates_list = locations_to_coordinates(locations)
            coordinates_tuple = tuple(
                (float(longitude), float(latitude))
                for longitude, latitude in coordinates_list
            )

            with st.spinner(
                "Đang tính ma trận khoảng cách và thời gian đường bộ..."
            ):
                distance_matrix, duration_matrix_seconds = (
                    cached_build_road_matrices(
                        coordinates=coordinates_tuple,
                        api_key=api_key,
                        profile=routing_profile,
                    )
                )

            result = run_selected_algorithm(
                algorithm=algorithm,
                distance_matrix=distance_matrix,
                start_index=start_index,
                return_to_start=return_to_start,
                ga_parameters=ga_parameters,
            )

            # Giữ khoảng cách theo ma trận để hiển thị đúng phần 2-opt.
            result["optimized_matrix_distance"] = float(
                result["distance"]
            )

            ordered_coordinates = tuple(
                coordinates_tuple[location_index]
                for location_index in result["display_route"]
            )

            with st.spinner(
                "Đang xây dựng tuyến đường theo mạng lưới giao thông..."
            ):
                route_geojson = cached_get_route_geojson(
                    ordered_coordinates=ordered_coordinates,
                    api_key=api_key,
                    profile=routing_profile,
                )

            actual_route_distance_km, actual_route_duration_seconds = (
                get_route_summary(route_geojson)
            )

            result["route_geojson"] = route_geojson
            result["distance"] = float(actual_route_distance_km)
            result["road_duration_seconds"] = float(
                actual_route_duration_seconds
            )
            result["routing_profile"] = routing_profile
            result["vehicle_label"] = profile_label

            departure_datetime = datetime.combine(
                datetime.now().date(),
                departure_time,
            )

            result = enrich_result_with_delivery_information(
                result=result,
                locations=locations,
                distance_matrix=distance_matrix,
                duration_matrix_seconds=duration_matrix_seconds,
                departure_datetime=departure_datetime,
                cost_per_km=float(cost_per_km),
            )

            result["return_to_start"] = bool(return_to_start)
            result["route_type"] = (
                "Khép kín" if return_to_start else "Mở"
            )
            result["start_index"] = int(start_index)
            result["location_count"] = int(len(locations))

            st.session_state.result = result
            st.session_state.last_saved_history_id = None
            st.success("Đã hoàn thành tối ưu lộ trình đường bộ.")

        except Exception as error:
            st.error(f"Không thể chạy thuật toán: {error}")


def build_history_record(
    result: dict,
    locations: pd.DataFrame,
) -> dict:
    """Chuyển kết quả hiện tại thành bản ghi có thể lưu trong SQLite."""

    display_route = [int(index) for index in result["display_route"]]
    route_names = [
        str(locations.iloc[index]["name"])
        for index in display_route
    ]

    start_index = int(result.get("start_index", display_route[0]))
    start_location = locations.iloc[start_index]
    parameters = result.get("parameters") or {}

    locations_snapshot = [
        {
            "id": int(row["id"]),
            "name": str(row["name"]),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "service_time": float(row["service_time"]),
        }
        for _, row in locations.iterrows()
    ]

    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "algorithm": str(result["algorithm"]),
        "route_type": str(result.get("route_type", "Khép kín")),
        "start_location_id": int(start_location["id"]),
        "start_location_name": str(start_location["name"]),
        "location_count": int(len(locations)),
        "route_indices": json.dumps(display_route),
        "route_names": " → ".join(route_names),
        "distance_km": float(result["distance"]),
        "matrix_distance_km": float(
            result.get("optimized_matrix_distance", result["distance"])
        ),
        "execution_time_seconds": float(result["execution_time"]),
        "delivery_cost": float(result["delivery_cost"]),
        "total_duration_minutes": float(
            result["total_duration_minutes"]
        ),
        "road_duration_seconds": float(
            result.get("road_duration_seconds", 0.0)
        ),
        "average_speed_kmh": float(
            result.get("average_speed_kmh", 0.0)
        ),
        "cost_per_km": float(result["cost_per_km"]),
        "vehicle_label": str(
            result.get("vehicle_label", "Xe giao hàng")
        ),
        "routing_profile": str(
            result.get("routing_profile", "driving-car")
        ),
        "departure_time": result["departure_datetime"].isoformat(),
        "evaluated_routes": (
            int(result["evaluated_routes"])
            if result.get("evaluated_routes") is not None
            else None
        ),
        "improvement_distance": (
            float(result["improvement_distance"])
            if result.get("improvement_distance") is not None
            else None
        ),
        "improvement_percentage": (
            float(result["improvement_percentage"])
            if result.get("improvement_percentage") is not None
            else None
        ),
        "ga_parameters": json.dumps(
            parameters,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "locations_snapshot": json.dumps(
            locations_snapshot,
            ensure_ascii=False,
            sort_keys=True,
        ),
    }


def render_save_history_button(
    result: dict,
    locations: pd.DataFrame,
) -> None:
    """Hiển thị nút lưu kết quả và ngăn lưu lặp cùng một lần chạy."""

    st.markdown("#### Lưu kết quả")

    if st.button(
        "💾 Lưu kết quả vào lịch sử",
        use_container_width=True,
        key="save_optimization_history",
    ):
        record = build_history_record(result, locations)
        created, record_id = save_history(record)
        st.session_state.last_saved_history_id = record_id

        if created:
            st.success(f"Đã lưu kết quả với ID {record_id}.")
        else:
            st.info(
                f"Kết quả này đã tồn tại trong lịch sử với ID {record_id}."
            )


# =========================================================
# BẢN ĐỒ ĐƯỜNG GIAO THÔNG
# =========================================================

def create_route_map(
    locations: pd.DataFrame,
    display_route: list[int],
    route_geojson: dict,
) -> folium.Map:
    """Tạo bản đồ với tuyến đường bám theo mạng lưới giao thông."""

    center_latitude = float(locations["latitude"].mean())
    center_longitude = float(locations["longitude"].mean())

    route_map = folium.Map(
        location=[center_latitude, center_longitude],
        zoom_start=13,
        control_scale=True,
        tiles="CartoDB positron",
    )

    first_index = display_route[0]

    for order, location_index in enumerate(display_route):
        is_return_marker = (
            order == len(display_route) - 1
            and order > 0
            and location_index == first_index
        )

        if is_return_marker:
            continue

        location = locations.iloc[location_index]
        is_start = order == 0

        marker_text = (
            f"Điểm xuất phát: {location['name']}"
            if is_start
            else f"Điểm {order}: {location['name']}"
        )

        folium.Marker(
            location=[
                float(location["latitude"]),
                float(location["longitude"]),
            ],
            popup=marker_text,
            tooltip=marker_text,
            icon=folium.Icon(
                color="red" if is_start else "blue",
                icon="home" if is_start else "info-sign",
            ),
        ).add_to(route_map)

    folium.GeoJson(
        route_geojson,
        name="Lộ trình đường bộ",
        style_function=lambda feature: {
            "color": "#0284c7",
            "weight": 6,
            "opacity": 0.90,
        },
        tooltip="Lộ trình giao hàng",
    ).add_to(route_map)

    bounding_box = route_geojson.get("bbox")

    if bounding_box is not None and len(bounding_box) == 4:
        min_longitude = float(bounding_box[0])
        min_latitude = float(bounding_box[1])
        max_longitude = float(bounding_box[2])
        max_latitude = float(bounding_box[3])

        route_map.fit_bounds(
            [
                [min_latitude, min_longitude],
                [max_latitude, max_longitude],
            ]
        )
    else:
        # Dự phòng nếu GeoJSON không có bbox.
        route_map.fit_bounds(
            [
                [
                    float(locations.iloc[index]["latitude"]),
                    float(locations.iloc[index]["longitude"]),
                ]
                for index in display_route
            ]
        )

    folium.LayerControl().add_to(route_map)

    return route_map


# =========================================================
# HIỂN THỊ KẾT QUẢ
# =========================================================

def render_convergence_chart(result: dict) -> None:
    """Hiển thị biểu đồ hội tụ của Genetic Algorithm."""

    history = result.get("history")

    if history is None or len(history) == 0:
        return

    st.markdown("#### Biểu đồ hội tụ")

    convergence_data = pd.DataFrame(
        {
            "Thế hệ": range(1, len(history) + 1),
            "Khoảng cách tốt nhất (km)": [
                float(value) for value in history
            ],
        }
    ).set_index("Thế hệ")

    st.line_chart(
        convergence_data,
        use_container_width=True,
    )

    st.caption(
        "Khoảng cách tốt nhất được tìm thấy sau từng thế hệ."
    )


def render_two_opt_information(result: dict) -> None:
    """Hiển thị mức cải thiện của 2-opt theo ma trận đường bộ."""

    if "improvement_percentage" not in result:
        return

    st.markdown("#### Hiệu quả cải thiện của 2-opt")

    before_distance = float(result["original_distance"])
    after_distance = float(
        result.get(
            "optimized_matrix_distance",
            result["distance"],
        )
    )

    column_1, column_2, column_3 = st.columns(3)

    with column_1:
        st.metric(
            "Trước 2-opt",
            f"{before_distance:.3f} km",
        )

    with column_2:
        st.metric(
            "Sau 2-opt",
            f"{after_distance:.3f} km",
        )

    with column_3:
        st.metric(
            "Tỷ lệ cải thiện",
            f"{result['improvement_percentage']:.2f}%",
            delta=f"-{result['improvement_distance']:.3f} km",
        )

    st.caption(
        "Các chỉ số 2-opt được tính từ ma trận khoảng cách đường bộ; "
        "tổng quãng đường phía trên lấy từ tuyến GeoJSON cuối cùng."
    )


def render_eta_information(result: dict) -> None:
    """Hiển thị bảng thời gian đến dự kiến."""

    eta_table = result.get("eta_table")

    if eta_table is None:
        return

    st.markdown("#### Thời gian giao hàng dự kiến")

    eta_display = eta_table.rename(
        columns={
            "order": "Thứ tự",
            "location_id": "Mã",
            "location_name": "Địa điểm",
            "segment_distance_km": "Quãng đường chặng (km)",
            "travel_time_minutes": "Di chuyển (phút)",
            "arrival_time": "Đến dự kiến",
            "service_time_minutes": "Phục vụ (phút)",
            "departure_time": "Rời đi",
        }
    )

    st.dataframe(
        eta_display,
        use_container_width=True,
        hide_index=True,
    )


def render_result() -> None:
    """Hiển thị kết quả tối ưu."""

    result = st.session_state.get("result")

    if result is None:
        st.info(
            "Hãy chọn thuật toán và nhấn “Tối ưu lộ trình”."
        )
        return

    locations = st.session_state.locations

    render_section_title(
        "📈",
        "5. Kết quả tối ưu",
        "Theo dõi quãng đường, chi phí, thời gian, ETA và tuyến đường đề xuất.",
    )

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

    with metric_1:
        st.metric("Thuật toán", result["algorithm"])

    with metric_2:
        st.metric(
            "Tổng quãng đường đường bộ",
            f"{result['distance']:.3f} km",
        )

    with metric_3:
        st.metric(
            "Thời gian xử lý thuật toán",
            f"{result['execution_time']:.6f} giây",
        )

    with metric_4:
        st.metric(
            "Chi phí dự kiến",
            f"{result['delivery_cost']:,.0f} VNĐ",
        )

    road_duration_minutes = float(
        result.get("road_duration_seconds", 0.0)
    ) / 60.0

    detail_1, detail_2, detail_3, detail_4 = st.columns(4)

    with detail_1:
        st.metric(
            "Tổng thời gian dự kiến",
            format_duration(result["total_duration_minutes"]),
        )

    with detail_2:
        st.metric(
            "Thời gian di chuyển",
            format_duration(road_duration_minutes),
        )

    with detail_3:
        st.metric(
            "Tốc độ trung bình tuyến",
            f"{result['average_speed_kmh']:.1f} km/h",
        )

    with detail_4:
        st.metric(
            "Phương tiện",
            result.get("vehicle_label", "Xe giao hàng"),
        )

    departure_datetime = result["departure_datetime"]
    st.caption(
        f"Giờ xuất phát: {departure_datetime.strftime('%H:%M')} · "
        f"Hồ sơ định tuyến: {result.get('routing_profile', 'driving-car')}"
    )

    route_text = format_route(
        result["display_route"],
        locations,
    )

    st.markdown("#### Thứ tự di chuyển")
    st.success(route_text)

    evaluated_routes = result.get("evaluated_routes")

    if evaluated_routes is not None:
        st.write(
            "Số phương án đã đánh giá:",
            f"{int(evaluated_routes):,}",
        )

    parameters = result.get("parameters")

    if parameters:
        with st.expander("Tham số Genetic Algorithm"):
            parameter_table = pd.DataFrame(
                [
                    {
                        "Tham số": key,
                        "Giá trị": value,
                    }
                    for key, value in parameters.items()
                ]
            )

            st.dataframe(
                parameter_table,
                use_container_width=True,
                hide_index=True,
            )

    render_two_opt_information(result)
    render_convergence_chart(result)
    render_eta_information(result)

    st.markdown("#### Chi tiết lộ trình")

    route_table = locations.iloc[
        result["display_route"]
    ][
        [
            "id",
            "name",
            "latitude",
            "longitude",
            "service_time",
        ]
    ].copy()

    route_table.insert(
        0,
        "order",
        range(len(route_table)),
    )

    route_table = route_table.rename(
        columns={
            "order": "Thứ tự",
            "id": "Mã",
            "name": "Tên địa điểm",
            "latitude": "Vĩ độ",
            "longitude": "Kinh độ",
            "service_time": "Thời gian phục vụ",
        }
    )

    st.dataframe(
        route_table,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Bản đồ lộ trình đường bộ")

    route_geojson = result.get("route_geojson")

    if route_geojson:
        route_map = create_route_map(
            locations=locations,
            display_route=result["display_route"],
            route_geojson=route_geojson,
        )

        folium_static(
            route_map,
            width=1200,
            height=550,
        )
    else:
        st.warning("Chưa có dữ liệu tuyến đường bộ.")

    render_save_history_button(result, locations)


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    initialize_database()
    initialize_session_state()

    apply_custom_ui()
    render_sidebar()
    render_hero_header()

    tab_data, tab_optimization, tab_history = st.tabs(
        [
            "📍 Quản lý địa điểm",
            "🧠 Tối ưu lộ trình",
            "📊 Lịch sử & thống kê",
        ]
    )

    with tab_data:
        render_data_import()
        st.divider()
        render_add_location_form()
        st.divider()
        render_location_editor()

    with tab_optimization:
        render_algorithm_controls()
        st.divider()
        render_result()

    with tab_history:
        render_history_dashboard()


if __name__ == "__main__":
    main()
