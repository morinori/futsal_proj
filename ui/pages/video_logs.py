"""비디오 로그 뷰어 페이지 (관리자 전용)"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from database.repositories import video_repo
from database.connection import db_manager
from utils.auth_utils import require_admin_access

def render_video_logs_page():
    """비디오 로그 뷰어 페이지"""
    require_admin_access()

    st.title("📊 비디오 재생 로그")
    st.write("사용자들의 비디오 재생 상태와 에러를 모니터링합니다.")

    # 필터 옵션
    col1, col2, col3 = st.columns(3)

    with col1:
        # 로그 레벨 필터
        level_filter = st.selectbox(
            "로그 레벨",
            ["전체", "info", "warn", "error"],
            key="log_level_filter"
        )

    with col2:
        # 비디오 필터
        videos = video_repo.get_all_videos()
        video_options = ["전체"] + [f"{v['id']} - {v['title']}" for v in videos]
        video_filter = st.selectbox(
            "비디오",
            video_options,
            key="video_filter"
        )

    with col3:
        # 시간 범위 필터
        time_filter = st.selectbox(
            "시간 범위",
            ["최근 1시간", "최근 24시간", "최근 7일", "최근 30일", "전체"],
            index=1,
            key="time_filter"
        )

    # 로그 데이터 조회
    logs = fetch_video_logs(level_filter, video_filter, time_filter)

    if not logs:
        st.info("로그가 없습니다.")
        return

    # 통계 요약
    st.divider()
    st.subheader("📈 로그 통계")
    display_log_statistics(logs)

    st.divider()

    # 에러 로그 하이라이트
    error_logs = [log for log in logs if log['level'] == 'error']
    if error_logs:
        st.subheader(f"🚨 에러 로그 ({len(error_logs)}건)")
        display_error_logs(error_logs)
        st.divider()

    # 전체 로그 테이블
    st.subheader("📋 전체 로그")
    display_logs_table(logs)


def fetch_video_logs(level_filter: str, video_filter: str, time_filter: str):
    """비디오 로그 조회"""
    # 기본 쿼리
    query = """
        SELECT
            vl.id,
            vl.video_id,
            v.title as video_title,
            vl.level,
            vl.event_type,
            vl.message,
            vl.details,
            vl.user_agent,
            vl.ip_address,
            vl.timestamp,
            vl.url
        FROM video_logs vl
        LEFT JOIN videos v ON vl.video_id = v.id
        WHERE 1=1
    """
    params = []

    # 레벨 필터
    if level_filter != "전체":
        query += " AND vl.level = ?"
        params.append(level_filter)

    # 비디오 필터
    if video_filter != "전체":
        video_id = int(video_filter.split(" - ")[0])
        query += " AND vl.video_id = ?"
        params.append(video_id)

    # 시간 범위 필터
    if time_filter != "전체":
        time_map = {
            "최근 1시간": 1,
            "최근 24시간": 24,
            "최근 7일": 24 * 7,
            "최근 30일": 24 * 30
        }
        hours_ago = time_map.get(time_filter, 24)
        cutoff_time = (datetime.now() - timedelta(hours=hours_ago)).isoformat()
        query += " AND vl.timestamp >= ?"
        params.append(cutoff_time)

    query += " ORDER BY vl.timestamp DESC LIMIT 1000"

    # DatabaseManager 사용
    with db_manager.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params) if params else ())
        rows = cur.fetchall()

    logs = []
    for row in rows:
        log = dict(row)
        # JSON 파싱
        if log['details']:
            try:
                log['details'] = json.loads(log['details'])
            except:
                pass
        logs.append(log)

    return logs


def display_log_statistics(logs: list):
    """로그 통계 표시"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_logs = len(logs)
        st.metric("총 로그", f"{total_logs:,}건")

    with col2:
        error_count = len([l for l in logs if l['level'] == 'error'])
        st.metric("에러", f"{error_count}건", delta=None if error_count == 0 else f"+{error_count}")

    with col3:
        warn_count = len([l for l in logs if l['level'] == 'warn'])
        st.metric("경고", f"{warn_count}건")

    with col4:
        unique_ips = len(set([l['ip_address'] for l in logs if l['ip_address']]))
        st.metric("고유 IP", f"{unique_ips}개")

    # 이벤트 타입별 통계
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**이벤트 타입별 분포**")
        event_counts = {}
        for log in logs:
            event_type = log['event_type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        event_df = pd.DataFrame([
            {"이벤트": k, "건수": v}
            for k, v in sorted(event_counts.items(), key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(event_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**비디오별 에러 건수**")
        video_errors = {}
        for log in logs:
            if log['level'] == 'error':
                video_title = log['video_title'] or f"Video {log['video_id']}"
                video_errors[video_title] = video_errors.get(video_title, 0) + 1

        if video_errors:
            error_df = pd.DataFrame([
                {"비디오": k, "에러 건수": v}
                for k, v in sorted(video_errors.items(), key=lambda x: x[1], reverse=True)
            ])
            st.dataframe(error_df, use_container_width=True, hide_index=True)
        else:
            st.info("에러가 없습니다.")


def display_error_logs(error_logs: list):
    """에러 로그 상세 표시"""
    for log in error_logs[:10]:  # 최근 10개만
        with st.expander(f"🔴 {log['timestamp']} - {log['video_title']} - {log['message']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**비디오 ID**: {log['video_id']}")
                st.markdown(f"**이벤트**: {log['event_type']}")
                st.markdown(f"**IP 주소**: {log['ip_address'] or 'N/A'}")

            with col2:
                st.markdown(f"**타임스탬프**: {log['timestamp']}")
                st.markdown(f"**User Agent**: {log['user_agent'][:50] if log['user_agent'] else 'N/A'}...")

            # 에러 상세 정보
            if log['details']:
                st.markdown("**에러 상세:**")
                st.json(log['details'])


def display_logs_table(logs: list):
    """로그 테이블 표시"""
    # 페이징
    logs_per_page = 50
    total_pages = (len(logs) - 1) // logs_per_page + 1

    if 'log_page' not in st.session_state:
        st.session_state['log_page'] = 1

    # 페이지 네비게이션
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.session_state['log_page'] > 1:
            if st.button("◀ 이전"):
                st.session_state['log_page'] -= 1
                st.rerun()

    with col2:
        st.markdown(f"<h4 style='text-align: center;'>{st.session_state['log_page']} / {total_pages}</h4>",
                   unsafe_allow_html=True)

    with col3:
        if st.session_state['log_page'] < total_pages:
            if st.button("다음 ▶"):
                st.session_state['log_page'] += 1
                st.rerun()

    # 현재 페이지 로그
    start_idx = (st.session_state['log_page'] - 1) * logs_per_page
    end_idx = start_idx + logs_per_page
    current_logs = logs[start_idx:end_idx]

    # 테이블 데이터 준비
    table_data = []
    for log in current_logs:
        # 레벨 이모지
        level_emoji = {
            'info': 'ℹ️',
            'warn': '⚠️',
            'error': '🔴'
        }.get(log['level'], '')

        table_data.append({
            "레벨": f"{level_emoji} {log['level']}",
            "시간": log['timestamp'][11:19] if len(log['timestamp']) > 19 else log['timestamp'],
            "비디오": log['video_title'][:20] if log['video_title'] else f"ID {log['video_id']}",
            "이벤트": log['event_type'],
            "메시지": log['message'][:40] + "..." if len(log['message']) > 40 else log['message'],
            "IP": log['ip_address'][:15] if log['ip_address'] else 'N/A'
        })

    # 테이블 표시
    df = pd.DataFrame(table_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
