"""Streamlit 캐싱이 적용된 서비스 래퍼 함수들

Service 계층은 Streamlit 의존성 없이 순수 비즈니스 로직을 유지하고,
UI 계층에서 필요한 경우에만 캐싱을 적용합니다.

TTL (Time To Live):
- 선수/구장 데이터: 5분 (자주 변경되지 않음)
- 경기 데이터: 1분 (상대적으로 자주 변경됨)
- 정적 옵션: 10분 (거의 변경되지 않음)
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import date

from services.player_service import player_service
from services.field_service import field_service
from services.match_service import match_service
from services.attendance_service import attendance_service
from services.news_service import news_service


# ============================================================================
# Player Service 캐싱
# ============================================================================

@st.cache_data(ttl=300)  # 5분 캐시
def get_all_players_cached() -> List[Dict[str, Any]]:
    """활성 선수 목록 조회 (캐시됨)

    Returns:
        활성 선수 목록
    """
    return player_service.get_all_players()


@st.cache_data(ttl=300)
def get_player_stats_cached(player_id: int) -> Dict[str, Any]:
    """선수 통계 조회 (캐시됨)

    Args:
        player_id: 선수 ID

    Returns:
        선수 통계 정보
    """
    return player_service.get_player_stats(player_id)


@st.cache_data(ttl=300)
def get_total_players_count_cached() -> int:
    """총 선수 수 조회 (캐시됨)

    Returns:
        활성 선수 수
    """
    return player_service.get_total_count()


# ============================================================================
# Field Service 캐싱
# ============================================================================

@st.cache_data(ttl=300)  # 5분 캐시
def get_available_fields_cached() -> List[Dict[str, Any]]:
    """사용 가능한 구장 목록 조회 (캐시됨)

    Returns:
        구장 목록 (display_name 포함)
    """
    return match_service.get_available_fields()


# ============================================================================
# Match Service 캐싱
# ============================================================================

@st.cache_data(ttl=60)  # 1분 캐시 (경기 데이터는 자주 변경될 수 있음)
def get_next_match_cached() -> Optional[Dict[str, Any]]:
    """다음 경기 조회 (캐시됨)

    Returns:
        다음 경기 정보 또는 None
    """
    return match_service.get_next_match()


@st.cache_data(ttl=60)
def get_monthly_matches_cached(year: int, month: int) -> List[Dict[str, Any]]:
    """월별 경기 목록 조회 (캐시됨)

    Args:
        year: 년도
        month: 월

    Returns:
        경기 목록
    """
    return match_service.get_monthly_matches(year, month)


@st.cache_data(ttl=60)
def get_recent_matches_cached(limit: int = 5) -> List[Dict[str, Any]]:
    """최근 경기 조회 (캐시됨)

    Args:
        limit: 조회할 경기 수

    Returns:
        최근 경기 목록
    """
    return match_service.get_recent_matches(limit)


@st.cache_data(ttl=60)
def get_matches_in_range_cached(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """날짜 범위로 경기 조회 (캐시됨) - 달력용

    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜

    Returns:
        경기 목록
    """
    return match_service.get_matches_in_range(start_date, end_date)


@st.cache_data(ttl=60)
def get_monthly_match_count_cached() -> int:
    """이번 달 경기 수 조회 (캐시됨)

    Returns:
        이번 달 경기 수
    """
    return match_service.get_monthly_count()


# ============================================================================
# Attendance Service 캐싱
# ============================================================================

@st.cache_data(ttl=600)  # 10분 캐시 (정적 데이터)
def get_attendance_status_options_cached() -> List[tuple]:
    """출석 상태 선택 옵션 조회 (캐시됨)

    Returns:
        [(status_code, display_name), ...]
    """
    return attendance_service.get_status_options()


# ============================================================================
# News Service 캐싱
# ============================================================================

@st.cache_data(ttl=120)  # 2분 캐시 (뉴스는 비교적 자주 변경될 수 있음)
def get_recent_news_cached(limit: int = 5) -> List[Dict[str, Any]]:
    """최근 뉴스 조회 (캐시됨)

    Args:
        limit: 조회할 뉴스 수

    Returns:
        최근 뉴스 목록
    """
    return news_service.get_recent_news(limit)


# ============================================================================
# 캐시 무효화 유틸리티
# ============================================================================

def clear_player_cache():
    """선수 관련 캐시 무효화

    사용 시점:
    - 선수 추가/수정/삭제 후
    """
    get_all_players_cached.clear()
    get_total_players_count_cached.clear()
    # 특정 선수 통계는 자동으로 TTL에 의해 만료됨


def clear_field_cache():
    """구장 관련 캐시 무효화

    사용 시점:
    - 구장 추가/수정 후
    """
    get_available_fields_cached.clear()


def clear_match_cache():
    """경기 관련 캐시 무효화

    사용 시점:
    - 경기 추가/수정/삭제 후
    """
    get_next_match_cached.clear()
    get_monthly_matches_cached.clear()
    get_recent_matches_cached.clear()
    get_matches_in_range_cached.clear()


def clear_all_cache():
    """모든 캐시 무효화

    사용 시점:
    - 대량 데이터 변경 후
    - 디버깅 목적
    """
    st.cache_data.clear()
