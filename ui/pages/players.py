"""선수 관리 페이지"""
import streamlit as st
from typing import Dict, Any
from services.player_service import player_service
from services.match_service import match_service
from database.repositories import attendance_repo
from utils.auth_utils import require_admin_access

class PlayersPage:
    """선수 관리 페이지"""

    def __init__(self):
        self.player_service = player_service
        self.match_service = match_service
        self.attendance_repo = attendance_repo

    def render(self) -> None:
        """선수 관리 페이지 렌더링"""
        require_admin_access()
        st.header("👥 선수 관리")

        # 탭 구성
        tab1, tab2, tab3 = st.tabs(["👥 선수 목록", "➕ 선수 추가", "📋 출석 관리"])

        with tab1:
            self._render_player_list()

        with tab2:
            self._render_add_player()

        with tab3:
            self._render_attendance_management()

    def _render_player_list(self) -> None:
        """선수 목록"""
        st.subheader("👥 등록된 선수 목록")

        players = self.player_service.get_all_players()

        if not players:
            st.info("등록된 선수가 없습니다.")
            return

        # 검색 및 필터
        col1, col2 = st.columns([2, 1])

        with col1:
            search_term = st.text_input("선수 검색", placeholder="이름으로 검색...")

        with col2:
            position_filter = st.selectbox("포지션 필터", ["전체", "GK", "DF", "MF", "FW"])

        # 필터링된 선수 목록
        filtered_players = players

        if search_term:
            filtered_players = [p for p in filtered_players
                             if search_term.lower() in p['name'].lower()]

        if position_filter != "전체":
            filtered_players = [p for p in filtered_players
                             if p['position'] == position_filter]

        st.write(f"**총 {len(filtered_players)}명의 선수**")

        # 선수 목록 표시
        for i, player in enumerate(filtered_players, 1):
            with st.expander(f"{i}. {player['name']} ({player['position_display']})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**이름**: {player['name']}")
                    st.write(f"**포지션**: {player['position_display']}")
                    st.write(f"**연락처**: {player['phone'] or '미입력'}")

                with col2:
                    st.write(f"**이메일**: {player['email'] or '미입력'}")
                    st.write(f"**가입일**: {player['created_at'][:10] if player['created_at'] else '미상'}")

                # 선수 관리 버튼들
                col_btn1, col_btn2, col_btn3 = st.columns(3)

                with col_btn1:
                    if st.button(f"📊 통계", key=f"stats_{player['id']}", width="stretch"):
                        self._show_player_stats(player['id'])

                with col_btn2:
                    if st.button(f"✏️ 수정", key=f"edit_player_{player['id']}", width="stretch"):
                        st.session_state[f"edit_mode_{player['id']}"] = True
                        st.rerun()

                with col_btn3:
                    if st.button(f"🗑️ 삭제", key=f"delete_player_{player['id']}", type="secondary", width="stretch"):
                        if st.session_state.get(f"confirm_delete_player_{player['id']}", False):
                            try:
                                success = self.player_service.delete_player(player['id'])
                                if success:
                                    st.success("선수가 삭제되었습니다!")
                                    # 확인 상태 초기화
                                    if f"confirm_delete_player_{player['id']}" in st.session_state:
                                        del st.session_state[f"confirm_delete_player_{player['id']}"]
                                    st.rerun()
                                else:
                                    st.error("선수 삭제에 실패했습니다.")
                            except Exception as e:
                                st.error(f"삭제 중 오류가 발생했습니다: {e}")
                        else:
                            st.session_state[f"confirm_delete_player_{player['id']}"] = True
                            st.warning("정말로 이 선수를 삭제하시겠습니까? 다시 삭제 버튼을 눌러주세요.")
                            st.rerun()

                # 수정 모드인 경우 수정 폼 표시
                if st.session_state.get(f"edit_mode_{player['id']}", False):
                    self._render_edit_player_form(player)

    def _render_add_player(self) -> None:
        """선수 추가"""
        st.subheader("➕ 새 선수 추가")

        with st.form("add_player_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("이름 *")
                position = st.selectbox("포지션 *", ["GK", "DF", "MF", "FW"])

            with col2:
                phone = st.text_input("전화번호", placeholder="010-1234-5678")
                email = st.text_input("이메일", placeholder="player@email.com")

            st.markdown("*표시된 항목은 필수입니다.")

            if st.form_submit_button("선수 추가", type="primary"):
                if name and position:
                    try:
                        # 중복 이름 체크
                        if self.player_service.check_player_name_exists(name):
                            st.error("이미 등록된 선수 이름입니다.")
                        else:
                            success = self.player_service.create_player(name, position, phone, email)
                            if success:
                                st.success("선수가 성공적으로 추가되었습니다!")
                                st.rerun()
                            else:
                                st.error("선수 추가에 실패했습니다.")

                    except ValueError as e:
                        st.error(f"입력 오류: {e}")
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
                else:
                    st.error("이름과 포지션은 필수 항목입니다.")

    def _render_attendance_management(self) -> None:
        """출석 관리"""
        st.subheader("📋 출석 관리")

        # 경기 선택
        matches = self.match_service.get_all_matches()

        if not matches:
            st.info("등록된 경기가 없습니다.")
            return

        # 최근 경기를 기본 선택으로
        match_options = {}
        for match in matches[:20]:  # 최근 20경기만
            display_name = f"{match['match_date']} {match['match_time']} vs {match.get('opponent', '팀내 경기')}"
            match_options[display_name] = match['id']

        if 'selected_match_id' in st.session_state:
            # 다른 페이지에서 넘어온 경우
            selected_match_id = st.session_state['selected_match_id']
            del st.session_state['selected_match_id']
        else:
            selected_match = st.selectbox("경기 선택", list(match_options.keys()))
            selected_match_id = match_options[selected_match]

        if selected_match_id:
            self._render_attendance_for_match(selected_match_id)

    def _render_attendance_for_match(self, match_id: int) -> None:
        """특정 경기의 출석 관리"""
        players = self.player_service.get_all_players()
        attendance_data = self.attendance_repo.get_by_match(match_id)  # 올바른 메소드명 사용

        if not players:
            st.info("등록된 선수가 없습니다.")
            return

        # 현재 출석 상태를 딕셔너리로 변환
        attendance_status = {}
        for att in attendance_data:
            attendance_status[att['player_id']] = att['status']

        st.subheader("출석 현황 업데이트")

        # 출석 상태 업데이트 폼
        with st.form(f"attendance_form_{match_id}"):
            attendance_updates = {}

            # 3열로 선수 목록 표시
            cols = st.columns(3)
            for i, player in enumerate(players):
                col = cols[i % 3]

                with col:
                    current_status = attendance_status.get(player['id'], 'present')

                    # 현재 상태가 지원되는 상태 목록에 없으면 기본값으로 설정
                    available_statuses = ['present', 'absent', 'pending']
                    if current_status not in available_statuses:
                        if current_status == 'late':
                            current_status = 'present'  # late는 present로 매핑
                        else:
                            current_status = 'pending'  # 알 수 없는 상태는 pending으로

                    status = st.selectbox(
                        f"{player['name']} ({player['position']})",
                        available_statuses,
                        index=available_statuses.index(current_status),
                        key=f"attendance_{match_id}_{player['id']}",
                        format_func=lambda x: {'present': '✅ 참석', 'absent': '❌ 불참', 'pending': '❓ 미정'}[x]
                    )
                    attendance_updates[player['id']] = status

            if st.form_submit_button("출석 현황 업데이트"):
                try:
                    # 각 선수의 상태 변경을 개별적으로 처리
                    update_count = 0
                    errors = []

                    for player_id, new_status in attendance_updates.items():
                        current_status = attendance_status.get(player_id, 'present')

                        # 상태가 변경된 경우만 업데이트
                        if new_status != current_status:
                            from services.attendance_service import attendance_service
                            success = attendance_service.update_player_status(match_id, player_id, new_status)
                            if success:
                                update_count += 1
                            else:
                                # 실패한 선수 찾기
                                failed_player = next((p for p in players if p['id'] == player_id), None)
                                errors.append(failed_player['name'] if failed_player else f"선수 ID {player_id}")

                    # 결과 메시지
                    if errors:
                        st.warning(f"일부 업데이트 실패: {', '.join(errors)}")

                    if update_count > 0:
                        st.success(f"출석 현황이 업데이트되었습니다! ({update_count}명 변경)")
                        st.rerun()
                    elif not errors:
                        st.info("변경된 출석 상태가 없습니다.")

                except Exception as e:
                    st.error(f"업데이트 실패: {e}")

        # 출석 통계 표시
        self._render_attendance_stats(match_id, players, attendance_status)

    def _render_attendance_stats(self, match_id: int, players: list, attendance_status: dict) -> None:
        """출석 통계 표시"""
        st.subheader("📊 출석 통계")

        total_players = len(players)
        present_count = sum(1 for status in attendance_status.values() if status == 'present')
        absent_count = sum(1 for status in attendance_status.values() if status == 'absent')
        pending_count = sum(1 for status in attendance_status.values() if status == 'pending')
        late_count = sum(1 for status in attendance_status.values() if status == 'late')  # 혹시 있을 경우

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("총 선수", f"{total_players}명")
        with col2:
            st.metric("✅ 참석", f"{present_count}명", f"{(present_count/total_players*100):.1f}%" if total_players > 0 else "0%")
        with col3:
            st.metric("❌ 불참", f"{absent_count}명", f"{(absent_count/total_players*100):.1f}%" if total_players > 0 else "0%")
        with col4:
            st.metric("❓ 미정", f"{pending_count}명", f"{(pending_count/total_players*100):.1f}%" if total_players > 0 else "0%")

    def _render_edit_player_form(self, player: Dict[str, Any]) -> None:
        """선수 수정 폼"""
        st.markdown("---")
        st.subheader(f"✏️ {player['name']} 선수 정보 수정")

        with st.form(f"edit_player_form_{player['id']}"):
            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("이름 *", value=player['name'], key=f"edit_name_{player['id']}")
                new_position = st.selectbox(
                    "포지션 *",
                    ["GK", "DF", "MF", "FW"],
                    index=["GK", "DF", "MF", "FW"].index(player['position']),
                    key=f"edit_position_{player['id']}"
                )

            with col2:
                new_phone = st.text_input("전화번호", value=player['phone'] or "", key=f"edit_phone_{player['id']}")
                new_email = st.text_input("이메일", value=player['email'] or "", key=f"edit_email_{player['id']}")

            st.markdown("*표시된 항목은 필수입니다.")

            # 폼 버튼
            col_form1, col_form2 = st.columns(2)

            with col_form1:
                if st.form_submit_button("수정 저장", type="primary", width="stretch"):
                    if new_name and new_position:
                        try:
                            # 중복 이름 체크 (기존 선수 제외)
                            if self.player_service.check_player_name_exists(new_name, exclude_id=player['id']):
                                st.error("이미 등록된 선수 이름입니다.")
                            else:
                                success = self.player_service.update_player(
                                    player['id'], new_name, new_position, new_phone, new_email
                                )
                                if success:
                                    st.success("선수 정보가 수정되었습니다!")
                                    # 수정 모드 종료
                                    if f"edit_mode_{player['id']}" in st.session_state:
                                        del st.session_state[f"edit_mode_{player['id']}"]
                                    st.rerun()
                                else:
                                    st.error("선수 정보 수정에 실패했습니다.")
                        except ValueError as e:
                            st.error(f"입력 오류: {e}")
                        except Exception as e:
                            st.error(f"수정 중 오류가 발생했습니다: {e}")
                    else:
                        st.error("이름과 포지션은 필수 항목입니다.")

            with col_form2:
                if st.form_submit_button("취소", width="stretch"):
                    # 수정 모드 종료
                    if f"edit_mode_{player['id']}" in st.session_state:
                        del st.session_state[f"edit_mode_{player['id']}"]
                    st.rerun()

    def _show_player_stats(self, player_id: int) -> None:
        """선수 상세 통계 표시"""
        player_stats = self.player_service.get_player_detailed_stats(player_id)
        player_info = self.player_service.get_player_by_id(player_id)

        if not player_info:
            st.error("선수 정보를 찾을 수 없습니다.")
            return

        st.subheader(f"📊 {player_info['name']} 선수 통계")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("총 득점", f"{player_stats.get('total_goals', 0)}골")
            st.metric("총 어시스트", f"{player_stats.get('total_assists', 0)}회")

        with col2:
            st.metric("총 세이브", f"{player_stats.get('total_saves', 0)}회")
            st.metric("MVP 횟수", f"{player_stats.get('total_mvp', 0)}회")

        with col3:
            st.metric("경고", f"{player_stats.get('total_yellow_cards', 0)}장")
            st.metric("출장 정지", f"{player_stats.get('total_red_cards', 0)}장")

        # 출석률
        attendance_rate = player_stats.get('attendance_rate', 0)
        st.metric("출석률", f"{attendance_rate:.1f}%")

        if attendance_rate >= 80:
            st.success("훌륭한 출석률을 보이고 있습니다! 👏")
        elif attendance_rate >= 60:
            st.warning("출석률이 다소 낮습니다. 더 자주 참여해주세요! 💪")
        else:
            st.error("출석률이 매우 낮습니다. 팀 활동에 더 많이 참여해주세요! 🔥")

    def render_player_overview(self) -> None:
        """선수 현황 개요 (대시보드용)"""
        players = self.player_service.get_all_players()

        if not players:
            st.info("등록된 선수가 없습니다.")
            return

        # 포지션별 분포
        position_counts = {}
        for player in players:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("포지션별 분포")
            for pos, count in position_counts.items():
                st.write(f"**{pos}**: {count}명")

        with col2:
            st.subheader("최근 활동 선수")
            # 최근 경기에 참여한 선수들 (구현 필요 시)
            active_players = players[:5]  # 임시로 처음 5명
            for player in active_players:
                st.write(f"• {player['name']} ({player['position']})")

# 페이지 인스턴스
players_page = PlayersPage()