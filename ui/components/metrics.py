"""메트릭스 컴포넌트"""
import streamlit as st
from typing import Dict, Any
from services.match_service import match_service
from services.player_service import player_service
from services.finance_service import finance_service
from services.team_builder_service import team_builder_service

class MetricsComponent:
    """메인 지표 컴포넌트"""

    def __init__(self):
        self.match_service = match_service
        self.player_service = player_service
        self.finance_service = finance_service

    def render(self) -> None:
        """메트릭스 렌더링"""
        self._render_main_metrics()
        self._render_secondary_metrics()

    def _render_main_metrics(self) -> None:
        """주요 메트릭스 렌더링"""
        # 주요 지표 데이터 수집
        next_match = self.match_service.get_next_match()
        total_players = self.player_service.get_total_count()
        monthly_matches = self.match_service.get_monthly_count()
        team_balance = self.finance_service.get_team_balance()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if next_match:
                next_date = next_match.get('match_date', '미정')
                next_opponent = next_match.get('opponent', '팀내 경기')
                st.metric(
                    label="다음 경기",
                    value=f"{next_date}",
                    help=f"상대: {next_opponent}"
                )
            else:
                st.metric(label="다음 경기", value="예정 없음")

        with col2:
            st.metric(
                label="총 선수 수",
                value=f"{total_players}명"
            )

        with col3:
            st.metric(
                label="이번 달 경기",
                value=f"{monthly_matches}경기"
            )

        with col4:
            balance_color = "normal" if team_balance >= 0 else "inverse"
            st.metric(
                label="팀 잔고",
                value=f"{team_balance:,}원",
                delta_color=balance_color
            )

    def _render_secondary_metrics(self) -> None:
        """보조 메트릭스 렌더링"""
        st.markdown("---")

        # 최근 경기만 표시
        recent_matches = self.match_service.get_recent_matches(3)

        st.subheader("🏆 최근 경기")
        if recent_matches:
            for i, match in enumerate(recent_matches, 1):
                opponent = match.get('opponent', '팀내 경기')
                result = match.get('result', '결과 미입력')
                match_date = match.get('match_date', '')

                st.write(f"**{i}.** {match_date}")
                st.write(f"vs {opponent} - {result}")
                if i < len(recent_matches):
                    st.write("---")
        else:
            st.info("최근 경기 데이터가 없습니다.")

    def render_quick_stats(self) -> None:
        """간단한 요약 통계 (대시보드 하단용)"""

        # 간단한 통계 수집
        matches_this_month = self.match_service.get_monthly_count()
        active_players = self.player_service.get_total_count()

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"🏃‍♂️ 활성 선수: **{active_players}명**")
            st.info(f"⚽ 이번 달 경기: **{matches_this_month}경기**")

        with col2:
            # 최근 뉴스나 공지사항이 있다면 표시
            try:
                from services.news_service import news_service
                recent_news = news_service.get_recent_news(1)
                if recent_news:
                    news = recent_news[0]
                    st.success(f"📢 최신 소식: {news['title'][:20]}...")
                else:
                    st.success("📢 새로운 소식이 없습니다.")
            except:
                st.success("📢 소식을 불러올 수 없습니다.")

        # 다음 경기 팀 구성 표시
        self._render_next_match_team_summary()

    def _render_next_match_team_summary(self) -> None:
        """다음 경기 팀 구성 요약"""
        next_match = self.match_service.get_next_match()

        if not next_match:
            return

        match_id = next_match['id']
        distribution = team_builder_service.get_distribution(match_id)

        if not distribution:
            return

        st.markdown("---")
        st.subheader("🏆 다음 경기 팀 구성")

        teams = distribution.get('teams', [])
        team_names = distribution.get('team_names', [])

        if teams:
            # 팀별 간단한 요약
            team_summary = []
            for team, team_name in zip(teams, team_names):
                team_summary.append(f"{team_name}: {len(team)}명")

            st.info(" | ".join(team_summary))

            # 상세 보기 링크
            if st.button("📋 출석 관리에서 상세 보기", key="view_team_detail"):
                st.session_state['current_page'] = "attendance"
                st.session_state['selected_match_id'] = match_id
                st.rerun()

    def render_performance_indicators(self) -> None:
        """성과 지표 (통계 페이지용)"""
        st.subheader("🎯 팀 성과 지표 (마무리한 경기 기준)")

        team_stats = self.player_service.get_team_average_stats()

        if team_stats:
            col1, col2, col3 = st.columns(3)

            with col1:
                avg_goals = team_stats.get('avg_goals_per_match', 0)
                st.metric(
                    "경기당 평균 득점",
                    f"{avg_goals:.1f}",
                    help="팀의 경기당 평균 득점 수"
                )

            with col2:
                attendance_rate = team_stats.get('avg_attendance_rate', 0)
                attendance_color = "normal" if attendance_rate >= 80 else "inverse"
                st.metric(
                    "평균 출석률",
                    f"{attendance_rate:.1f}%",
                    delta_color=attendance_color,
                    help="선수들의 평균 출석률"
                )

            with col3:
                total_matches = team_stats.get('total_matches', 0)
                st.metric(
                    "총 경기 수",
                    f"{total_matches}경기",
                    help="지금까지 진행한 총 경기 수"
                )
        else:
            st.info("아직 경기 데이터가 없습니다. 첫 경기를 등록해보세요!")

# 컴포넌트 인스턴스
metrics_component = MetricsComponent()