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
    """Áp dụng giao diện logistics-tech chuyên nghiệp và nhất quán."""

    st.markdown(
        """
        <style>
        :root {
            --primary-900: #0c4a6e;
            --primary-800: #075985;
            --primary-700: #0369a1;
            --primary-600: #0284c7;
            --primary-500: #0ea5e9;
            --cyan-500: #06b6d4;
            --teal-600: #0d9488;
            --success-600: #059669;
            --surface: rgba(255, 255, 255, 0.84);
            --surface-strong: rgba(255, 255, 255, 0.96);
            --border: rgba(7, 89, 133, 0.10);
            --border-hover: rgba(2, 132, 199, 0.24);
            --text-main: #0f172a;
            --text-muted: #526274;
            --radius-card: 18px;
            --shadow-card: 0 8px 24px rgba(15, 76, 110, 0.08);
            --shadow-hover: 0 14px 30px rgba(15, 76, 110, 0.14);
        }

        html {
            scroll-behavior: smooth;
        }

        .stApp {
            color: var(--text-main);
            background:
                radial-gradient(
                    circle at 12% 8%,
                    rgba(14, 165, 233, 0.10),
                    transparent 31%
                ),
                radial-gradient(
                    circle at 88% 12%,
                    rgba(13, 148, 136, 0.08),
                    transparent 29%
                ),
                linear-gradient(
                    135deg,
                    #f8fbff 0%,
                    #f2f8fb 52%,
                    #f5faf8 100%
                );
            background-attachment: fixed;
        }

        [data-testid="stHeader"] {
            background: rgba(248, 251, 255, 0.76);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid rgba(7, 89, 133, 0.06);
        }

        .block-container {
            max-width: 1240px;
            padding-top: 1rem;
            padding-bottom: 3rem;
        }

        /* Hero gọn hơn, ưu tiên nội dung chức năng */
        .hero-banner {
            position: relative;
            overflow: hidden;
            padding: 23px 28px;
            margin-bottom: 14px;
            border-radius: 23px;
            color: white;
            background:
                linear-gradient(
                    118deg,
                    rgba(3, 105, 161, 0.98) 0%,
                    rgba(2, 132, 199, 0.96) 54%,
                    rgba(6, 182, 212, 0.92) 100%
                );
            box-shadow: 0 16px 40px rgba(2, 84, 125, 0.20);
            isolation: isolate;
            animation: fade-up 0.45s ease-out both;
        }

        .hero-banner::before,
        .hero-banner::after {
            content: "";
            position: absolute;
            border-radius: 999px;
            z-index: -1;
        }

        .hero-banner::before {
            width: 190px;
            height: 190px;
            top: -96px;
            right: 6%;
            background: rgba(255, 255, 255, 0.09);
        }

        .hero-banner::after {
            width: 135px;
            height: 135px;
            right: -38px;
            bottom: -72px;
            border: 22px solid rgba(255, 255, 255, 0.08);
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 6px 12px;
            margin-bottom: 10px;
            border: 1px solid rgba(255, 255, 255, 0.26);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.13);
            backdrop-filter: blur(10px);
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .hero-title {
            max-width: 960px;
            margin: 0;
            font-size: clamp(1.7rem, 3.3vw, 2.28rem);
            font-weight: 850;
            line-height: 1.16;
            letter-spacing: -0.025em;
        }

        .hero-subtitle {
            max-width: 930px;
            margin-top: 9px;
            font-size: 0.95rem;
            line-height: 1.62;
            color: rgba(255, 255, 255, 0.91);
        }

        .hero-features {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }

        .hero-feature {
            padding: 7px 10px;
            border-radius: 11px;
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.16);
            font-size: 0.79rem;
            font-weight: 680;
            transition:
                transform 180ms ease,
                background 180ms ease;
        }

        .hero-feature:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.20);
        }

        /* Quick stats */
        .quick-stats {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 0 0 14px;
        }

        .quick-stat {
            display: flex;
            align-items: center;
            gap: 11px;
            min-height: 68px;
            padding: 11px 13px;
            border: 1px solid var(--border);
            border-radius: 16px;
            background: var(--surface);
            box-shadow: var(--shadow-card);
            backdrop-filter: blur(12px);
            transition:
                transform 180ms ease,
                box-shadow 180ms ease,
                border-color 180ms ease,
                background 180ms ease;
        }

        .quick-stat:hover {
            transform: translateY(-3px);
            border-color: var(--border-hover);
            background: var(--surface-strong);
            box-shadow: var(--shadow-hover);
        }

        .quick-stat-icon {
            display: grid;
            place-items: center;
            flex: 0 0 36px;
            width: 36px;
            height: 36px;
            border-radius: 12px;
            background: linear-gradient(135deg, #e0f2fe, #ccfbf1);
            font-size: 1rem;
        }

        .quick-stat-value {
            color: var(--primary-800);
            font-size: 1rem;
            font-weight: 850;
            line-height: 1.2;
        }

        .quick-stat-label {
            margin-top: 2px;
            color: var(--text-muted);
            font-size: 0.75rem;
            line-height: 1.3;
        }

        /* Section heading */
        .section-heading {
            display: flex;
            gap: 13px;
            align-items: flex-start;
            padding: 15px 17px;
            margin: 6px 0 13px;
            border: 1px solid var(--border);
            border-radius: var(--radius-card);
            background: var(--surface);
            box-shadow: var(--shadow-card);
            backdrop-filter: blur(12px);
            transition:
                transform 180ms ease,
                box-shadow 180ms ease,
                border-color 180ms ease;
        }

        .section-heading:hover {
            transform: translateY(-3px);
            border-color: var(--border-hover);
            box-shadow: var(--shadow-hover);
        }

        .section-icon {
            display: grid;
            place-items: center;
            flex: 0 0 41px;
            width: 41px;
            height: 41px;
            border-radius: 13px;
            background: linear-gradient(135deg, #e0f2fe, #cffafe);
            font-size: 1.18rem;
            box-shadow: inset 0 0 0 1px rgba(2, 132, 199, 0.08);
        }

        .section-title {
            margin: 0;
            color: var(--primary-800);
            font-size: 1.05rem;
            font-weight: 820;
            line-height: 1.3;
        }

        .section-description {
            margin-top: 3px;
            color: var(--text-muted);
            font-size: 0.84rem;
            line-height: 1.5;
        }

        .control-group-header {
            display: flex;
            align-items: center;
            gap: 9px;
            margin: 0 0 12px;
            color: var(--primary-800);
            font-size: 0.94rem;
            font-weight: 820;
        }

        .control-group-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--primary-500), var(--teal-600));
            box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.10);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background:
                radial-gradient(
                    circle at 30% 0%,
                    rgba(14, 165, 233, 0.12),
                    transparent 26%
                ),
                linear-gradient(180deg, #f7fbff 0%, #f1f8f5 100%);
            border-right: 1px solid rgba(7, 89, 133, 0.07);
        }

        [data-testid="stSidebarContent"] {
            padding-top: 1rem;
        }

        .sidebar-brand {
            padding: 17px;
            margin-bottom: 13px;
            border-radius: 19px;
            color: white;
            background: linear-gradient(145deg, #075985, #0891b2);
            box-shadow: 0 12px 28px rgba(7, 89, 133, 0.18);
        }

        .sidebar-brand-title {
            font-size: 1.08rem;
            font-weight: 850;
        }

        .sidebar-brand-subtitle {
            margin-top: 5px;
            color: rgba(255, 255, 255, 0.82);
            font-size: 0.77rem;
            line-height: 1.42;
        }

        .roadmap-card {
            padding: 12px 13px;
            margin: 8px 0;
            border: 1px solid var(--border);
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.73);
            transition:
                transform 180ms ease,
                box-shadow 180ms ease,
                background 180ms ease;
        }

        .roadmap-card:hover {
            transform: translateX(3px);
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 10px 22px rgba(7, 89, 133, 0.09);
        }

        .roadmap-title {
            color: var(--primary-800);
            font-size: 0.85rem;
            font-weight: 820;
        }

        .roadmap-content {
            margin-top: 4px;
            color: var(--text-muted);
            font-size: 0.75rem;
            line-height: 1.5;
        }

        /* Tabs */
        div[data-baseweb="tab-list"] {
            gap: 8px;
            padding: 5px;
            border: 1px solid rgba(7, 89, 133, 0.08);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.66);
            box-shadow: 0 7px 20px rgba(7, 89, 133, 0.05);
            backdrop-filter: blur(12px);
        }

        button[data-baseweb="tab"] {
            min-height: 44px;
            padding: 0 17px;
            border-radius: 11px;
            color: #334155;
            font-weight: 720;
            transition:
                transform 180ms ease,
                background 180ms ease,
                color 180ms ease,
                box-shadow 180ms ease;
        }

        button[data-baseweb="tab"]:hover {
            transform: translateY(-2px);
            color: var(--primary-800);
            background: rgba(224, 242, 254, 0.85);
            box-shadow: 0 8px 16px rgba(7, 89, 133, 0.09);
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: white !important;
            background: linear-gradient(
                135deg,
                var(--primary-700),
                var(--primary-600),
                var(--teal-600)
            ) !important;
            box-shadow: 0 8px 18px rgba(8, 145, 178, 0.22);
            transform: translateY(-1px);
        }

        div[data-baseweb="tab-highlight"] {
            display: none;
        }

        /* Native bordered containers become control panels */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--border) !important;
            border-radius: var(--radius-card) !important;
            background: rgba(255, 255, 255, 0.70) !important;
            box-shadow: var(--shadow-card);
            backdrop-filter: blur(12px);
            transition:
                transform 180ms ease,
                box-shadow 180ms ease,
                border-color 180ms ease;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: var(--border-hover) !important;
            box-shadow: var(--shadow-hover);
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {
            min-height: 43px;
            border: 1px solid rgba(2, 132, 199, 0.13);
            border-radius: 13px;
            color: var(--primary-800);
            background: linear-gradient(135deg, #fafdff, #eaf7fb);
            font-weight: 760;
            box-shadow: 0 7px 17px rgba(7, 89, 133, 0.07);
            transition:
                transform 180ms ease,
                box-shadow 180ms ease,
                filter 180ms ease,
                border-color 180ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-2px);
            border-color: rgba(2, 132, 199, 0.31);
            box-shadow: 0 12px 24px rgba(7, 89, 133, 0.14);
            filter: brightness(1.02);
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
                #0369a1 0%,
                #0891b2 56%,
                #0d9488 100%
            ) !important;
            box-shadow:
                0 12px 25px rgba(2, 132, 199, 0.22),
                0 0 0 1px rgba(255, 255, 255, 0.12) inset !important;
        }

        button[kind="primary"]:hover {
            box-shadow:
                0 16px 30px rgba(2, 132, 199, 0.29),
                0 0 18px rgba(6, 182, 212, 0.16) !important;
        }

        /* Inputs */
        div[data-baseweb="select"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stTextArea"] textarea {
            border-color: rgba(7, 89, 133, 0.14) !important;
            border-radius: 12px !important;
            background: rgba(255, 255, 255, 0.92) !important;
            transition:
                border-color 180ms ease,
                box-shadow 180ms ease,
                background 180ms ease;
        }

        div[data-baseweb="select"] > div:hover,
        [data-testid="stTextInput"] input:hover,
        [data-testid="stNumberInput"] input:hover,
        [data-testid="stTimeInput"] input:hover,
        [data-testid="stTextArea"] textarea:hover {
            border-color: rgba(2, 132, 199, 0.44) !important;
            background: white !important;
            box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.08);
        }

        div[data-baseweb="select"] > div:focus-within,
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTimeInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--primary-500) !important;
            box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.12) !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            padding: 10px;
            border: 1px solid var(--border);
            border-radius: var(--radius-card);
            background: var(--surface);
            box-shadow: var(--shadow-card);
            transition:
                transform 180ms ease,
                box-shadow 180ms ease;
        }

        [data-testid="stFileUploader"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
        }

        [data-testid="stFileUploaderDropzone"] {
            border: 1.5px dashed rgba(2, 132, 199, 0.26);
            border-radius: 14px;
            background: linear-gradient(135deg, #f9fdff, #f2fbf9);
        }

        /* Metrics */
        [data-testid="stMetric"] {
            height: 100%;
            padding: 14px 15px 13px;
            border: 1px solid var(--border);
            border-radius: var(--radius-card);
            background: var(--surface);
            box-shadow: var(--shadow-card);
            backdrop-filter: blur(12px);
            animation: metric-enter 0.34s ease-out both;
            transition:
                transform 180ms ease,
                box-shadow 180ms ease,
                border-color 180ms ease,
                background 180ms ease;
        }

        [data-testid="stMetric"]:hover {
            transform: translateY(-4px);
            border-color: var(--border-hover);
            background: var(--surface-strong);
            box-shadow: var(--shadow-hover);
        }

        [data-testid="stMetricLabel"] {
            color: #526274;
            font-weight: 660;
        }

        [data-testid="stMetricValue"] {
            color: var(--primary-800);
            font-weight: 860;
        }

        /* Data, forms, expanders and status */
        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"],
        [data-testid="stForm"],
        [data-testid="stExpander"],
        [data-testid="stStatusWidget"] {
            border: 1px solid var(--border);
            border-radius: var(--radius-card);
            background: rgba(255, 255, 255, 0.78);
            box-shadow: var(--shadow-card);
            overflow: hidden;
            transition:
                box-shadow 180ms ease,
                border-color 180ms ease;
        }

        [data-testid="stDataFrame"]:hover,
        [data-testid="stDataEditor"]:hover,
        [data-testid="stForm"]:hover,
        [data-testid="stExpander"]:hover,
        [data-testid="stStatusWidget"]:hover {
            border-color: var(--border-hover);
            box-shadow: var(--shadow-hover);
        }

        [data-testid="stForm"] {
            padding: 15px;
        }

        /* Alerts */
        [data-testid="stAlert"] {
            border-radius: 15px;
            border: 1px solid rgba(7, 89, 133, 0.09);
            box-shadow: 0 8px 18px rgba(7, 89, 133, 0.05);
            animation: fade-up 0.28s ease-out both;
        }

        /* Charts and maps */
        [data-testid="stVegaLiteChart"],
        [data-testid="stArrowVegaLiteChart"],
        iframe {
            border-radius: var(--radius-card) !important;
            box-shadow: 0 12px 28px rgba(7, 89, 133, 0.11);
        }

        iframe {
            border: 1px solid rgba(7, 89, 133, 0.09) !important;
        }

        .map-caption {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 4px 0 12px;
        }

        .map-caption span {
            padding: 5px 9px;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.86);
            color: var(--text-muted);
            font-size: 0.75rem;
            font-weight: 650;
        }

        /* Titles and dividers */
        h1, h2, h3, h4 {
            color: #0f4c6e;
        }

        h4 {
            margin-top: 1.2rem !important;
            padding-left: 9px;
            border-left: 4px solid var(--cyan-500);
        }

        hr {
            margin: 1.25rem 0 !important;
            border-color: rgba(7, 89, 133, 0.09) !important;
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 9px;
            height: 9px;
        }

        ::-webkit-scrollbar-track {
            background: #edf7fb;
        }

        ::-webkit-scrollbar-thumb {
            border: 2px solid #edf7fb;
            border-radius: 999px;
            background: linear-gradient(#38bdf8, #0e7490);
        }

        @keyframes fade-up {
            from {
                opacity: 0;
                transform: translateY(9px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes metric-enter {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 900px) {
            .quick-stats {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero-banner {
                padding: 21px 18px;
                border-radius: 20px;
            }

            .hero-features {
                gap: 6px;
            }

            button[data-baseweb="tab"] {
                padding: 0 9px;
                font-size: 0.79rem;
            }
        }

        @media (max-width: 540px) {
            .quick-stats {
                grid-template-columns: 1fr;
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
                AI PROJECT · ROUTE OPTIMIZATION
            </div>
            <h1 class="hero-title">
                Bài toán tối ưu lộ trình giao hàng bằng TSP
            </h1>
            <div class="hero-subtitle">
                Ứng dụng minh họa các thuật toán giải Traveling Salesman
                Problem nhằm đề xuất thứ tự giao hàng, giảm tổng quãng đường
                và hỗ trợ ước tính chi phí, thời gian di chuyển trên mạng
                lưới đường giao thông thực tế.
            </div>
            <div class="hero-features">
                <div class="hero-feature">5 phương pháp tối ưu</div>
                <div class="hero-feature">Định tuyến đường bộ</div>
                <div class="hero-feature">ETA theo từng chặng</div>
                <div class="hero-feature">Lịch sử và thống kê</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

def render_quick_stats() -> None:
    """Hiển thị các chỉ số tóm tắt ngay dưới hero."""

    location_count = len(st.session_state.get("locations", []))

    st.markdown(
        f"""
        <div class="quick-stats">
            <div class="quick-stat">
                <div class="quick-stat-icon">A</div>
                <div>
                    <div class="quick-stat-value">5 phương pháp</div>
                    <div class="quick-stat-label">Exact, heuristic và metaheuristic</div>
                </div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-icon">R</div>
                <div>
                    <div class="quick-stat-value">3 phương tiện</div>
                    <div class="quick-stat-label">Xe giao hàng, xe đạp và đi bộ</div>
                </div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-icon">P</div>
                <div>
                    <div class="quick-stat-value">{location_count} địa điểm</div>
                    <div class="quick-stat-label">Dữ liệu đang được sử dụng</div>
                </div>
            </div>
            <div class="quick-stat">
                <div class="quick-stat-icon">D</div>
                <div>
                    <div class="quick-stat-value">ORS + SQLite</div>
                    <div class="quick-stat-label">Định tuyến thực tế và lưu lịch sử</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_control_group_header(
    title: str,
    description: str,
) -> None:
    """Hiển thị tiêu đề nhỏ cho từng nhóm điều khiển."""

    st.markdown(
        f"""
        <div class="control-group-header">
            <span class="control-group-dot"></span>
            <span>{title}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(description)




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
                Ứng dụng thử nghiệm thuật toán tối ưu lộ trình giao hàng
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

    st.sidebar.markdown("#### Tiến độ chức năng")
    st.sidebar.progress(90)
    st.sidebar.caption("Đồ án đã hoàn thành khoảng 90% chức năng dự kiến.")

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
        "Thiết lập bài toán, phương tiện và thông số vận hành trước khi tối ưu.",
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

    with st.container(border=True):
        render_control_group_header(
            "Cấu hình bài toán",
            "Xác định điểm xuất phát, thuật toán và dạng lộ trình.",
        )

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

    with st.container(border=True):
        render_control_group_header(
            "Thông tin vận hành",
            "Thiết lập phương tiện, chi phí và thời điểm bắt đầu giao hàng.",
        )

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
        "⚡ Bắt đầu tối ưu lộ trình",
        type="primary",
        use_container_width=True,
    ):
        process_status = None

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

            with st.status(
                "Đang xử lý lộ trình...",
                expanded=True,
            ) as process_status:
                process_status.write(
                    "Bước 1/4 · Xây dựng ma trận khoảng cách và thời gian đường bộ."
                )
                distance_matrix, duration_matrix_seconds = (
                    cached_build_road_matrices(
                        coordinates=coordinates_tuple,
                        api_key=api_key,
                        profile=routing_profile,
                    )
                )

                process_status.write(
                    f"Bước 2/4 · Chạy thuật toán {algorithm}."
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

                process_status.write(
                    "Bước 3/4 · Dựng tuyến đường trên mạng lưới giao thông."
                )
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

                process_status.write(
                    "Bước 4/4 · Tính ETA, tốc độ và chi phí giao hàng."
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

                process_status.update(
                    label="Đã hoàn tất tối ưu lộ trình.",
                    state="complete",
                    expanded=False,
                )

            st.success("Kết quả đã sẵn sàng ở phần bên dưới.")

        except Exception as error:
            if process_status is not None:
                process_status.update(
                    label="Quá trình tối ưu không hoàn tất.",
                    state="error",
                    expanded=True,
                )
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
    """Tạo bản đồ đường bộ với marker đánh số theo thứ tự giao hàng."""

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
        is_open_route_end = (
            order == len(display_route) - 1
            and location_index != first_index
        )

        if is_start:
            marker_label = "K"
            marker_color = "#dc2626"
            marker_role = "Điểm xuất phát"
        elif is_open_route_end:
            marker_label = str(order)
            marker_color = "#059669"
            marker_role = "Điểm kết thúc"
        else:
            marker_label = str(order)
            marker_color = "#0284c7"
            marker_role = f"Điểm giao thứ {order}"

        marker_text = (
            f"{marker_role}: {location['name']}"
        )
        popup_html = (
            f"<b>{marker_role}</b><br>"
            f"{location['name']}<br>"
            f"Mã địa điểm: {int(location['id'])}<br>"
            f"Thời gian phục vụ: {float(location['service_time']):g} phút"
        )

        marker_html = f"""
        <div style="
            display:flex;
            align-items:center;
            justify-content:center;
            width:34px;
            height:34px;
            border-radius:50%;
            background:{marker_color};
            color:white;
            font-size:13px;
            font-weight:800;
            border:3px solid rgba(255,255,255,0.96);
            box-shadow:0 5px 13px rgba(15,23,42,0.28);
        ">{marker_label}</div>
        """

        folium.Marker(
            location=[
                float(location["latitude"]),
                float(location["longitude"]),
            ],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=marker_text,
            icon=folium.DivIcon(
                html=marker_html,
                icon_size=(34, 34),
                icon_anchor=(17, 17),
                class_name="tsp-numbered-marker",
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
        highlight_function=lambda feature: {
            "color": "#06b6d4",
            "weight": 8,
            "opacity": 1.0,
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
        route_map.fit_bounds(
            [
                [
                    float(locations.iloc[index]["latitude"]),
                    float(locations.iloc[index]["longitude"]),
                ]
                for index in display_route
            ]
        )

    legend_html = """
    <div style="
        position: fixed;
        left: 18px;
        bottom: 24px;
        z-index: 9999;
        padding: 10px 12px;
        border-radius: 12px;
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(7,89,133,0.12);
        box-shadow: 0 8px 20px rgba(15,76,110,0.14);
        color: #334155;
        font-size: 12px;
        line-height: 1.7;
    ">
        <div style="font-weight:800;color:#075985;margin-bottom:3px;">
            Chú thích lộ trình
        </div>
        <div><span style="color:#dc2626;">●</span> K: Điểm xuất phát</div>
        <div><span style="color:#0284c7;">●</span> 1, 2, 3...: Thứ tự giao</div>
        <div><span style="color:#059669;">●</span> Điểm kết thúc tuyến mở</div>
        <div><span style="color:#0284c7;">━</span> Tuyến đường đề xuất</div>
    </div>
    """
    route_map.get_root().html.add_child(folium.Element(legend_html))

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
    st.markdown(
        """
        <div class="map-caption">
            <span>Đỏ: điểm xuất phát</span>
            <span>Xanh dương: thứ tự giao hàng</span>
            <span>Xanh lá: điểm cuối tuyến mở</span>
            <span>Di chuột lên tuyến để làm nổi bật</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    route_geojson = result.get("route_geojson")

    with st.container(border=True):
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
    render_quick_stats()

    tab_data, tab_optimization, tab_history = st.tabs(
        [
            "Quản lý địa điểm",
            "Tối ưu lộ trình",
            "Lịch sử & thống kê",
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
