"""달력 컴포넌트"""
import streamlit as st
import calendar
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from services.match_service import match_service
from streamlit_calendar import calendar as st_calendar

class CalendarComponent:
    """달력 컴포넌트"""

    def __init__(self):
        self.match_service = match_service

    def render(self) -> None:
        """streamlit_calendar를 사용한 달력 렌더링"""
        # 현재 달의 경기 데이터 가져오기
        today = datetime.now()
        year = st.session_state.get('calendar_year', today.year)
        month = st.session_state.get('calendar_month', today.month)

        # 경기 데이터를 가져와서 달력 이벤트로 변환
        matches = self.match_service.get_monthly_matches(year, month)
        calendar_events = self._create_calendar_events(matches)

        # streamlit_calendar 설정
        calendar_options = {
            "editable": "false",
            "navLinks": "true",
            "resources": [],
            "selectable": "true"
        }

        # 달력 표시 및 클릭 이벤트 처리
        calendar_result = st_calendar(
            events=calendar_events,
            options=calendar_options,
            custom_css="""
            .fc-event-past {
                opacity: 0.8;
            }
            .fc-event-time {
                font-weight: bold;
            }
            .fc-daygrid-event {
                font-size: 12px;
                padding: 1px 2px;
            }
            """,
            key="futsal_calendar"
        )

        # 달력 이벤트 클릭 처리
        if calendar_result.get("eventClick"):
            event_info = calendar_result["eventClick"]["event"]
            # 출석 관리 페이지로 이동
            st.session_state['current_page'] = "attendance"
            st.success(f"📋 {event_info.get('title', '경기')} - 출석 관리로 이동합니다!")
            st.rerun()

        # 이번 달 경기 요약 정보
        self._render_match_summary(matches)

    def _create_calendar_events(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """경기 데이터를 달력 이벤트로 변환"""
        events = []

        for match in matches:
            # 경기 날짜와 시간 파싱
            match_date = match['match_date']  # '2024-01-15' 형식
            match_time = match.get('match_time', '10:00')  # '14:00' 형식

            # datetime 객체 생성
            try:
                match_datetime = datetime.strptime(f"{match_date} {match_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                # 시간 파싱 실패시 기본 시간으로 설정
                match_datetime = datetime.strptime(f"{match_date} 10:00", "%Y-%m-%d %H:%M")

            # 경기 종료 시간 (2시간 후)
            end_datetime = match_datetime + timedelta(hours=2)

            # 상대팀 정보
            opponent = match.get('opponent', '팀내 경기')
            field_name = match.get('field_name', '미정')

            # 경기 타입에 따른 색상 설정
            if '팀내' in opponent:
                color = '#4CAF50'  # 녹색 - 팀내 경기
            else:
                color = '#ff5722'  # 주황색 - 대외 경기

            # 달력 이벤트 생성
            event = {
                "title": f"🏟️ vs {opponent}",
                "start": match_datetime.isoformat(),
                "end": end_datetime.isoformat(),
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "white",
                "extendedProps": {
                    "match_id": match['id'],
                    "opponent": opponent,
                    "field_name": field_name,
                    "match_time": match_time,
                    "description": f"장소: {field_name}\n시간: {match_time}\n상대: {opponent}"
                }
            }

            events.append(event)

        return events


    def _render_match_summary(self, matches: List[Dict[str, Any]]) -> None:
        """월별 경기 요약"""
        if not matches:
            st.info("이번 달 예정된 경기가 없습니다.")
            return

        st.markdown("---")
        st.markdown(f"### 📋 이번 달 경기 목록 ({len(matches)}경기)")
        st.markdown("*달력의 경기를 클릭하거나 아래 버튼을 클릭하여 출석 관리로 이동하세요*")

        # 간단한 경기 목록 (카드 형태)
        for match in matches:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    opponent = match.get('opponent', '팀내 경기')
                    field_name = match.get('field_name', '미정')

                    # 경기 타입에 따른 아이콘
                    icon = "🏠" if "팀내" in opponent else "🆚"

                    st.markdown(f"""
                    **{icon} {match['match_date']} {match['match_time']}**
                    🏟️ **장소**: {field_name}
                    👥 **상대**: {opponent}
                    """)

                with col2:
                    if st.button(
                        "📋 출석관리",
                        key=f"summary_btn_{match['id']}",
                        help=f"{opponent} 경기 출석 관리",
                        width="stretch"
                    ):
                        st.session_state['current_page'] = "attendance"
                        st.success(f"📋 {opponent} 경기 출석 관리로 이동!")
                        st.rerun()

                st.divider()

# 컴포넌트 인스턴스
calendar_component = CalendarComponent()