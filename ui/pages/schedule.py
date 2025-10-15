"""일정 관리 페이지"""
import streamlit as st
from datetime import datetime, date
from ui.components.calendar import calendar_component
from services.match_service import match_service
from services.field_service import field_service
from utils.auth_utils import require_admin_access

class SchedulePage:
    """일정 관리 페이지"""

    def __init__(self):
        self.match_service = match_service
        self.field_service = field_service

    def render(self) -> None:
        """일정 관리 페이지 렌더링"""
        require_admin_access()
        st.header("📅 일정 관리")

        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["📅 달력", "➕ 경기 추가", "🏟️ 구장 관리", "📋 경기 목록"])

        with tab1:
            self._render_calendar_view()

        with tab2:
            self._render_add_match()

        with tab3:
            self._render_field_management()

        with tab4:
            self._render_match_list()

    def _render_calendar_view(self) -> None:
        """달력 뷰 렌더링"""
        st.subheader("📅 경기 일정 달력")
        calendar_component.render()

    def _render_add_match(self) -> None:
        """경기 추가 폼"""
        st.subheader("⚽ 새 경기 추가")

        # 구장 목록 가져오기
        fields = self.field_service.get_all_fields()

        if not fields:
            st.warning("먼저 구장을 등록해주세요.")
            if st.button("기본 구장 자동 생성"):
                self.field_service.create_field("테스트 구장", "테스트 주소", 100000)
                st.rerun()
            return

        with st.form("add_match_form"):
            col1, col2 = st.columns(2)

            with col1:
                # 구장 선택
                field_options = {f"{f['name']} - {f['address']}": f['id'] for f in fields}
                selected_field = st.selectbox("구장 선택", options=list(field_options.keys()))

                match_date = st.date_input(
                    "경기 날짜",
                    value=datetime.now().date(),
                    min_value=datetime.now().date()
                )

            with col2:
                # 시간 선택
                time_options = self.match_service.get_time_options()
                selected_time = st.selectbox(
                    "경기 시간",
                    options=[time[0] for time in time_options],
                    format_func=lambda x: next(time[1] for time in time_options if time[0] == x)
                )

                opponent = st.text_input("상대팀 (선택사항)", placeholder="팀내 경기")

            # 추가 정보
            st.markdown("**추가 정보**")
            col3, col4 = st.columns(2)

            with col3:
                result = st.text_input("경기 결과 (선택사항)", placeholder="경기 후 입력")

            with col4:
                # 출석 마감 시간 선택
                lock_options = {
                    "제한 없음": 0,
                    "경기 30분 전": 30,
                    "경기 60분 전": 60,
                    "경기 90분 전": 90
                }
                selected_lock = st.selectbox("출석 마감", options=list(lock_options.keys()))
                attendance_lock_minutes = lock_options[selected_lock]

            if st.form_submit_button("경기 추가", type="primary"):
                if selected_field and match_date and selected_time:
                    try:
                        field_id = field_options[selected_field]

                        # 중복 경기 확인
                        if self.match_service.validate_match_time_conflict(field_id, match_date, selected_time):
                            st.error("해당 시간에 이미 다른 경기가 예정되어 있습니다.")
                        else:
                            success = self.match_service.create_match(
                                field_id=field_id,
                                match_date=match_date,
                                match_time=selected_time,
                                opponent=opponent or "",
                                attendance_lock_minutes=attendance_lock_minutes
                            )

                            if success:
                                st.success("경기가 성공적으로 추가되었습니다!")
                                st.rerun()
                            else:
                                st.error("경기 추가에 실패했습니다.")

                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
                else:
                    st.error("필수 항목을 모두 입력해주세요.")

    def _render_field_management(self) -> None:
        """구장 관리"""
        st.subheader("🏟️ 구장 관리")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**새 구장 추가**")
            with st.form("add_field_form"):
                name = st.text_input("구장명")
                address = st.text_input("주소")
                cost = st.number_input("대관료", min_value=0, step=10000)

                if st.form_submit_button("구장 추가"):
                    if name:
                        try:
                            success = self.field_service.create_field(name, address, cost)
                            if success:
                                st.success("구장이 추가되었습니다!")
                                st.rerun()
                            else:
                                st.error("구장 추가에 실패했습니다.")
                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {e}")
                    else:
                        st.error("구장명을 입력해주세요.")

        with col2:
            st.markdown("**등록된 구장 목록**")
            fields = self.field_service.get_all_fields()

            if fields:
                for field in fields:
                    with st.expander(f"🏟️ {field['name']}"):
                        st.write(f"**주소**: {field['address'] or '미입력'}")
                        st.write(f"**대관료**: {field['cost_display']}")
                        st.write(f"**등록일**: {field['created_at'][:10] if field['created_at'] else '미상'}")

                        # 통계 정보
                        field_matches = len([m for m in self.match_service.get_all_matches()
                                           if m['field_id'] == field['id']])
                        st.write(f"**진행된 경기**: {field_matches}회")
            else:
                st.info("등록된 구장이 없습니다.")

    def _render_match_list(self) -> None:
        """경기 목록"""
        st.subheader("📋 전체 경기 목록")

        matches = self.match_service.get_all_matches()

        if not matches:
            st.info("등록된 경기가 없습니다.")
            return

        # 필터 옵션
        col1, col2, col3 = st.columns(3)

        with col1:
            # 월별 필터
            today = datetime.now()
            filter_year = st.selectbox("연도", [today.year - 1, today.year, today.year + 1], index=1)

        with col2:
            filter_month = st.selectbox("월", list(range(1, 13)), index=today.month - 1)

        with col3:
            # 구장별 필터
            fields = self.field_service.get_all_fields()
            field_names = ["전체"] + [f['name'] for f in fields]
            filter_field = st.selectbox("구장", field_names)

        # 필터 적용
        filtered_matches = matches

        if filter_field != "전체":
            filtered_matches = [m for m in filtered_matches if m.get('field_name') == filter_field]

        # 선택된 월의 경기만 필터링
        monthly_matches = self.match_service.get_monthly_matches(filter_year, filter_month)

        # 경기 목록 표시
        if monthly_matches:
            st.write(f"**{filter_year}년 {filter_month}월 경기 ({len(monthly_matches)}건)**")

            for i, match in enumerate(monthly_matches, 1):
                with st.expander(
                    f"{i}. {match['match_date']} {match['match_time']} - "
                    f"{match.get('opponent', '팀내 경기')} @ {match.get('field_name', '미정')}"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**날짜**: {match['match_date']}")
                        st.write(f"**시간**: {match['match_time']}")
                        st.write(f"**구장**: {match.get('field_name', '미정')}")

                    with col2:
                        st.write(f"**상대팀**: {match.get('opponent', '팀내 경기')}")
                        st.write(f"**결과**: {match.get('result', '경기 전')}")
                        st.write(f"**등록일**: {match.get('created_at', '미상')[:10]}")

                    # 경기 관리 버튼들
                    col_btn1, col_btn2, col_btn3 = st.columns(3)

                    with col_btn1:
                        if st.button(f"📋 출석 관리", key=f"attendance_{match['id']}"):
                            st.session_state['selected_match_id'] = match['id']
                            st.session_state['current_page'] = "출석 관리"
                            st.rerun()

                    with col_btn2:
                        if st.button(f"✏️ 수정", key=f"edit_{match['id']}", type="primary"):
                            st.session_state[f'editing_match_{match["id"]}'] = True
                            st.rerun()

                    with col_btn3:
                        if st.button(f"🗑️ 삭제", key=f"delete_{match['id']}", type="secondary"):
                            if st.session_state.get(f"confirm_delete_{match['id']}", False):
                                try:
                                    success = self.match_service.delete_match(match['id'])
                                    if success:
                                        st.success("경기가 삭제되었습니다!")
                                        # 확인 상태 초기화
                                        if f"confirm_delete_{match['id']}" in st.session_state:
                                            del st.session_state[f"confirm_delete_{match['id']}"]
                                        st.rerun()
                                    else:
                                        st.error("경기 삭제에 실패했습니다.")
                                except Exception as e:
                                    st.error(f"삭제 중 오류가 발생했습니다: {e}")
                            else:
                                st.session_state[f"confirm_delete_{match['id']}"] = True
                                st.warning("정말로 이 경기를 삭제하시겠습니까? 다시 삭제 버튼을 눌러주세요.")
                                st.rerun()

                    # 수정 모드일 때 수정 폼 표시
                    if st.session_state.get(f'editing_match_{match["id"]}', False):
                        self._render_edit_match_form(match)
        else:
            st.info(f"{filter_year}년 {filter_month}월에 예정된 경기가 없습니다.")

    def _render_match_statistics(self) -> None:
        """경기 통계 (추가 기능)"""
        st.subheader("📊 경기 통계")

        matches = self.match_service.get_all_matches()

        if not matches:
            st.info("통계를 위한 경기 데이터가 없습니다.")
            return

        col1, col2, col3 = st.columns(3)

        with col1:
            total_matches = len(matches)
            completed_matches = len([m for m in matches if m.get('result')])
            st.metric("총 경기 수", total_matches)
            st.metric("완료된 경기", completed_matches)

        with col2:
            # 이번 달 경기 수
            this_month_count = self.match_service.get_monthly_count()
            st.metric("이번 달 경기", f"{this_month_count}경기")

            # 다음 경기
            next_match = self.match_service.get_next_match()
            if next_match:
                st.metric("다음 경기", f"{next_match['match_date']}")
            else:
                st.metric("다음 경기", "예정 없음")

        with col3:
            # 구장별 통계
            field_usage = {}
            for match in matches:
                field_name = match.get('field_name', '미정')
                field_usage[field_name] = field_usage.get(field_name, 0) + 1

            if field_usage:
                most_used_field = max(field_usage.items(), key=lambda x: x[1])
                st.metric("주요 구장", most_used_field[0])
                st.metric("사용 횟수", f"{most_used_field[1]}회")

    def _render_edit_match_form(self, match: dict) -> None:
        """경기 수정 폼"""
        st.markdown("---")
        st.markdown("### ✏️ 경기 정보 수정")

        # 구장 목록 가져오기
        fields = self.field_service.get_all_fields()

        with st.form(f"edit_match_form_{match['id']}"):
            col1, col2 = st.columns(2)

            with col1:
                # 구장 선택
                field_options = {f"{f['name']} - {f['address']}": f['id'] for f in fields}
                current_field_display = f"{match.get('field_name', '미정')} - {match.get('field_address', '')}"

                # 현재 구장이 선택 목록에 있는지 확인
                if current_field_display in field_options:
                    current_field_index = list(field_options.keys()).index(current_field_display)
                else:
                    current_field_index = 0

                selected_field = st.selectbox(
                    "구장 선택",
                    options=list(field_options.keys()),
                    index=current_field_index,
                    key=f"edit_field_{match['id']}"
                )

                # 날짜 선택 (현재 날짜로 초기화)
                current_date = datetime.strptime(match['match_date'], "%Y-%m-%d").date()
                match_date = st.date_input(
                    "경기 날짜",
                    value=current_date,
                    key=f"edit_date_{match['id']}"
                )

            with col2:
                # 시간 선택
                time_options = self.match_service.get_time_options()
                current_time_index = 0
                for i, (time_val, _) in enumerate(time_options):
                    if time_val == match['match_time']:
                        current_time_index = i
                        break

                selected_time = st.selectbox(
                    "경기 시간",
                    options=[time[0] for time in time_options],
                    format_func=lambda x: next(time[1] for time in time_options if time[0] == x),
                    index=current_time_index,
                    key=f"edit_time_{match['id']}"
                )

                # 상대팀
                opponent = st.text_input(
                    "상대팀",
                    value=match.get('opponent', ''),
                    placeholder="팀내 경기",
                    key=f"edit_opponent_{match['id']}"
                )

            # 출석 마감 시간 선택
            st.markdown("**출석 설정**")
            lock_options = {
                "제한 없음": 0,
                "경기 30분 전": 30,
                "경기 60분 전": 60,
                "경기 90분 전": 90
            }
            current_lock_minutes = match.get('attendance_lock_minutes', 0)
            current_lock_label = next((k for k, v in lock_options.items() if v == current_lock_minutes), "제한 없음")
            current_lock_index = list(lock_options.keys()).index(current_lock_label)

            selected_lock = st.selectbox(
                "출석 마감",
                options=list(lock_options.keys()),
                index=current_lock_index,
                key=f"edit_lock_{match['id']}"
            )
            attendance_lock_minutes = lock_options[selected_lock]

            # 경기 결과
            st.markdown("**경기 결과**")
            col_result1, col_result2 = st.columns(2)

            with col_result1:
                result = st.text_area(
                    "경기 결과",
                    value=match.get('result', ''),
                    placeholder="예: 승 3-1, 패 1-2, 무 2-2 등",
                    height=100,
                    key=f"edit_result_{match['id']}"
                )

            with col_result2:
                st.markdown("**결과 입력 가이드**")
                st.markdown("""
                - 승: 승 3-1
                - 패: 패 1-2
                - 무: 무 2-2
                - 팀내경기: 팀내 A조 승
                - 기타: 자유 형식
                """)

            # 폼 제출 버튼들
            col_submit1, col_submit2 = st.columns(2)

            with col_submit1:
                if st.form_submit_button("💾 저장", type="primary"):
                    try:
                        field_id = field_options[selected_field]

                        # 시간 충돌 검사 (현재 경기 제외)
                        if (field_id != match['field_id'] or
                            str(match_date) != match['match_date'] or
                            selected_time != match['match_time']):

                            if self.match_service.validate_match_time_conflict(
                                field_id, match_date, selected_time, exclude_match_id=match['id']
                            ):
                                st.error("해당 시간에 이미 다른 경기가 예정되어 있습니다.")
                                return

                        # 경기 정보 업데이트
                        success = self.match_service.update_match(
                            match_id=match['id'],
                            field_id=field_id,
                            match_date=match_date,
                            match_time=selected_time,
                            opponent=opponent or "",
                            result=result or "",
                            attendance_lock_minutes=attendance_lock_minutes
                        )

                        if success:
                            st.success("경기 정보가 성공적으로 수정되었습니다!")
                            # 수정 모드 종료
                            del st.session_state[f'editing_match_{match["id"]}']
                            st.rerun()
                        else:
                            st.error("경기 수정에 실패했습니다.")

                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")

            with col_submit2:
                if st.form_submit_button("❌ 취소"):
                    # 수정 모드 종료
                    del st.session_state[f'editing_match_{match["id"]}']
                    st.rerun()

# 페이지 인스턴스
schedule_page = SchedulePage()