"""인증 관련 UI 컴포넌트"""
import streamlit as st
from services.auth_service import auth_service
from utils.auth_utils import is_admin_logged_in, get_current_admin, logout_admin
# from utils.session_utils import save_admin_session  # 파일 기반 세션 제거


def render_login_form():
    """관리자 로그인 폼 렌더링"""
    if is_admin_logged_in():
        return  # 이미 로그인된 경우 렌더링하지 않음

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 관리자 로그인")

    with st.sidebar.form("admin_login_form"):
        username = st.text_input("사용자명", placeholder="사용자명 입력")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
        login_button = st.form_submit_button("로그인", width="stretch")

        if login_button:
            if username and password:
                admin_info = auth_service.login(username, password)
                if admin_info:
                    # 세션 상태 설정
                    st.session_state['is_admin'] = True
                    st.session_state['admin_id'] = admin_info['id']
                    st.session_state['admin_username'] = admin_info['username']
                    st.session_state['admin_name'] = admin_info['name']
                    st.session_state['admin_role'] = admin_info['role']
                    st.session_state['admin_menu_expanded'] = False

                    st.sidebar.success(f"환영합니다, {admin_info['name']}님!")
                    st.rerun()
                else:
                    st.sidebar.error("로그인 정보가 올바르지 않습니다.")
            else:
                st.sidebar.error("사용자명과 비밀번호를 모두 입력해주세요.")


def render_admin_dropdown():
    """관리자 드롭다운 메뉴 렌더링"""
    if not is_admin_logged_in():
        render_login_form()
        return

    current_admin = get_current_admin()
    if not current_admin:
        return

    admin_name = current_admin['name']
    expanded = st.session_state.get('admin_menu_expanded', False)

    st.sidebar.markdown("---")

    # 드롭다운 토글 버튼
    toggle_icon = "⬆️" if expanded else "⬇️"
    if st.sidebar.button(f"👤 {admin_name} {toggle_icon}", width="stretch"):
        st.session_state['admin_menu_expanded'] = not expanded
        st.rerun()

    # 드롭다운 메뉴
    if expanded:
        col1, col2 = st.sidebar.columns([0.1, 0.9])

        with col2:
            if st.button("📅 일정 관리", width="stretch", key="admin_schedule"):
                st.session_state['current_page'] = 'schedule'
                st.session_state['admin_menu_expanded'] = False
                st.rerun()

            if st.button("👥 선수 관리", width="stretch", key="admin_players"):
                st.session_state['current_page'] = 'players'
                st.session_state['admin_menu_expanded'] = False
                st.rerun()

            if st.button("📈 선수 통계", width="stretch", key="admin_statistics"):
                st.session_state['current_page'] = 'statistics'
                st.session_state['admin_menu_expanded'] = False
                st.rerun()

            if st.button("💰 재정 관리", width="stretch", key="admin_finance"):
                st.session_state['current_page'] = 'finance'
                st.session_state['admin_menu_expanded'] = False
                st.rerun()

            if st.button("⚽ 팀 구성", width="stretch", key="admin_team_builder"):
                st.session_state['current_page'] = 'team_builder'
                st.session_state['admin_menu_expanded'] = False
                st.rerun()

            if st.button("📰 소식 관리", width="stretch", key="admin_news_management"):
                st.session_state['current_page'] = 'news_management'
                st.session_state['admin_menu_expanded'] = False
                st.rerun()

            if st.button("🎥 동영상 업로드", width="stretch", key="admin_video_upload"):
                st.session_state['current_page'] = 'video_upload'
                st.session_state['admin_menu_expanded'] = False
                st.rerun()

            if st.button("⚙️ 관리자 설정", width="stretch", key="admin_settings"):
                st.session_state['current_page'] = 'admin_settings'
                st.session_state['admin_menu_expanded'] = False
                st.rerun()

            st.markdown("")  # 공간 추가

            if st.button("🚪 로그아웃", width="stretch", key="admin_logout"):
                logout_admin()
                st.rerun()


def render_admin_status():
    """현재 관리자 상태 표시 (디버깅용)"""
    if is_admin_logged_in():
        current_admin = get_current_admin()
        if current_admin:
            st.sidebar.caption(f"관리자: {current_admin['name']} ({current_admin['username']})")


def render_admin_required_message():
    """관리자 로그인이 필요하다는 메시지"""
    st.error("🔐 관리자 로그인이 필요한 페이지입니다.")
    st.info("사이드바 하단의 '🔐 관리자 로그인'을 이용해 로그인해주세요.")

    st.markdown("### 관리자 계정 안내")
    st.info("관리자 계정 정보는 팀 관리자에게 문의하시기 바랍니다.")