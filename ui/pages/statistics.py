"""통계 페이지"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ui.components.metrics import metrics_component
from ui.components.auth import render_admin_required_message
from services.player_service import player_service
from services.match_service import match_service
from utils.auth_utils import require_admin_access

class StatisticsPage:
    """통계 페이지"""

    def __init__(self):
        self.player_service = player_service
        self.match_service = match_service

    def render(self) -> None:
        """통계 페이지 렌더링"""
        # 관리자 권한 확인
        if not require_admin_access():
            render_admin_required_message()
            return

        st.header("📈 선수 통계")
        st.info("📅 마무리한 경기만을 기준으로 통계를 계산합니다.")

        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["👤 개인 통계", "🏆 순위표", "📊 팀 통계", "📝 통계 입력"])

        with tab1:
            self._render_individual_stats()

        with tab2:
            self._render_leaderboard()

        with tab3:
            self._render_team_stats()

        with tab4:
            self._render_stats_input()

    def _render_individual_stats(self) -> None:
        """개인 통계"""
        st.subheader("👤 개인 통계 조회")

        players = self.player_service.get_all_players()

        if not players:
            st.info("등록된 선수가 없습니다.")
            return

        # 선수 선택
        selected_player = st.selectbox(
            "선수 선택",
            players,
            format_func=lambda x: f"{x['name']} ({x['position_display']})",
            key="individual_stats_player_select"
        )

        if selected_player:
            player_stats = self.player_service.get_player_detailed_stats(selected_player['id'])

            # 기본 정보
            st.subheader(f"🏃‍♂️ {selected_player['name']} 선수 정보")

            col1, col2 = st.columns(2)

            with col1:
                st.info(f"**포지션**: {selected_player['position_display']}")
                st.info(f"**연락처**: {selected_player['phone'] or '미입력'}")

            with col2:
                st.info(f"**이메일**: {selected_player['email'] or '미입력'}")
                st.info(f"**가입일**: {selected_player['created_at'][:10] if selected_player['created_at'] else '미상'}")

            # 통계 지표
            st.subheader("📊 경기 통계 (마무리한 경기 기준)")

            # 2x2 그리드로 변경 (모바일 대응)
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "득점",
                    f"{player_stats.get('total_goals', 0)}골"
                )

            with col2:
                st.metric(
                    "어시스트",
                    f"{player_stats.get('total_assists', 0)}회"
                )

            col3, col4 = st.columns(2)

            with col3:
                st.metric(
                    "세이브",
                    f"{player_stats.get('total_saves', 0)}회"
                )

            with col4:
                st.metric(
                    "MVP",
                    f"{player_stats.get('total_mvp', 0)}회"
                )

            # 추가 통계
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("경고", f"{player_stats.get('total_yellow_cards', 0)}장")

            with col2:
                st.metric("퇴장", f"{player_stats.get('total_red_cards', 0)}장")

            with col3:
                attendance_rate = player_stats.get('attendance_rate', 0)
                attendance_color = "normal" if attendance_rate >= 80 else "inverse"
                st.metric(
                    "출석률",
                    f"{attendance_rate:.1f}%",
                    delta_color=attendance_color
                )

            # 성과 평가
            self._render_player_evaluation(player_stats)

    def _render_leaderboard(self) -> None:
        """순위표"""
        st.subheader("🏆 팀 순위표 (마무리한 경기 기준)")

        try:
            leaderboard_data = self.player_service.get_leaderboard_data()

            col1, col2, col3 = st.columns(3)

            # 득점왕
            with col1:
                st.markdown("### ⚽ 득점왕")
                goals_data = leaderboard_data.get('goals', [])
                if goals_data:
                    df_goals = pd.DataFrame(goals_data, columns=['순위', '선수명', '득점', '경기수'])
                    st.dataframe(df_goals, width="stretch", hide_index=True)
                else:
                    st.info("득점 데이터가 없습니다.")

            # 어시스트왕
            with col2:
                st.markdown("### 🅰️ 어시스트왕")
                assists_data = leaderboard_data.get('assists', [])
                if assists_data:
                    df_assists = pd.DataFrame(assists_data, columns=['순위', '선수명', '어시스트', '경기수'])
                    st.dataframe(df_assists, width="stretch", hide_index=True)
                else:
                    st.info("어시스트 데이터가 없습니다.")

            # MVP
            with col3:
                st.markdown("### 🏆 MVP")
                mvp_data = leaderboard_data.get('mvp', [])
                if mvp_data:
                    df_mvp = pd.DataFrame(mvp_data, columns=['순위', '선수명', 'MVP횟수'])
                    st.dataframe(df_mvp, width="stretch", hide_index=True)
                else:
                    st.info("MVP 데이터가 없습니다.")

            # 순위표 차트
            if goals_data or assists_data:
                self._render_leaderboard_charts(leaderboard_data)

        except Exception as e:
            st.error(f"순위표 데이터를 불러오는 중 오류가 발생했습니다: {e}")

    def _render_team_stats(self) -> None:
        """팀 통계"""
        st.subheader("📊 팀 전체 통계 (마무리한 경기 기준)")

        # 메트릭 컴포넌트 사용
        metrics_component.render_performance_indicators()

        st.markdown("---")

        # 팀 평균 통계
        team_stats = self.player_service.get_team_average_stats()

        if team_stats:
            col1, col2 = st.columns(2)

            with col1:
                # 경기 통계 차트
                st.subheader("📈 경기 통계")

                chart_data = {
                    '지표': ['경기당 평균 골', '평균 출석률'],
                    '수치': [
                        team_stats.get('avg_goals_per_match', 0),
                        team_stats.get('avg_attendance_rate', 0)
                    ]
                }

                df_chart = pd.DataFrame(chart_data)
                fig = px.bar(df_chart, x='지표', y='수치', title="팀 성과 지표")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # 월별 경기 수 추이
                st.subheader("📅 월별 활동")

                try:
                    from datetime import datetime
                    current_year = datetime.now().year
                    monthly_data = []

                    for month in range(1, 13):
                        count = len(self.match_service.get_monthly_matches(current_year, month))
                        monthly_data.append({'월': f'{month}월', '경기수': count})

                    df_monthly = pd.DataFrame(monthly_data)
                    fig = px.line(df_monthly, x='월', y='경기수', title=f"{current_year}년 월별 경기 수")
                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.info("월별 경기 데이터를 표시할 수 없습니다.")

        else:
            st.info("팀 통계 데이터가 없습니다. 경기를 진행하고 통계를 입력해주세요.")

    def _render_stats_input(self) -> None:
        """통계 입력"""
        st.subheader("📝 경기 통계 입력")

        matches = self.match_service.get_all_matches()
        players = self.player_service.get_all_players()

        if not matches or not players:
            st.info("경기와 선수가 모두 등록되어야 통계를 입력할 수 있습니다.")
            return

        # 경기 선택
        match_options = {}
        for match in matches[:10]:  # 최근 10경기
            display_name = f"{match['match_date']} vs {match.get('opponent', '팀내 경기')}"
            match_options[display_name] = match['id']

        selected_match = st.selectbox("경기 선택", list(match_options.keys()), key="stats_input_match_select")
        match_id = match_options[selected_match]

        # 선수 선택
        selected_player = st.selectbox(
            "선수 선택",
            players,
            format_func=lambda x: f"{x['name']} ({x['position_display']})",
            key="stats_input_player_select"
        )

        if match_id and selected_player:
            self._render_stats_input_form(match_id, selected_player['id'], selected_player['name'])

    def _render_stats_input_form(self, match_id: int, player_id: int, player_name: str) -> None:
        """통계 입력 폼"""
        st.subheader(f"📊 {player_name} 선수 통계 입력")

        with st.form(f"stats_form_{match_id}_{player_id}"):
            # 2x3 그리드로 변경 (모바일 대응)
            col1, col2 = st.columns(2)

            with col1:
                goals = st.number_input("득점", min_value=0, max_value=50, value=0)
                assists = st.number_input("어시스트", min_value=0, max_value=50, value=0)
                saves = st.number_input("세이브", min_value=0, max_value=100, value=0)

            with col2:
                yellow_cards = st.number_input("경고", min_value=0, max_value=10, value=0)
                red_cards = st.number_input("퇴장", min_value=0, max_value=5, value=0)
                mvp = st.checkbox("MVP")

            if st.form_submit_button("통계 저장", type="primary"):
                try:
                    success = self.player_service.save_player_stats(
                        player_id, match_id, goals, assists, saves, yellow_cards, red_cards, mvp
                    )

                    if success:
                        st.success("통계가 성공적으로 저장되었습니다!")
                        st.rerun()
                    else:
                        st.error("통계 저장에 실패했습니다.")

                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

    def _render_player_evaluation(self, player_stats: dict) -> None:
        """선수 성과 평가"""
        st.subheader("⭐ 성과 평가")

        goals = player_stats.get('total_goals', 0)
        assists = player_stats.get('total_assists', 0)
        mvp_count = player_stats.get('total_mvp', 0)
        attendance = player_stats.get('attendance_rate', 0)

        # 평가 점수 계산 (간단한 로직)
        score = (goals * 3) + (assists * 2) + (mvp_count * 10) + (attendance * 0.5)

        if score >= 100:
            evaluation = "🏆 최우수 선수"
            color = "success"
        elif score >= 50:
            evaluation = "⭐ 우수 선수"
            color = "info"
        elif score >= 20:
            evaluation = "👍 일반 선수"
            color = "warning"
        else:
            evaluation = "💪 발전 필요"
            color = "error"

        if color == "success":
            st.success(f"{evaluation} (점수: {score:.1f})")
        elif color == "info":
            st.info(f"{evaluation} (점수: {score:.1f})")
        elif color == "warning":
            st.warning(f"{evaluation} (점수: {score:.1f})")
        else:
            st.error(f"{evaluation} (점수: {score:.1f})")

    def _render_leaderboard_charts(self, leaderboard_data: dict) -> None:
        """순위표 차트"""
        st.subheader("📊 순위 차트")

        goals_data = leaderboard_data.get('goals', [])
        assists_data = leaderboard_data.get('assists', [])

        if goals_data:
            # 득점 차트
            df_goals = pd.DataFrame(goals_data[:5], columns=['순위', '선수명', '득점', '경기수'])
            fig = px.bar(
                df_goals,
                x='선수명',
                y='득점',
                title="상위 5명 득점 현황",
                color='득점'
            )
            st.plotly_chart(fig, use_container_width=True)

        if assists_data:
            # 어시스트 차트
            df_assists = pd.DataFrame(assists_data[:5], columns=['순위', '선수명', '어시스트', '경기수'])
            fig = px.bar(
                df_assists,
                x='선수명',
                y='어시스트',
                title="상위 5명 어시스트 현황",
                color='어시스트'
            )
            st.plotly_chart(fig, use_container_width=True)

# 페이지 인스턴스
statistics_page = StatisticsPage()