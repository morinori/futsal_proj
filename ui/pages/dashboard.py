"""메인 대시보드 페이지"""
import streamlit as st
from ui.components.calendar import calendar_component
from ui.components.metrics import metrics_component
from ui.utils.cached_services import (
    get_recent_news_cached,
    get_monthly_match_count_cached,
    get_total_players_count_cached,
)

class DashboardPage:
    """메인 대시보드 페이지"""

    def render(self) -> None:
        """대시보드 렌더링"""
        self._render_main_content()
        self._render_metrics()
        self._render_recent_news()

    def _render_metrics(self) -> None:
        """메트릭스 섹션 렌더링"""
        st.header("📊 팀 현황")
        metrics_component.render()

    def _render_main_content(self) -> None:
        """메인 컨텐츠 렌더링"""

        col1, col2 = st.columns([2, 1])

        with col1:
            st.header("📅 경기 일정")
            calendar_component.render()

        with col2:
            st.header("📈 팀 현황 요약")
            metrics_component.render_quick_stats()

    def _render_recent_news(self) -> None:
        """최근 뉴스 렌더링"""
        st.header("📰 최신 소식")

        try:
            recent_news = get_recent_news_cached(3)

            if recent_news:
                for news in recent_news:
                    with st.expander(
                        f"{'📌 ' if news['pinned'] else ''}{news['title']} - {news['created_date']}"
                    ):
                        st.write(f"**작성자**: {news['author']}")
                        st.write(f"**카테고리**: {news['category_display']}")
                        st.write("---")
                        st.write(news['content'])

                # 더 많은 소식 보기 버튼
                if len(recent_news) == 3:
                    if st.button("📰 모든 소식 보기", key="view_all_news"):
                        st.session_state['current_page'] = "팀 소식"
                        st.rerun()
            else:
                st.info("아직 등록된 소식이 없습니다.")

        except Exception as e:
            st.error(f"소식을 불러오는 중 오류가 발생했습니다: {e}")


    def _render_welcome_section(self) -> None:
        """환영 섹션 (첫 방문자용)"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 10px; color: white; text-align: center; margin: 2rem 0;">
            <h2>🎉 풋살팀 플랫폼에 오신 것을 환영합니다!</h2>
            <p>경기 일정 관리, 선수 통계, 팀 소식, 재정 관리까지<br>
               팀 운영에 필요한 모든 기능을 한 곳에서 만나보세요.</p>
        </div>
        """, unsafe_allow_html=True)

    def render_quick_actions(self) -> None:
        """빠른 작업 버튼들"""
        st.header("🚀 빠른 작업")

        # 2x2 그리드로 변경 (모바일 대응)
        col1, col2 = st.columns(2)

        with col1:
            if st.button("⚽ 경기 추가", width="stretch"):
                st.session_state['current_page'] = "일정 관리"
                st.rerun()

        with col2:
            if st.button("👥 선수 추가", width="stretch"):
                st.session_state['current_page'] = "선수 관리"
                st.rerun()

        col3, col4 = st.columns(2)

        with col3:
            if st.button("📰 소식 작성", width="stretch"):
                st.session_state['current_page'] = "팀 소식"
                st.rerun()

        with col4:
            if st.button("💰 재정 기록", width="stretch"):
                st.session_state['current_page'] = "팀 재정"
                st.rerun()

    def render_team_overview(self) -> None:
        """팀 개요 (확장된 대시보드용)"""
        st.header("🏆 팀 개요")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 이번 달 활동")

            # 간단한 진행 상황 (캐시됨)
            monthly_matches = get_monthly_match_count_cached()
            total_players = get_total_players_count_cached()

            # 진행률 바
            st.markdown("**경기 활동**")
            progress_value = min(monthly_matches / 8, 1.0)  # 월 8경기를 100%로 가정
            st.progress(progress_value)
            st.caption(f"이번 달 {monthly_matches}경기 진행")

            st.markdown("**팀 구성**")
            team_progress = min(total_players / 20, 1.0)  # 20명을 100%로 가정
            st.progress(team_progress)
            st.caption(f"총 {total_players}명의 선수")

        with col2:
            st.subheader("🎯 목표 달성도")

            # 팀 목표 (예시)
            goals = [
                {"name": "월 경기 수", "current": monthly_matches, "target": 8},
                {"name": "팀 인원", "current": total_players, "target": 20},
            ]

            for goal in goals:
                progress = min(goal["current"] / goal["target"], 1.0)
                st.metric(
                    goal["name"],
                    f"{goal['current']}/{goal['target']}",
                    f"{progress*100:.0f}% 달성"
                )

# 페이지 인스턴스
dashboard_page = DashboardPage()