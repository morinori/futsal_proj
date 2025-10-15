"""팀 소식 관리 페이지 (관리자 전용)"""
import streamlit as st
from services.news_service import news_service
from utils.auth_utils import require_admin_access

class NewsManagementPage:
    """팀 소식 관리 페이지"""

    def __init__(self):
        self.news_service = news_service

    def render(self) -> None:
        """팀 소식 관리 페이지 렌더링"""
        # 관리자 권한 확인
        if not require_admin_access():
            return

        st.header("📰 소식 관리")

        # 탭 구성
        tab1, tab2 = st.tabs(["✍️ 소식 작성", "📋 소식 관리"])

        with tab1:
            self._render_news_editor()

        with tab2:
            self._render_news_manager()

    def _render_news_editor(self) -> None:
        """소식 작성 에디터"""
        st.subheader("✍️ 새 소식 작성")

        # 중복 제출 방지: 제출 완료 플래그 확인 및 리셋
        if st.session_state.get('news_submitted', False):
            st.session_state.news_submitted = False
            st.success("소식이 성공적으로 게시되었습니다!")
            # 폼을 다시 렌더링하기 위해 계속 진행

        with st.form("news_form"):
            # 제목
            title = st.text_input("제목 *", max_chars=100)

            # 내용
            content = st.text_area("내용 *", height=200, max_chars=5000)

            col1, col2, col3 = st.columns(3)

            with col1:
                # 관리자 이름을 기본 작성자로 설정
                default_author = st.session_state.get('admin_name', '')
                author = st.text_input("작성자 *", value=default_author, max_chars=20)

            with col2:
                category_options = self.news_service.get_category_options()
                category = st.selectbox(
                    "카테고리",
                    [cat['code'] for cat in category_options],
                    format_func=lambda x: next(
                        (cat['display'] for cat in category_options if cat['code'] == x), x
                    )
                )

            with col3:
                pinned = st.checkbox("📌 상단 고정", help="중요한 소식은 상단에 고정할 수 있습니다.")

            st.markdown("*표시된 항목은 필수입니다.")

            # 미리보기
            if title or content:
                st.markdown("### 📖 미리보기")
                if title:
                    st.markdown(f"**{title}**")
                if content:
                    # 개행 처리: \n을 <br>로 변환
                    content_with_br = content.replace('\n', '<br>')
                    st.markdown(content_with_br, unsafe_allow_html=True)

            if st.form_submit_button("📰 소식 게시", type="primary"):
                if title and content and author:
                    try:
                        success = self.news_service.create_news(
                            title=title,
                            content=content,
                            author=author,
                            pinned=pinned,
                            category=category
                        )

                        if success:
                            # 중복 제출 방지: 플래그 설정 후 rerun
                            st.session_state.news_submitted = True
                            st.rerun()
                        else:
                            st.error("소식 게시에 실패했습니다.")

                    except ValueError as e:
                        st.error(f"입력 오류: {e}")
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
                else:
                    st.error("제목, 내용, 작성자는 필수 항목입니다.")

    def _render_news_manager(self) -> None:
        """소식 관리 (수정/삭제/고정)"""
        st.subheader("📋 소식 관리")

        # 수정 모드 확인
        if 'editing_news_id' in st.session_state and st.session_state.editing_news_id:
            self._render_news_edit_form()
            return

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
                        self._render_news_item_with_actions(news, is_pinned=True)

                if regular_news:
                    st.markdown("### 📰 일반 소식")
                    for news in regular_news:
                        self._render_news_item_with_actions(news, is_pinned=False)

            else:
                st.info("소식이 없습니다.")

        except Exception as e:
            st.error(f"소식을 불러오는 중 오류가 발생했습니다: {e}")

    def _render_news_item_with_actions(self, news: dict, is_pinned: bool = False) -> None:
        """개별 소식 아이템 + 관리 버튼"""
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
            # 개행 처리: \n을 <br>로 변환
            content_with_br = news['content'].replace('\n', '<br>')
            st.markdown(content_with_br, unsafe_allow_html=True)

            # 관리 버튼들
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📝 수정", key=f"edit_{news['id']}", help="소식 수정"):
                    st.session_state.editing_news_id = news['id']
                    st.rerun()

            with col2:
                if st.button("🗑️ 삭제", key=f"delete_{news['id']}", help="소식 삭제"):
                    try:
                        success = self.news_service.delete_news(news['id'])
                        if success:
                            st.success("소식이 삭제되었습니다.")
                            st.rerun()
                        else:
                            st.error("삭제에 실패했습니다.")
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")

            with col3:
                pin_text = "📌 고정 해제" if news['pinned'] else "📌 고정하기"
                if st.button(pin_text, key=f"pin_{news['id']}", help="고정 상태 변경"):
                    try:
                        success = self.news_service.toggle_pinned(news['id'])
                        if success:
                            st.success("고정 상태가 변경되었습니다.")
                            st.rerun()
                        else:
                            st.error("변경에 실패했습니다.")
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")

    def _render_news_edit_form(self) -> None:
        """소식 수정 폼"""
        news_id = st.session_state.editing_news_id
        news = self.news_service.get_news_by_id(news_id)

        if not news:
            st.error("소식을 찾을 수 없습니다.")
            st.session_state.editing_news_id = None
            st.rerun()
            return

        st.subheader(f"📝 소식 수정 - {news['title']}")

        with st.form("news_edit_form"):
            # 제목
            title = st.text_input("제목 *", value=news['title'], max_chars=100)

            # 내용
            content = st.text_area("내용 *", value=news['content'], height=200, max_chars=5000)

            col1, col2, col3 = st.columns(3)

            with col1:
                author = st.text_input("작성자 *", value=news['author'], max_chars=20)

            with col2:
                category_options = self.news_service.get_category_options()
                current_category_index = next(
                    (i for i, cat in enumerate(category_options) if cat['code'] == news['category']), 0
                )
                category = st.selectbox(
                    "카테고리",
                    [cat['code'] for cat in category_options],
                    index=current_category_index,
                    format_func=lambda x: next(
                        (cat['display'] for cat in category_options if cat['code'] == x), x
                    )
                )

            with col3:
                pinned = st.checkbox("📌 상단 고정", value=news['pinned'], help="중요한 소식은 상단에 고정할 수 있습니다.")

            st.markdown("*표시된 항목은 필수입니다.")

            # 미리보기
            if title or content:
                st.markdown("### 📖 미리보기")
                if title:
                    st.markdown(f"**{title}**")
                if content:
                    # 개행 처리: \n을 <br>로 변환
                    content_with_br = content.replace('\n', '<br>')
                    st.markdown(content_with_br, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 수정 저장", type="primary"):
                    if title and content and author:
                        try:
                            success = self.news_service.update_news(
                                news_id=news_id,
                                title=title,
                                content=content,
                                author=author,
                                pinned=pinned,
                                category=category
                            )

                            if success:
                                st.success("소식이 성공적으로 수정되었습니다!")
                                st.session_state.editing_news_id = None
                                st.rerun()
                            else:
                                st.error("소식 수정에 실패했습니다.")

                        except ValueError as e:
                            st.error(f"입력 오류: {e}")
                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {e}")
                    else:
                        st.error("제목, 내용, 작성자는 필수 항목입니다.")

            with col2:
                if st.form_submit_button("❌ 취소"):
                    st.session_state.editing_news_id = None
                    st.rerun()

# 페이지 인스턴스
news_management_page = NewsManagementPage()