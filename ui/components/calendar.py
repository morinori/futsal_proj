"""달력 컴포넌트 - 모바일 최적화"""
import streamlit as st
import calendar
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from services.match_service import match_service
from streamlit_calendar import calendar as st_calendar

class CalendarComponent:
    """모바일 최적화 달력 컴포넌트"""

    def __init__(self):
        self.match_service = match_service
        self._initialize_calendar_state()

    def _initialize_calendar_state(self):
        """캘린더 상태 초기화"""
        if 'calendar_view' not in st.session_state:
            st.session_state.calendar_view = 'dayGridMonth'
        if 'calendar_date' not in st.session_state:
            st.session_state.calendar_date = datetime.now().isoformat()[:10]
        if 'mobile_detected' not in st.session_state:
            st.session_state.mobile_detected = False
        if 'last_event_click' not in st.session_state:
            st.session_state.last_event_click = None


    def _get_mobile_optimized_css(self) -> str:
        """모바일 최적화 CSS"""
        return """
        <style>
        /* 기본 캘린더 스타일 */
        .fc-event {
            min-height: 28px !important;
            font-size: 11px !important;
            padding: 3px 5px !important;
            cursor: pointer;
            border-radius: 4px !important;
            line-height: 1.2 !important;
            transition: all 0.2s ease;
        }

        .fc-button {
            min-height: 38px !important;
            font-size: 13px !important;
            padding: 4px 8px !important;
            border-radius: 6px !important;
        }

        .fc-toolbar-title {
            font-size: 18px !important;
            font-weight: 600 !important;
            color: #333 !important;
        }

        .fc-daygrid-day {
            min-height: 65px !important;
        }

        .fc-col-header-cell {
            padding: 8px 4px !important;
            font-weight: 600;
            background-color: #f8f9fa !important;
        }

        .fc-scrollgrid {
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px !important;
        }

        /* 모바일 전용 스타일 */
        @media (max-width: 768px) {
            .fc-event {
                min-height: 32px !important;
                font-size: 10px !important;
                padding: 2px 4px !important;
                margin: 1px 0 !important;
                touch-action: manipulation;
            }

            .fc-toolbar {
                flex-direction: column !important;
                gap: 8px !important;
                margin-bottom: 15px !important;
            }

            .fc-toolbar-chunk {
                display: flex;
                justify-content: center;
                align-items: center;
            }

            .fc-button-group {
                gap: 8px !important;
            }

            .fc-button {
                min-height: 42px !important;
                min-width: 42px !important;
                font-size: 14px !important;
                padding: 8px 12px !important;
            }

            .fc-toolbar-title {
                font-size: 20px !important;
                margin: 0 10px !important;
            }

            .fc-daygrid-day {
                min-height: 70px !important;
            }

            .fc-daygrid-day-number {
                font-size: 14px !important;
                padding: 4px !important;
            }

            /* 터치 영역 최적화 */
            .fc-event:active {
                transform: scale(0.98);
                opacity: 0.8;
            }

            /* 모바일 스크롤 최적화 */
            .fc {
                touch-action: pan-y !important;
                -webkit-overflow-scrolling: touch !important;
            }
        }

        /* 데스크톱 전용 스타일 */
        @media (min-width: 769px) {
            .fc-event:hover {
                opacity: 0.9;
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        }
        </style>
        """

    def _get_adaptive_calendar_options(self, is_mobile: bool = False) -> Dict[str, Any]:
        """모바일/데스크톱 적응형 캘린더 옵션 - 월 뷰 전용"""
        base_options = {
            "initialView": "dayGridMonth",  # 월 뷰로 고정
            "initialDate": st.session_state.get('calendar_date', datetime.now().isoformat()[:10]),
            "editable": False,
            "selectable": False,
            "selectMirror": False,
            "eventStartEditable": False,
            "eventDurationEditable": False,
            "droppable": False,
            "height": "auto",
            "dayMaxEvents": 3 if is_mobile else 4,
        }

        if is_mobile:
            # 모바일: month 버튼 추가
            base_options.update({
                "headerToolbar": {
                    "left": "prev,next",
                    "center": "title",
                    "right": "today,dayGridMonth"
                },
                "aspectRatio": 1.0,
                "fixedWeekCount": False,
                "dayMaxEvents": 2,
            })
        else:
            # 데스크톱: 월 뷰와 month 버튼 추가
            base_options.update({
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth"  # month 버튼 추가
                },
                "aspectRatio": 1.35,
                "navLinks": True,
            })

        return base_options

    def _detect_mobile(self) -> bool:
        """CSS 미디어 쿼리 기반 모바일 감지"""
        # Streamlit의 내장 viewport 정보를 활용한 간접적 감지
        # 일반적으로 모바일은 768px 이하로 간주
        # 실제로는 CSS 미디어쿼리가 자동으로 처리하므로 기본값 반환
        return st.session_state.get('mobile_detected', False)

    def render(self) -> None:
        """모바일 최적화된 달력 렌더링"""

        # 모바일 감지는 CSS 미디어 쿼리로 자동 처리 (iframe 없음)

        # 현재 달의 경기 데이터 가져오기
        today = datetime.now()
        year = st.session_state.get('calendar_year', today.year)
        month = st.session_state.get('calendar_month', today.month)

        # 경기 데이터를 가져와서 달력 이벤트로 변환
        matches = self.match_service.get_monthly_matches(year, month)
        calendar_events = self._create_mobile_optimized_events(matches, is_mobile=False)

        # 반응형 캘린더 옵션 (CSS로 처리)
        calendar_options = self._get_adaptive_calendar_options(is_mobile=False)

        # 모바일 최적화 CSS
        mobile_css = self._get_mobile_optimized_css()

        # 달력 표시 및 클릭 이벤트 처리 (반응형)
        calendar_result = st_calendar(
            events=calendar_events,
            options=calendar_options,
            custom_css=mobile_css,
            key="futsal_calendar_responsive"
        )

        # 이벤트 처리
        self._handle_calendar_events(calendar_result, is_mobile=False)

        # 이번 달 경기 요약 정보
        self._render_match_summary(matches, is_mobile=False)

    def _create_mobile_optimized_events(self, matches: List[Dict[str, Any]], is_mobile: bool = False) -> List[Dict[str, Any]]:
        """모바일 최적화된 캘린더 이벤트 생성"""
        events = []

        for match in matches:
            # 경기 날짜와 시간 파싱
            match_date = match['match_date']
            match_time = match.get('match_time', '10:00')

            # datetime 객체 생성
            try:
                match_datetime = datetime.strptime(f"{match_date} {match_time}", "%Y-%m-%d %H:%M")
            except ValueError:
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

            # 모바일용 간소화된 제목
            if is_mobile:
                title = f"{match_time} vs {opponent[:8]}{'...' if len(opponent) > 8 else ''}"
            else:
                title = f"🏟️ vs {opponent}"

            # 달력 이벤트 생성
            event = {
                "title": title,
                "start": match_datetime.isoformat(),
                "end": end_datetime.isoformat(),
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "white",
                "classNames": ["mobile-optimized-event"] if is_mobile else [],
                "display": "block",
                "extendedProps": {
                    "match_id": match['id'],
                    "opponent": opponent,
                    "field_name": field_name,
                    "match_time": match_time,
                    "description": f"장소: {field_name}\n시간: {match_time}\n상대: {opponent}",
                    "touch_action": "attendance_redirect"
                }
            }

            events.append(event)

        return events

    def _handle_calendar_events(self, calendar_result: Dict[str, Any], is_mobile: bool = False) -> None:
        """모바일 최적화된 이벤트 처리"""

        # 이벤트 클릭 처리 (뷰 변경 방지)
        if calendar_result.get("eventClick"):
            event_info = calendar_result["eventClick"]["event"]

            # 중복 클릭 방지
            current_click = f"{event_info.get('id', 'unknown')}_{int(datetime.now().timestamp())}"
            last_click = st.session_state.get('last_event_click', '')

            if current_click != last_click:
                st.session_state['last_event_click'] = current_click
                st.session_state['current_page'] = "attendance"

                # 피드백 메시지
                st.success(f"📋 {event_info.get('title', '경기')} - 출석 관리로 이동합니다!")

                st.rerun()

        # 날짜 변경은 데스크톱에서만 허용 (모바일에서는 차단)
        if calendar_result.get("dateClick") and not is_mobile:
            clicked_date = calendar_result["dateClick"]["date"]
            if clicked_date:
                st.session_state['calendar_date'] = clicked_date[:10]  # YYYY-MM-DD 형식만 저장
                st.rerun()

        # 뷰 변경 이벤트 처리 (month 버튼 클릭 시)
        if calendar_result.get("viewChange"):
            new_view = calendar_result["viewChange"].get("view", {}).get("type")
            if new_view and new_view != st.session_state.get('calendar_view'):
                st.session_state['calendar_view'] = new_view
                st.rerun()

    def _render_match_summary(self, matches: List[Dict[str, Any]], is_mobile: bool = False) -> None:
        """모바일 최적화된 월별 경기 요약"""
        if not matches:
            st.info("이번 달 예정된 경기가 없습니다.")
            return

        st.markdown("---")
        st.markdown(f"### 📋 이번 달 경기 목록 ({len(matches)}경기)")
        st.markdown("*달력의 경기를 클릭하거나 아래 버튼을 클릭하여 출석 관리로 이동하세요*")

        # 반응형 레이아웃 (CSS로 처리)
        for match in matches:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    opponent = match.get('opponent', '팀내 경기')
                    field_name = match.get('field_name', '미정')
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