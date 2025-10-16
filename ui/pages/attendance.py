"""출석 관리 페이지"""
import streamlit as st
from services.attendance_service import attendance_service
from services.match_service import match_service
from services.player_service import player_service
from services.team_builder_service import team_builder_service

class AttendancePage:
    """출석 관리 페이지"""

    def __init__(self):
        self.attendance_service = attendance_service
        self.match_service = match_service
        self.player_service = player_service

    def render(self) -> None:
        """출석 관리 페이지 렌더링"""
        st.header("📋 출석 관리")

        # 출석 관리 탭들
        tab1, tab2, tab3 = st.tabs(["👤 개인별 출석", "📅 경기별 출석", "🏆 팀 구성"])

        with tab1:
            self._render_personal_attendance_tab()

        with tab2:
            self._render_match_attendance_tab()

        with tab3:
            self._render_team_composition_tab()

    def _render_specific_match_attendance(self, match_id: int) -> None:
        """특정 경기의 출석 현황 표시 (달력에서 클릭한 경우)"""
        # 경기 정보 표시
        match_info = self._get_match_by_id(match_id)
        if match_info:
            st.markdown(f"### 🏟️ {match_info['match_date']} {match_info['match_time']} - {match_info.get('field_name', '미정')}")

        # 출석 데이터 확인 및 생성 (무한 루프 완전 방지)
        attendance_list = []
        try:
            attendance_list = self.attendance_service.get_match_attendance(match_id)
        except Exception as e:
            st.error(f"출석 데이터 조회 중 오류: {e}")
            return

        # 출석 데이터가 없을 때만 생성 시도
        if not attendance_list:
            # 활성 선수 수 확인
            active_players = self.player_service.get_all_players()
            if not active_players:
                st.warning("활성화된 선수가 없습니다. 먼저 선수를 등록해주세요.")
                return

            # 중복 생성 방지를 위한 안전한 플래그 관리
            creation_key = f"attendance_created_{match_id}"
            processing_key = f"attendance_processing_{match_id}"

            # 현재 처리 중인지 확인
            if st.session_state.get(processing_key, False):
                st.warning("출석 데이터를 생성 중입니다. 잠시만 기다려주세요...")
                return

            if not st.session_state.get(creation_key, False):
                # 처리 중 플래그 설정
                st.session_state[processing_key] = True

                with st.spinner("출석 데이터를 생성하고 있습니다..."):
                    try:
                        # 생성 전 한 번 더 체크 (다른 요청이 이미 생성했을 수 있음)
                        recheck_list = self.attendance_service.get_match_attendance(match_id)
                        if recheck_list:
                            attendance_list = recheck_list
                            st.success("출석 데이터가 이미 준비되어 있습니다!")
                        else:
                            success = self.attendance_service.create_attendance_for_match(match_id)

                            if success:
                                # 생성 후 다시 조회
                                attendance_list = self.attendance_service.get_match_attendance(match_id)
                                if attendance_list:
                                    st.success(f"{len(attendance_list)}명의 출석 데이터가 생성되었습니다!")
                                else:
                                    st.error("출석 데이터 생성 후 조회에 실패했습니다.")
                                    return
                            else:
                                st.error("출석 데이터 생성에 실패했습니다.")
                                return

                        st.session_state[creation_key] = True

                    except Exception as e:
                        st.error(f"출석 데이터 생성 중 오류: {e}")
                        return
                    finally:
                        # 처리 완료, 플래그 해제
                        if processing_key in st.session_state:
                            del st.session_state[processing_key]
            else:
                st.warning("출석 데이터 생성에 실패했습니다. '출석 데이터 새로고침' 버튼을 클릭해보세요.")
                return

        # 출석 요약
        summary = self.attendance_service.get_attendance_summary(match_id)

        # 2x2 그리드로 변경 (모바일 대응)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 인원", summary['total_players'])
        with col2:
            st.metric("✅ 참석", summary['present_count'])

        col3, col4 = st.columns(2)
        with col3:
            st.metric("❌ 불참", summary['absent_count'])
        with col4:
            st.metric("❓ 미정", summary['pending_count'])

        # 전체 출석 현황 테이블
        attendance_list = self.attendance_service.get_match_attendance(match_id)

        if attendance_list:
            for att in attendance_list:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{att['player_name']}**")
                with col2:
                    st.write(att['status_display'])

        # 선택된 경기 세션 상태 초기화 버튼
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("다른 경기 보기", key="clear_selected_match"):
                if 'selected_match_id' in st.session_state:
                    del st.session_state['selected_match_id']
                if 'match_select_dropdown' in st.session_state:
                    del st.session_state['match_select_dropdown']
                personal_keys = [key for key in st.session_state.keys() if key.startswith('personal_match_select_')]
                for key in personal_keys:
                    del st.session_state[key]
                st.rerun()

        with col_btn2:
            if st.button("출석 데이터 새로고침", key="refresh_attendance_data"):
                # 모든 출석 관련 생성 플래그들 초기화
                keys_to_remove = [key for key in st.session_state.keys()
                                if key.startswith('attendance_') and 'created_' in key]
                keys_to_remove.extend([key for key in st.session_state.keys()
                                     if key.startswith('personal_attendance_created_')])
                keys_to_remove.extend([key for key in st.session_state.keys()
                                     if key.startswith('current_selected_player_')])
                for key in keys_to_remove:
                    del st.session_state[key]
                st.success("모든 출석 데이터 플래그가 초기화되었습니다.")
                st.rerun()

    def _render_match_attendance_tab(self) -> None:
        """경기별 출석 현황 탭"""
        upcoming_matches = self._get_upcoming_matches()
        match_options = [
            {
                'label': f"{match['match_date']} {match['match_time']} - {match.get('field_name', '미정')}",
                'id': match['id']
            }
            for match in upcoming_matches
        ]

        if not match_options:
            st.info("예정된 경기가 없습니다.")
            return

        # selectbox 기본값 설정
        dropdown_key = 'match_select_dropdown'
        current_index = st.session_state.get(dropdown_key)
        if not isinstance(current_index, int):
            current_index = None

        selected_match_id = st.session_state.get('selected_match_id')
        match_index_for_selected = None
        if selected_match_id is not None:
            for idx, option in enumerate(match_options):
                if option['id'] == selected_match_id:
                    match_index_for_selected = idx
                    break

        if match_index_for_selected is not None:
            st.session_state[dropdown_key] = match_index_for_selected
        elif current_index is None or current_index >= len(match_options):
            st.session_state[dropdown_key] = 0

        selected_index = st.selectbox(
            "경기 선택",
            options=list(range(len(match_options))),
            format_func=lambda idx: match_options[idx]['label'],
            key=dropdown_key
        )

        selected_match = match_options[selected_index]
        st.session_state['selected_match_id'] = selected_match['id']
        self._render_match_attendance_detail(selected_match['id'])


    def _render_personal_attendance_tab(self) -> None:
        """개인별 출석 관리 탭"""
        # "누구세요?" 드롭다운
        players = self.player_service.get_all_players()

        if not players:
            st.warning("등록된 선수가 없습니다.")
            return

        player_options = {player['name']: player['id'] for player in players}

        selected_player_name = st.selectbox(
            "👤 누구세요?",
            options=list(player_options.keys()),
            key="personal_attendance_player"
        )

        if selected_player_name:
            player_id = player_options[selected_player_name]

            # 선수가 변경될 때마다 해당 선수의 생성 플래그를 초기화 (한 번만)
            current_player_key = f"current_selected_player_{player_id}"
            if not st.session_state.get(current_player_key, False):
                # 다른 선수의 플래그들은 초기화하되, 현재 선수 것만 유지
                keys_to_remove = [key for key in st.session_state.keys()
                                if key.startswith('personal_attendance_created_') and not key.endswith(str(player_id))]
                for key in keys_to_remove:
                    del st.session_state[key]

                # 이전 선수 키들도 정리
                prev_keys = [key for key in st.session_state.keys() if key.startswith('current_selected_player_')]
                for key in prev_keys:
                    del st.session_state[key]

                st.session_state[current_player_key] = True

            self._render_personal_attendance_detail(player_id, selected_player_name)

    def _render_personal_attendance_detail(self, player_id: int, player_name: str) -> None:
        """개인 출석 상세 관리"""
        st.markdown(f"### {player_name}님의 출석 관리")

        # 예정된 경기 목록 조회
        upcoming_match_list = self._get_upcoming_matches()

        if not upcoming_match_list:
            st.info("예정된 경기가 없습니다.")
            return

        # 경기 선택 드롭다운
        st.subheader("📅 경기 선택")
        match_options = [
            {
                'label': f"{match['match_date']} {match['match_time']} - {match.get('opponent', '팀내 경기')} @ {match.get('field_name', '미정')}",
                'id': match['id']
            }
            for match in upcoming_match_list
        ]

        dropdown_key = f"personal_match_select_{player_id}"
        current_index = st.session_state.get(dropdown_key)
        if not isinstance(current_index, int):
            current_index = None

        selected_match_id = st.session_state.get('selected_match_id')
        match_index_for_selected = None
        if selected_match_id is not None:
            for idx, option in enumerate(match_options):
                if option['id'] == selected_match_id:
                    match_index_for_selected = idx
                    break

        if match_index_for_selected is not None:
            st.session_state[dropdown_key] = match_index_for_selected
        elif current_index is None or current_index >= len(match_options):
            st.session_state[dropdown_key] = 0

        selected_index = st.selectbox(
            "참석할 경기를 선택하세요:",
            options=list(range(len(match_options))),
            format_func=lambda idx: match_options[idx]['label'],
            key=dropdown_key
        )

        selected_match = match_options[selected_index]
        selected_match_id = selected_match['id']

        # 선택된 경기에 대한 출석 데이터 확인 및 생성
        self._render_personal_match_attendance(player_id, player_name, selected_match_id)

    def _render_personal_match_attendance(self, player_id: int, player_name: str, match_id: int) -> None:
        """개인의 특정 경기 출석 관리"""
        # 경기 정보 표시
        match_info = self._get_match_by_id(match_id)
        if match_info:
            st.markdown(f"#### 🏟️ {match_info['match_date']} {match_info['match_time']}")
            st.markdown(f"**장소**: {match_info.get('field_name', '미정')} | **상대**: {match_info.get('opponent', '팀내 경기')}")

        # 해당 경기의 출석 데이터가 있는지 확인
        attendance_list = self.attendance_service.get_match_attendance(match_id)
        player_attendance = None

        # 현재 선수의 출석 데이터 찾기
        for att in attendance_list:
            if att['player_id'] == player_id:
                player_attendance = att
                break

        # 출석 데이터가 없으면 생성
        if not player_attendance:
            personal_attendance_key = f"personal_attendance_created_{player_id}_{match_id}"

            if not st.session_state.get(personal_attendance_key, False):
                st.info("출석 데이터를 생성하고 있습니다...")

                with st.spinner("처리 중..."):
                    try:
                        success = self.attendance_service.create_attendance_for_match(match_id)
                        if success:
                            st.session_state[personal_attendance_key] = True
                            st.success("출석 데이터가 생성되었습니다!")
                            st.rerun()
                        else:
                            st.error("출석 데이터 생성에 실패했습니다.")
                            return
                    except Exception as e:
                        st.error(f"출석 데이터 생성 중 오류: {e}")
                        return
            else:
                # 다시 조회 시도
                attendance_list = self.attendance_service.get_match_attendance(match_id)
                for att in attendance_list:
                    if att['player_id'] == player_id:
                        player_attendance = att
                        break

                if not player_attendance:
                    st.error("출석 데이터 생성 후에도 조회되지 않습니다.")
                    if st.button("🔄 새로고침", key=f"refresh_personal_attendance_{player_id}_{match_id}"):
                        if personal_attendance_key in st.session_state:
                            del st.session_state[personal_attendance_key]
                        st.rerun()
                    return

        # 최종 출석 데이터 확인
        final_attendance_list = self.attendance_service.get_match_attendance(match_id)
        final_player_attendance = None
        for att in final_attendance_list:
            if att['player_id'] == player_id:
                final_player_attendance = att
                break

        # 디버깅 정보 표시 (필요시 주석 해제)
        # st.markdown("---")
        # st.markdown("### 🔍 디버깅 정보")
        # st.write(f"**선수 ID**: {player_id}")
        # st.write(f"**경기 ID**: {match_id}")
        # st.write(f"**출석 데이터 개수**: {len(final_attendance_list)}")
        #
        # if final_player_attendance:
        #     st.write(f"**찾은 출석 데이터**: {final_player_attendance}")
        #     st.success("✅ 출석 데이터를 성공적으로 찾았습니다!")
        # else:
        #     st.error("❌ 출석 데이터를 찾지 못했습니다!")
        #     st.write("**전체 출석 데이터**:")
        #     for i, att in enumerate(final_attendance_list):
        #         st.write(f"  {i+1}. player_id: {att['player_id']}, status: {att['status']}")
        #
        # st.markdown("---")

        # 상태 변경 섹션 (무조건 표시)
        st.markdown("### ✏️ 출석 상태 변경")

        # 출석 잠금 상태 확인
        is_locked = self.attendance_service.is_attendance_locked(match_id)

        # 잠금 상태 정보 표시
        if match_info:
            from datetime import datetime, timedelta, timezone
            lock_minutes = match_info.get('attendance_lock_minutes', 0)

            if lock_minutes > 0:
                # 한국 표준시(KST) = UTC+9
                KST = timezone(timedelta(hours=9))
                now = datetime.now(timezone.utc).astimezone(KST).replace(tzinfo=None)
                match_datetime = datetime.strptime(f"{match_info['match_date']} {match_info['match_time']}", "%Y-%m-%d %H:%M")
                lock_datetime = match_datetime - timedelta(minutes=lock_minutes)

                st.info(f"**출석 마감 시간**: {lock_datetime.strftime('%m월 %d일 %H:%M')}")

                if is_locked:
                    st.error("🔒 **출석 변경 마감됨**")
                else:
                    remaining = lock_datetime - now
                    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    st.success(f"✅ **변경 가능** (남은 시간: {hours}시간 {minutes}분)")

        st.markdown("---")

        if final_player_attendance:
            current_status = final_player_attendance['status']
            st.info(f"**현재 상태**: {final_player_attendance['status_display']}")
        else:
            current_status = 'absent'  # 기본값 변경
            st.warning("출석 데이터가 없어서 기본값(불참)으로 처리합니다.")

        # 잠금 상태 경고 표시
        if is_locked:
            st.warning("🔒 **출석 변경 마감**: 경기 시작 시간이 임박하여 출석 상태를 변경할 수 없습니다.")

        # 상태 변경 버튼들 (항상 표시)
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "✅ 참석",
                key=f"btn_present_{match_id}_{player_id}",
                width="stretch",
                disabled=(current_status == 'present' or is_locked),
                type="primary" if (current_status != 'present' and not is_locked) else "secondary"
            ):
                # 출석 데이터가 없으면 먼저 생성
                if not final_player_attendance:
                    self.attendance_service.create_attendance_for_match(match_id)

                success = self.attendance_service.update_player_status(match_id, player_id, 'present')
                if success:
                    st.success("✅ 참석으로 변경되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 변경에 실패했습니다. 출석 마감 시간이 지났을 수 있습니다.")

        with col2:
            if st.button(
                "❌ 불참",
                key=f"btn_absent_{match_id}_{player_id}",
                width="stretch",
                disabled=(current_status == 'absent' or is_locked),
                type="primary" if (current_status != 'absent' and not is_locked) else "secondary"
            ):
                # 출석 데이터가 없으면 먼저 생성
                if not final_player_attendance:
                    self.attendance_service.create_attendance_for_match(match_id)

                success = self.attendance_service.update_player_status(match_id, player_id, 'absent')
                if success:
                    st.success("❌ 불참으로 변경되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 변경에 실패했습니다. 출석 마감 시간이 지났을 수 있습니다.")

        with col3:
            if st.button(
                "❓ 미정",
                key=f"btn_pending_{match_id}_{player_id}",
                width="stretch",
                disabled=(current_status == 'pending' or is_locked),
                type="primary" if (current_status != 'pending' and not is_locked) else "secondary"
            ):
                # 출석 데이터가 없으면 먼저 생성
                if not final_player_attendance:
                    self.attendance_service.create_attendance_for_match(match_id)

                success = self.attendance_service.update_player_status(match_id, player_id, 'pending')
                if success:
                    st.success("❓ 미정으로 변경되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 변경에 실패했습니다. 출석 마감 시간이 지났을 수 있습니다.")

        # 도움말
        st.markdown("---")
        st.info("💡 위 버튼들을 클릭하여 출석 상태를 변경할 수 있습니다.")

        # 새로고침 버튼
        if st.button("🔄 새로고침", key=f"refresh_personal_{match_id}_{player_id}"):
            st.success("페이지를 새로고침합니다...")
            st.rerun()

    def _render_team_composition_tab(self) -> None:
        """팀 구성 탭"""
        st.markdown("### 🏆 팀 구성")

        # 경기 선택
        upcoming_matches = self._get_upcoming_matches()

        if not upcoming_matches:
            st.info("예정된 경기가 없습니다.")
            return

        match_options = [
            {
                'label': f"{match['match_date']} {match['match_time']} - {match.get('field_name', '미정')} vs {match.get('opponent', '미정')}",
                'id': match['id']
            }
            for match in upcoming_matches
        ]

        # selectbox 기본값 설정
        dropdown_key = 'team_composition_match_select'
        current_index = st.session_state.get(dropdown_key, 0)
        if not isinstance(current_index, int) or current_index >= len(match_options):
            current_index = 0
            st.session_state[dropdown_key] = 0

        selected_index = st.selectbox(
            "경기 선택",
            options=list(range(len(match_options))),
            format_func=lambda idx: match_options[idx]['label'],
            key=dropdown_key
        )

        selected_match = match_options[selected_index]
        selected_match_id = selected_match['id']

        # 팀 구성 표시
        self._render_team_distribution_detail(selected_match_id)

    def _render_match_attendance_detail(self, match_id: int) -> None:
        """경기별 출석 상세 현황"""
        # 출석 데이터 확인 및 생성 (무한 루프 완전 방지)
        attendance_list = []
        try:
            attendance_list = self.attendance_service.get_match_attendance(match_id)
        except Exception as e:
            st.error(f"출석 데이터 조회 중 오류: {e}")
            return

        # 출석 데이터가 없을 때만 생성 시도
        if not attendance_list:
            # 활성 선수 수 확인
            active_players = self.player_service.get_all_players()
            if not active_players:
                st.warning("활성화된 선수가 없습니다.")
                return

            # 생성 시도 플래그 확인 (detail용 별도 키)
            creation_key = f"attendance_detail_created_{match_id}"
            if not st.session_state.get(creation_key, False):
                with st.spinner("출석 데이터를 생성하고 있습니다..."):
                    try:
                        success = self.attendance_service.create_attendance_for_match(match_id)
                        st.session_state[creation_key] = True

                        if success:
                            # 생성 후 다시 조회
                            attendance_list = self.attendance_service.get_match_attendance(match_id)
                            if not attendance_list:
                                st.error("출석 데이터 생성 후 조회에 실패했습니다.")
                                return
                        else:
                            st.error("출석 데이터 생성에 실패했습니다.")
                            return
                    except Exception as e:
                        st.error(f"출석 데이터 생성 중 오류: {e}")
                        return
            else:
                st.warning("출석 데이터가 없습니다. '출석 데이터 새로고침' 버튼을 클릭해보세요.")
                return

        # 출석 요약
        summary = self.attendance_service.get_attendance_summary(match_id)

        # 2x2 그리드로 변경 (모바일 대응)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("총 인원", summary['total_players'])
        with col2:
            st.metric("✅ 참석", summary['present_count'])

        col3, col4 = st.columns(2)
        with col3:
            st.metric("❌ 불참", summary['absent_count'])
        with col4:
            st.metric("❓ 미정", summary['pending_count'])

        # 참석률 진행바
        if summary['total_players'] > 0:
            progress_value = summary['present_count'] / summary['total_players']
            st.progress(progress_value, text=f"참석 확정률: {summary['present_rate']:.1f}%")

        # 선수별 출석 현황 (불참 제외)
        st.markdown("### 👥 선수별 출석 현황")
        attendance_list = self.attendance_service.get_match_attendance(match_id)

        if attendance_list:
            # 상태별로 그룹화 (불참 제외)
            present_players = [att for att in attendance_list if att['status'] == 'present']
            absent_players = [att for att in attendance_list if att['status'] == 'absent']
            pending_players = [att for att in attendance_list if att['status'] == 'pending']

            # 참석과 미정만 2컬럼으로 표시
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**✅ 참석 확정**")
                if present_players:
                    for player in present_players:
                        st.write(f"• {player['player_name']}")
                else:
                    st.write("아직 참석 확정된 선수가 없습니다.")

            with col2:
                st.markdown("**❓ 미정**")
                if pending_players:
                    for player in pending_players:
                        st.write(f"• {player['player_name']}")
                else:
                    st.write("미정 상태인 선수가 없습니다.")

            # 불참 선수 보기 옵션 (선택적 표시)
            if absent_players:
                st.markdown("---")
                if st.checkbox("👁️ 불참 선수도 보기", key=f"show_absent_{match_id}"):
                    st.markdown("**❌ 불참 선수**")
                    for player in absent_players:
                        st.write(f"• {player['player_name']}")

            # 추가 안내
            st.markdown("---")
            st.info(f"📝 **참고**: 총 {len(absent_players)}명이 불참으로 설정되어 있습니다. (기본값)")

        else:
            st.info("출석 데이터가 없습니다.")

    def _get_upcoming_matches(self) -> list:
        """예정된 경기 목록 조회 (헬퍼 메소드)"""
        try:
            all_matches = self.match_service.get_all_matches()
            from datetime import date
            today = date.today()
            # 오늘 이후의 경기만 필터링
            upcoming = [match for match in all_matches if match['match_date'] >= str(today)]
            return upcoming[:10]  # 최대 10개만
        except:
            return []

    def _get_match_by_id(self, match_id: int) -> dict:
        """경기 ID로 경기 정보 조회 (헬퍼 메소드)"""
        try:
            all_matches = self.match_service.get_all_matches()
            for match in all_matches:
                if match['id'] == match_id:
                    return match
            return {}
        except:
            return {}

    def _render_team_distribution_detail(self, match_id: int) -> None:
        """팀 구성 상세 표시 (팀 구성 탭용)"""
        distribution = team_builder_service.get_distribution(match_id)

        if not distribution:
            st.warning("이 경기의 팀 구성이 아직 저장되지 않았습니다.")
            st.info("관리자가 '팀 구성' 페이지에서 팀을 구성하고 저장하면 여기에 표시됩니다.")
            return

        teams = distribution.get('teams', [])
        bench = distribution.get('bench', [])
        team_names = distribution.get('team_names', [])

        if not teams:
            st.info("구성된 팀이 없습니다.")
            return

        # 팀 구성 요약
        st.markdown("#### 📊 팀 구성 요약")
        total_players = sum(len(team) for team in teams) + len(bench)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("팀 개수", f"{len(teams)}팀")
        with col2:
            st.metric("총 인원", f"{total_players}명")
        with col3:
            st.metric("벤치", f"{len(bench)}명")

        st.markdown("---")

        # 팀별 카드
        for i, (team, team_name) in enumerate(zip(teams, team_names)):
            with st.expander(f"{team_name} ({len(team)}명)", expanded=True):
                if team:
                    for player in team:
                        st.write(f"👤 {player.get('player_name', '알 수 없음')}")
                else:
                    st.info("팀원이 없습니다.")

        # 벤치
        if bench:
            with st.expander(f"🪑 벤치 ({len(bench)}명)", expanded=False):
                for player in bench:
                    st.write(f"👤 {player.get('player_name', '알 수 없음')}")

# 페이지 인스턴스
attendance_page = AttendancePage()
