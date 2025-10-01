"""팀 소식 페이지"""
import streamlit as st
from services.news_service import news_service

class NewsPage:
    """팀 소식 페이지"""

    def __init__(self):
        self.news_service = news_service

    def render(self) -> None:
        """팀 소식 페이지 렌더링 (일반 사용자 - 열람 전용)"""
        st.header("📰 팀 소식")

        # 일반 사용자는 소식 목록만 열람 가능
        self._render_news_list()

    def _render_news_list(self) -> None:
        """소식 목록"""
        st.subheader("📋 팀 소식 목록")

        # 검색 및 필터
        col1, col2 = st.columns([2, 1])

        with col1:
            search_term = st.text_input("소식 검색", placeholder="제목, 내용, 작성자로 검색...")

        with col2:
            category_options = self.news_service.get_category_options()
            category_filter = st.selectbox(
                "카테고리 필터",
                ["전체"] + [cat['code'] for cat in category_options],
                format_func=lambda x: "전체" if x == "전체" else next(
                    (cat['display'] for cat in category_options if cat['code'] == x), x
                )
            )

        # 소식 목록 가져오기
        try:
            if search_term:
                news_list = self.news_service.search_news(search_term)
            elif category_filter != "전체":
                news_list = self.news_service.get_news_by_category(category_filter)
            else:
                news_list = self.news_service.get_all_news()

            if news_list:
                st.write(f"**총 {len(news_list)}개의 소식**")

                # 고정 소식 먼저 표시
                pinned_news = [news for news in news_list if news['pinned']]
                regular_news = [news for news in news_list if not news['pinned']]

                if pinned_news:
                    st.markdown("### 📌 고정 소식")
                    for news in pinned_news:
                        self._render_news_item(news, is_pinned=True)

                if regular_news:
                    st.markdown("### 📰 일반 소식")
                    for news in regular_news:
                        self._render_news_item(news, is_pinned=False)

            else:
                st.info("소식이 없습니다.")

        except Exception as e:
            st.error(f"소식을 불러오는 중 오류가 발생했습니다: {e}")

    def _render_news_item(self, news: dict, is_pinned: bool = False) -> None:
        """개별 소식 아이템 렌더링"""
        pin_icon = "📌 " if is_pinned else ""
        title = f"{pin_icon}{news['title']}"

        with st.expander(f"{title} - {news['created_date']}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**작성자**: {news['author']}")
                st.markdown(f"**카테고리**: {news['category_display']}")
                st.markdown(f"**작성일**: {news['created_date']}")

            with col2:
                if news['pinned']:
                    st.success("📌 고정됨")

            st.markdown("---")
            st.markdown(news['content'])


    def render_news_summary(self) -> None:
        """소식 요약 (대시보드용)"""
        try:
            recent_news = self.news_service.get_recent_news(3)
            pinned_news = self.news_service.get_pinned_news()

            if pinned_news:
                st.subheader("📌 중요 소식")
                for news in pinned_news[:2]:  # 최대 2개만
                    with st.expander(f"📌 {news['title']}"):
                        st.write(f"**작성자**: {news['author']}")
                        st.write(news['content_preview'])

            if recent_news:
                st.subheader("📰 최신 소식")
                for news in recent_news:
                    if not news['pinned']:  # 고정 소식이 아닌 것만
                        with st.expander(f"{news['title']} - {news['created_date']}"):
                            st.write(f"**작성자**: {news['author']}")
                            st.write(f"**카테고리**: {news['category_display']}")
                            st.write(news['content_preview'])

        except Exception as e:
            st.error(f"소식을 불러오는 중 오류가 발생했습니다: {e}")

    def render_news_statistics(self) -> None:
        """소식 통계 (관리자용)"""
        try:
            news_stats = self.news_service.get_news_statistics()

            st.subheader("📊 소식 통계")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("총 소식 수", f"{news_stats['total_news']}개")

            with col2:
                st.metric("고정 소식", f"{news_stats['pinned_count']}개")

            with col3:
                recent_authors = news_stats.get('recent_authors', [])
                st.metric("활성 작성자", f"{len(recent_authors)}명")

            # 카테고리별 분포
            category_counts = news_stats.get('category_counts', {})
            if category_counts:
                st.subheader("📂 카테고리별 분포")

                # 카테고리 데이터를 표시 이름으로 변환
                category_options = self.news_service.get_category_options()
                display_counts = {}
                for code, count in category_counts.items():
                    display_name = next(
                        (cat['display'] for cat in category_options if cat['code'] == code),
                        code
                    )
                    display_counts[display_name] = count

                for category, count in display_counts.items():
                    st.write(f"**{category}**: {count}개")

        except Exception as e:
            st.error(f"통계를 불러오는 중 오류가 발생했습니다: {e}")

# 페이지 인스턴스
news_page = NewsPage()