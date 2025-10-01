"""인증 유틸리티"""
import streamlit as st
from datetime import datetime, timedelta
from utils.session_utils import restore_admin_session, clear_admin_session


def require_admin_access():
    """관리자 전용 페이지 권한 체크"""
    if not st.session_state.get('is_admin', False):
        st.error("🔐 관리자 로그인이 필요한 페이지입니다.")
        st.info("사이드바 하단의 '관리자 로그인'을 클릭해주세요.")
        st.stop()
    return True


def is_admin_logged_in() -> bool:
    """관리자 로그인 여부 확인 - Streamlit 세션만 사용"""
    # 현재 세션 상태만 확인 (파일 기반 세션 제거)
    if st.session_state.get('is_admin', False):
        # 기본적인 세션 무결성 검증
        required_keys = ['admin_id', 'admin_username', 'admin_name']
        for key in required_keys:
            if not st.session_state.get(key):
                # 세션이 손상된 경우 로그아웃 처리
                logout_admin()
                return False

        # 세션 타임아웃 체크 (30분)
        last_activity = st.session_state.get('last_activity')
        if last_activity:
            try:
                last_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_time > timedelta(minutes=30):
                    logout_admin()
                    return False
            except:
                pass

        # 활동 시간 업데이트
        st.session_state['last_activity'] = datetime.now().isoformat()
        return True

    return False


def get_current_admin():
    """현재 로그인된 관리자 정보 반환"""
    if not is_admin_logged_in():
        return None

    return {
        'id': st.session_state.get('admin_id'),
        'username': st.session_state.get('admin_username'),
        'name': st.session_state.get('admin_name'),
        'role': st.session_state.get('admin_role', 'admin')
    }


def logout_admin():
    """관리자 로그아웃 처리 - Streamlit 세션만 정리"""
    # Streamlit 세션 상태만 정리 (각 브라우저별 독립적)
    admin_keys = [
        'is_admin',
        'admin_id',
        'admin_username',
        'admin_name',
        'admin_role',
        'admin_menu_expanded',
        'last_activity'
    ]

    for key in admin_keys:
        if key in st.session_state:
            del st.session_state[key]

    # 메인 페이지로 리다이렉트
    st.session_state['current_page'] = 'dashboard'