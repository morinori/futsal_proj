"""팀 구성 페이지"""
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import StringIO

from services.team_builder_service import team_builder_service, PlayerInfo
from services.attendance_service import attendance_service
from services.match_service import match_service
from utils.auth_utils import is_admin_logged_in
from ui.components.auth import render_admin_required_message


class TeamBuilderPage:
    """팀 구성 페이지"""

    def __init__(self):
        self.team_builder_service = team_builder_service
        self.attendance_service = attendance_service
        self.match_service = match_service

        # 세션 상태 초기화
        if 'team_builder' not in st.session_state:
            st.session_state['team_builder'] = {}
        if 'team_builder_selected_match_id' not in st.session_state:
            st.session_state['team_builder_selected_match_id'] = None

    def render(self) -> None:
        """팀 구성 페이지 렌더링"""
        # 관리자 권한 확인
        if not is_admin_logged_in():
            render_admin_required_message()
            return

        st.header("⚽ 팀 구성")

        # 경기 선택 영역
        self._render_match_selection()

        # 선택된 경기가 있는 경우 팀 구성 영역 표시
        selected_match_id = st.session_state.get('team_builder_selected_match_id')
        if selected_match_id:
            self._render_team_builder(selected_match_id)

    def _render_match_selection(self) -> None:
        """경기 선택 영역"""
        st.subheader("📅 다가오는 경기")
        self._render_upcoming_matches()

        # 디버깅: 현재 선택된 경기 ID 표시
        if st.session_state.get('team_builder_selected_match_id'):
            st.caption(f"선택된 경기 ID: {st.session_state.get('team_builder_selected_match_id')}")

    def _render_upcoming_matches(self) -> None:
        """다가오는 경기 목록"""
        # 다음 경기 조회
        next_match = self.match_service.get_next_match()

        # 최근 5경기 조회 (향후 경기 포함)
        all_matches = self.match_service.get_all_matches()
        today = datetime.now().date()

        # 향후 경기 필터링
        upcoming_matches = [
            m for m in all_matches
            if datetime.strptime(m['match_date'], '%Y-%m-%d').date() >= today
        ]

        # 최근 순으로 정렬 (가까운 미래부터)
        upcoming_matches.sort(key=lambda x: (x['match_date'], x['match_time']))

        if not upcoming_matches:
            st.info("예정된 경기가 없습니다.")
            return

        # 경기 선택 selectbox
        match_options = [
            f"{m['match_date']} {m['match_time']} - {m.get('field_name', '미정')} vs {m.get('opponent', '미정')}"
            for m in upcoming_matches
        ]

        # 현재 선택된 경기가 있으면 그 인덱스 사용, 없으면 다음 경기
        current_selected_id = st.session_state.get('team_builder_selected_match_id')
        default_index = 0

        if current_selected_id:
            # 현재 선택된 경기의 인덱스 찾기
            for i, m in enumerate(upcoming_matches):
                if m['id'] == current_selected_id:
                    default_index = i
                    break
        elif next_match:
            # 선택된 경기가 없으면 다음 경기
            for i, m in enumerate(upcoming_matches):
                if m['id'] == next_match['id']:
                    default_index = i
                    break

        selected_option = st.selectbox(
            "경기를 선택하세요",
            options=match_options,
            index=default_index,
            key="upcoming_match_selector"
        )

        # 선택된 경기 ID 저장
        if selected_option:
            selected_index = match_options.index(selected_option)
            selected_match_id = upcoming_matches[selected_index]['id']

            # 현재 선택된 경기와 다른 경기를 선택한 경우
            current_selected = st.session_state.get('team_builder_selected_match_id')

            if current_selected is not None and current_selected != selected_match_id:
                # 작업 중인 데이터가 있으면 경고
                if self._has_unsaved_changes():
                    st.warning("⚠️ 다른 경기를 선택하면 현재 작업 중인 팀 구성이 초기화됩니다.")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("경기 변경", type="primary", key="confirm_match_change_upcoming"):
                            st.session_state['team_builder_selected_match_id'] = selected_match_id
                            st.rerun()
                    with col2:
                        if st.button("취소", key="cancel_match_change_upcoming"):
                            st.rerun()
                else:
                    # 작업 중인 데이터가 없으면 조용히 변경
                    st.session_state['team_builder_selected_match_id'] = selected_match_id
            elif current_selected is None:
                # 첫 로드 시 기본값 설정 (rerun 없이)
                st.session_state['team_builder_selected_match_id'] = selected_match_id

    def _has_unsaved_changes(self) -> bool:
        """저장되지 않은 변경사항이 있는지 확인"""
        current_match_id = st.session_state.get('team_builder_selected_match_id')
        if not current_match_id:
            return False

        match_key = f"match_{current_match_id}"
        return match_key in st.session_state['team_builder']

    def _render_team_builder(self, match_id: int) -> None:
        """팀 구성 영역"""
        # 경기 정보 표시
        match_info = self._get_match_info(match_id)
        if not match_info:
            st.error("경기 정보를 찾을 수 없습니다.")
            return

        # 경기 요약 카드
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 날짜", match_info['match_date'])
        with col2:
            st.metric("⏰ 시간", match_info['match_time'])
        with col3:
            st.metric("🏟️ 구장", match_info.get('field_name', '미정'))
        with col4:
            st.metric("🆚 상대", match_info.get('opponent', '미정'))

        # 참석자 데이터 조회
        attendance_data = self.attendance_service.get_match_attendance(match_id)
        present_players = [
            {'player_id': att['player_id'], 'player_name': att['player_name']}
            for att in attendance_data
            if att['status'] == 'present'
        ]

        # 참석 현황 요약
        st.markdown("---")
        st.subheader("📊 참석 현황")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            present_count = len([a for a in attendance_data if a['status'] == 'present'])
            st.metric("참석", f"{present_count}명", delta=None, delta_color="normal")
        with col2:
            absent_count = len([a for a in attendance_data if a['status'] == 'absent'])
            st.metric("불참", f"{absent_count}명")
        with col3:
            pending_count = len([a for a in attendance_data if a['status'] == 'pending'])
            st.metric("미정", f"{pending_count}명")
        with col4:
            st.metric("총 인원", f"{len(attendance_data)}명")

        if not present_players:
            st.warning("⚠️ 참석 선수가 없어 팀을 구성할 수 없습니다.")
            return

        # 팀 설정 카드
        st.markdown("---")
        self._render_team_config(match_id, present_players)

        # 팀 구성 상태가 있으면 표시
        match_key = f"match_{match_id}"
        if match_key in st.session_state['team_builder']:
            self._render_team_distribution(match_id, present_players)

    def _render_team_config(self, match_id: int, present_players: List[Dict[str, Any]]) -> None:
        """팀 설정 카드"""
        st.subheader("⚙️ 팀 설정")

        col1, col2 = st.columns(2)

        with col1:
            team_count = st.number_input(
                "팀 개수",
                min_value=0,
                max_value=10,
                value=0,
                step=1,
                key=f"team_count_{match_id}",
                help="0을 입력하면 팀당 인원으로 자동 계산됩니다."
            )

        with col2:
            team_size = st.number_input(
                "팀당 인원",
                min_value=0,
                max_value=20,
                value=0,
                step=1,
                key=f"team_size_{match_id}",
                help="0을 입력하면 팀 개수로 자동 계산됩니다."
            )

        # 레이아웃 계산
        layout = self.team_builder_service.calculate_layout(
            total_present=len(present_players),
            team_count=team_count if team_count > 0 else None,
            team_size=team_size if team_size > 0 else None
        )

        # 계산 결과 표시
        if layout.is_valid:
            st.success(f"✅ {layout.message}")

            # 자동 분배 옵션
            col1, col2, col3 = st.columns(3)

            with col1:
                remainder_mode = st.radio(
                    "잔여 인원 처리",
                    options=["bench", "spread"],
                    format_func=lambda x: "벤치 유지" if x == "bench" else "팀에 분산",
                    key=f"remainder_mode_{match_id}"
                )

            with col2:
                st.write("")  # 간격
                st.write("")  # 간격
                if st.button("🎲 자동 분배", type="primary", key=f"auto_distribute_{match_id}"):
                    self._auto_distribute(match_id, present_players, layout, remainder_mode)
                    st.rerun()

            with col3:
                st.write("")  # 간격
                st.write("")  # 간격
                if st.button("🔄 초기화", key=f"reset_distribution_{match_id}"):
                    match_key = f"match_{match_id}"
                    if match_key in st.session_state['team_builder']:
                        del st.session_state['team_builder'][match_key]
                    st.rerun()

        else:
            st.error(f"❌ {layout.message}")

    def _auto_distribute(
        self,
        match_id: int,
        present_players: List[Dict[str, Any]],
        layout,
        remainder_mode: str
    ) -> None:
        """자동 분배 실행"""
        # 분배 실행
        distribution = self.team_builder_service.distribute_players(
            players=present_players,
            team_count=layout.team_count,
            team_size=layout.team_size,
            strategy="balanced_random"
        )

        # 잔여 인원 처리
        if remainder_mode == "spread" and distribution.bench:
            distribution = self.team_builder_service.rebalance_with_remainder(
                teams=distribution.teams,
                bench=distribution.bench,
                mode="spread"
            )

        # 세션 상태에 저장
        match_key = f"match_{match_id}"
        st.session_state['team_builder'][match_key] = {
            'config': {
                'team_count': layout.team_count,
                'team_size': layout.team_size,
                'remainder_mode': remainder_mode
            },
            'teams': distribution.teams,
            'bench': distribution.bench,
            'team_names': distribution.team_names
        }

    def _render_team_distribution(self, match_id: int, present_players: List[Dict[str, Any]]) -> None:
        """팀 분배 결과 표시"""
        match_key = f"match_{match_id}"
        data = st.session_state['team_builder'][match_key]

        teams = data['teams']
        bench = data['bench']
        team_names = data['team_names']

        st.markdown("---")
        st.subheader("🏆 팀 구성")

        # 팀별 카드
        for i, (team, team_name) in enumerate(zip(teams, team_names)):
            with st.expander(f"{team_name} ({len(team)}명)", expanded=True):
                if team:
                    # 팀 선수 목록
                    for player in team:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"👤 {player.player_name}")
                        with col2:
                            if st.button("→ 벤치", key=f"to_bench_{match_id}_{i}_{player.player_id}"):
                                self._move_player(match_id, player.player_id, f"team_{i}", "bench")
                                st.rerun()
                else:
                    st.info("팀원이 없습니다.")

        # 벤치 카드
        if bench:
            with st.expander(f"🪑 벤치 ({len(bench)}명)", expanded=True):
                for player in bench:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"👤 {player.player_name}")
                    with col2:
                        # 팀 선택 selectbox
                        team_options = [f"Team {chr(65+i)}" for i in range(len(teams))]
                        selected_team = st.selectbox(
                            "팀 선택",
                            options=team_options,
                            key=f"select_team_{match_id}_{player.player_id}",
                            label_visibility="collapsed"
                        )
                        team_idx = team_options.index(selected_team)
                        if st.button("→ 팀", key=f"to_team_{match_id}_{player.player_id}"):
                            self._move_player(match_id, player.player_id, "bench", f"team_{team_idx}")
                            st.rerun()

        # 결과 요약 및 내보내기
        st.markdown("---")
        self._render_export_section(match_id, teams, bench, team_names)

    def _move_player(self, match_id: int, player_id: int, from_location: str, to_location: str) -> None:
        """선수 이동"""
        match_key = f"match_{match_id}"
        data = st.session_state['team_builder'][match_key]

        teams, bench, success, message = self.team_builder_service.move_player_to_team(
            teams=data['teams'],
            bench=data['bench'],
            player_id=player_id,
            from_location=from_location,
            to_location=to_location
        )

        if success:
            data['teams'] = teams
            data['bench'] = bench
            st.success(message)
        else:
            st.error(message)

    def _render_export_section(
        self,
        match_id: int,
        teams: List[List[PlayerInfo]],
        bench: List[PlayerInfo],
        team_names: List[str]
    ) -> None:
        """결과 요약 및 내보내기 영역"""
        st.subheader("📤 결과 내보내기")

        # 텍스트 포맷 생성
        text_output = self._generate_text_output(teams, bench, team_names)

        # 클립보드 복사용
        st.text_area("팀 구성 결과 (복사용)", text_output, height=200, key=f"text_output_{match_id}")

        col1, col2 = st.columns(2)

        with col1:
            # CSV 다운로드
            csv_output = self._generate_csv_output(teams, bench, team_names)
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv_output,
                file_name=f"team_distribution_{match_id}.csv",
                mime="text/csv",
                key=f"download_csv_{match_id}"
            )

        with col2:
            # 재분배 버튼 (이미 위에 있으므로 생략 가능)
            pass

    def _generate_text_output(
        self,
        teams: List[List[PlayerInfo]],
        bench: List[PlayerInfo],
        team_names: List[str]
    ) -> str:
        """텍스트 포맷 생성"""
        lines = []
        lines.append("=== 팀 구성 결과 ===\n")

        for team, team_name in zip(teams, team_names):
            lines.append(f"\n[{team_name}] ({len(team)}명)")
            for player in team:
                lines.append(f"  - {player.player_name}")

        if bench:
            lines.append(f"\n[벤치] ({len(bench)}명)")
            for player in bench:
                lines.append(f"  - {player.player_name}")

        return "\n".join(lines)

    def _generate_csv_output(
        self,
        teams: List[List[PlayerInfo]],
        bench: List[PlayerInfo],
        team_names: List[str]
    ) -> str:
        """CSV 포맷 생성"""
        rows = []
        rows.append(["팀", "선수명"])

        for team, team_name in zip(teams, team_names):
            for player in team:
                rows.append([team_name, player.player_name])

        for player in bench:
            rows.append(["벤치", player.player_name])

        df = pd.DataFrame(rows[1:], columns=rows[0])
        return df.to_csv(index=False, encoding='utf-8-sig')

    def _get_match_info(self, match_id: int) -> Optional[Dict[str, Any]]:
        """경기 정보 조회"""
        all_matches = self.match_service.get_all_matches()
        for match in all_matches:
            if match['id'] == match_id:
                return match
        return None


# 페이지 인스턴스 생성
def render():
    """페이지 렌더링 함수"""
    page = TeamBuilderPage()
    page.render()
