"""
Streamlit 풋살팀 플랫폼 - 메인 애플리케이션
UI 계층 리팩토링 완료 버전
"""
import streamlit as st
import streamlit.components.v1 as components
import logging

# 설정 import
from config.settings import ui_config

# 페이지 import
from ui.pages import (
    dashboard_page,
    schedule_page,
    players_page,
    statistics_page,
    attendance_page,
    news_page,
    gallery_page,
    finance_page,
    admin_settings,
    video_upload,
    video_gallery,
    news_management,
    video_logs
)

# 인증 컴포넌트 import
from ui.components.auth import render_admin_dropdown
from utils.auth_utils import is_admin_logged_in

# 데이터베이스 초기화
from database.migrations import init_complete_db

# 페이지 설정
st.set_page_config(
    page_title=ui_config.PAGE_TITLE,
    layout=ui_config.LAYOUT,
    initial_sidebar_state=ui_config.SIDEBAR_STATE,
    page_icon="⚽"
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CSS 스타일 및 모바일 사이드바 제어
st.markdown("""
<style>
/* =================
   Design Token System
   ================= */
:root {
    /* Primary Colors - 풋살 그린 테마 */
    --primary-50: #e8f5e8;
    --primary-100: #c8e6c8;
    --primary-200: #a5d6a5;
    --primary-300: #81c784;
    --primary-400: #66bb6a;
    --primary-500: #4CAF50;  /* 메인 브랜드 컬러 */
    --primary-600: #43a047;
    --primary-700: #388e3c;
    --primary-800: #2e7d32;
    --primary-900: #1b5e20;

    /* Neutral Colors */
    --gray-50: #f8f9fa;
    --gray-100: #e9ecef;
    --gray-200: #dee2e6;
    --gray-300: #ced4da;
    --gray-400: #adb5bd;
    --gray-500: #6c757d;
    --gray-600: #495057;
    --gray-700: #343a40;
    --gray-800: #212529;
    --gray-900: #121212;

    /* Semantic Colors */
    --success: #28a745;
    --success-light: #d4edda;
    --warning: #ffc107;
    --warning-light: #fff3cd;
    --error: #dc3545;
    --error-light: #f8d7da;
    --info: #17a2b8;
    --info-light: #d1ecf1;

    /* Typography Scale */
    --font-size-xs: 0.75rem;    /* 12px */
    --font-size-sm: 0.875rem;   /* 14px */
    --font-size-base: 1rem;     /* 16px */
    --font-size-lg: 1.125rem;   /* 18px */
    --font-size-xl: 1.25rem;    /* 20px */
    --font-size-2xl: 1.5rem;    /* 24px */
    --font-size-3xl: 1.875rem;  /* 30px */

    /* Font Weights */
    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;

    /* Spacing Scale */
    --space-1: 0.25rem;   /* 4px */
    --space-2: 0.5rem;    /* 8px */
    --space-3: 0.75rem;   /* 12px */
    --space-4: 1rem;      /* 16px */
    --space-5: 1.25rem;   /* 20px */
    --space-6: 1.5rem;    /* 24px */
    --space-8: 2rem;      /* 32px */
    --space-10: 2.5rem;   /* 40px */
    --space-12: 3rem;     /* 48px */

    /* Border Radius */
    --radius-none: 0;
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;

    /* Shadows */
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 25px rgba(0,0,0,0.15), 0 4px 10px rgba(0,0,0,0.1);
    --shadow-xl: 0 20px 40px rgba(0,0,0,0.2);

    /* Z-index Scale */
    --z-dropdown: 1000;
    --z-sticky: 1020;
    --z-fixed: 1030;
    --z-modal: 1040;
    --z-popover: 1050;
    --z-tooltip: 1060;

    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-base: 200ms ease;
    --transition-slow: 300ms ease;
}

/* 메인 헤더 - 디자인 토큰 적용 */
.main-header {
    background: linear-gradient(90deg, var(--primary-500), var(--primary-700));
    padding: var(--space-6);
    border-radius: var(--radius-lg);
    color: white;
    text-align: center;
    margin-bottom: var(--space-8);
    box-shadow: var(--shadow-md);
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-semibold);
}

/* Streamlit 불필요한 요소만 숨기기 (메뉴는 보이게) */
.stDeployButton,
.viewerBadge_container__1QSob,
.styles_viewerBadge__1yB5_,
[data-testid="stDecoration"],
.stActionButton {
    display: none !important;
}

/* 상단 여백 - 상단바가 제목을 가리지 않도록 충분한 여백 확보 */
.stMainBlockContainer {
    padding-top: 3rem !important;
}

/* 메인 콘텐츠 블록에 추가 여백 */
.main .block-container {
    padding-top: 2rem !important;
}

/* 모바일 최적화 - 사이드바 간섭 없음 */

/* =================
   Component System
   ================= */

/* Sidebar - 디자인 토큰 적용 */
.sidebar .sidebar-content {
    background: linear-gradient(180deg, var(--gray-50), var(--gray-100));
}

/* Card System */
.metric-container, .card {
    background: white;
    padding: var(--space-6);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    margin: var(--space-3) 0;
    border: 1px solid var(--gray-100);
}

.card-header {
    border-bottom: 1px solid var(--gray-200);
    padding-bottom: var(--space-4);
    margin-bottom: var(--space-4);
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--gray-800);
}

/* Status Boxes - 시맨틱 컬러 적용 */
.success-box, .alert-success {
    background-color: var(--success-light);
    border: 1px solid var(--success);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    margin: var(--space-4) 0;
    color: var(--gray-800);
    border-left: 4px solid var(--success);
}

.warning-box, .alert-warning {
    background-color: var(--warning-light);
    border: 1px solid var(--warning);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    margin: var(--space-4) 0;
    color: var(--gray-800);
    border-left: 4px solid var(--warning);
}

.error-box, .alert-error {
    background-color: var(--error-light);
    border: 1px solid var(--error);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    margin: var(--space-4) 0;
    color: var(--gray-800);
    border-left: 4px solid var(--error);
}

.info-box, .alert-info {
    background-color: var(--info-light);
    border: 1px solid var(--info);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    margin: var(--space-4) 0;
    color: var(--gray-800);
    border-left: 4px solid var(--info);
}

/* Button System - 통일된 버튼 스타일 */
.stButton > button, .btn {
    background: var(--primary-500) !important;
    color: white !important;
    border: none !important;
    padding: var(--space-3) var(--space-6) !important;
    border-radius: var(--radius-md) !important;
    font-size: var(--font-size-base) !important;
    font-weight: var(--font-weight-medium) !important;
    cursor: pointer !important;
    transition: all var(--transition-base) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stButton > button:hover, .btn:hover {
    background: var(--primary-600) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
}

.stButton > button:active, .btn:active {
    transform: translateY(0) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* 버튼 변형 - Primary/Secondary/Danger */
.btn-primary {
    background: var(--primary-500) !important;
}

.btn-primary:hover {
    background: var(--primary-600) !important;
}

.btn-secondary {
    background: var(--gray-500) !important;
    color: white !important;
}

.btn-secondary:hover {
    background: var(--gray-600) !important;
}

.btn-success {
    background: var(--success) !important;
}

.btn-success:hover {
    background: #218838 !important;
}

.btn-warning {
    background: var(--warning) !important;
    color: var(--gray-800) !important;
}

.btn-warning:hover {
    background: #e0a800 !important;
}

.btn-danger, .btn-error {
    background: var(--error) !important;
}

.btn-danger:hover, .btn-error:hover {
    background: #c82333 !important;
}

/* Tab System - 디자인 토큰 적용 */
.stTabs [data-baseweb="tab-list"] {
    gap: var(--space-2);
    background: var(--gray-50);
    padding: var(--space-1);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-6);
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    background-color: transparent;
    border-radius: var(--radius-md);
    padding: var(--space-3) var(--space-6);
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    color: var(--gray-600);
    transition: all var(--transition-base);
    border: none;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: var(--gray-100);
    color: var(--gray-800);
}

.stTabs [aria-selected="true"] {
    background: var(--primary-500) !important;
    color: white !important;
    box-shadow: var(--shadow-sm);
    transform: translateY(-1px);
}

/* =================
   Attendance Status System
   ================= */

/* 출석 상태 배지 */
.attendance-status {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-full);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-semibold);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.status-present {
    background: linear-gradient(135deg, #28a745, #20c997);
    color: white;
    box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
}

.status-absent {
    background: linear-gradient(135deg, #dc3545, #e74c3c);
    color: white;
    box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
}

.status-pending {
    background: linear-gradient(135deg, #ffc107, #f39c12);
    color: var(--gray-800);
    box-shadow: 0 2px 4px rgba(255, 193, 7, 0.3);
}

/* 출석 상태 카드 */
.attendance-card {
    background: white;
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--gray-100);
    transition: all var(--transition-base);
}

.attendance-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--primary-200);
}

/* 출석률 진행바 */
.attendance-progress {
    width: 100%;
    height: 12px;
    background: var(--gray-200);
    border-radius: var(--radius-full);
    overflow: hidden;
    position: relative;
}

.attendance-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--primary-400), var(--primary-600));
    border-radius: var(--radius-full);
    transition: width var(--transition-slow);
    position: relative;
}

.attendance-progress-bar::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* 출석 통계 매트릭 */
.attendance-metric {
    text-align: center;
    padding: var(--space-4);
}

.attendance-metric-value {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--primary-600);
    display: block;
}

.attendance-metric-label {
    font-size: var(--font-size-sm);
    color: var(--gray-600);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: var(--space-2);
}

/* 출석 변경 버튼 그룹 */
.attendance-buttons {
    display: flex;
    gap: var(--space-3);
    margin-top: var(--space-4);
}

.attendance-btn {
    flex: 1;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-md);
    border: 2px solid transparent;
    font-weight: var(--font-weight-semibold);
    transition: all var(--transition-base);
    cursor: pointer;
}

.attendance-btn-present {
    background: var(--success-light);
    color: var(--success);
    border-color: var(--success);
}

.attendance-btn-present:hover {
    background: var(--success);
    color: white;
}

.attendance-btn-absent {
    background: var(--error-light);
    color: var(--error);
    border-color: var(--error);
}

.attendance-btn-absent:hover {
    background: var(--error);
    color: white;
}

.attendance-btn-pending {
    background: var(--warning-light);
    color: var(--warning);
    border-color: var(--warning);
}

.attendance-btn-pending:hover {
    background: var(--warning);
    color: var(--gray-800);
}
</style>

<script>
// 사이드바 간섭 제거됨 - Streamlit 기본 동작 유지
</script>
""", unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태 초기화"""
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "dashboard"

    # 만료된 세션 파일 정리 (성능상 가끔씩만 실행)
    import random
    if random.randint(1, 100) <= 5:  # 5% 확률로 실행
        from utils.session_utils import cleanup_expired_sessions
        cleanup_expired_sessions()


def inject_mobile_sidebar_control():
    """모바일에서 사이드바 자동 닫기 (iframe 없는 방식)"""
    # iframe을 사용하지 않고 기존 CSS 스타일에 JavaScript 포함
    pass  # CSS 내부의 JavaScript가 처리함

def get_available_pages():
    """로그인 상태에 따른 접근 가능 페이지 반환"""
    public_pages = {
        "🏠 메인 대시보드": "dashboard",
        "📋 출석 관리": "attendance",
        "📰 팀 소식": "news",
        "📸 갤러리": "gallery",
    }

    admin_pages = {
        "📅 일정 관리": "schedule",
        "👥 선수 관리": "players",
        "📈 선수 통계": "statistics",
        "💰 재정 관리": "finance",
        "📰 소식 관리": "news_management",
        "📊 비디오 로그": "video_logs",
        "⚙️ 관리자 설정": "admin_settings",
    }

    if is_admin_logged_in():
        return {**public_pages, **admin_pages}
    else:
        return public_pages

def render_sidebar():
    """사이드바 렌더링"""
    st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2>⚽ SGSC</h2>
    </div>
    """, unsafe_allow_html=True)

    # 일반 사용자 페이지
    public_pages = {
        "🏠 메인 대시보드": "dashboard",
        "📋 출석 관리": "attendance",
        "📰 팀 소식": "news",
        "📸 갤러리": "gallery",
        "🎬 동영상": "video_gallery",
    }

    st.sidebar.markdown("### 📋 메뉴")

    for display_name, page_name in public_pages.items():
        if st.sidebar.button(display_name, key=f"nav_{page_name}", width="stretch"):
            st.session_state['current_page'] = page_name
            st.rerun()

    # 관리자 드롭다운 (로그인 폼 또는 관리자 메뉴)
    render_admin_dropdown()

    # 현재 선택된 페이지 표시
    current_page = st.session_state.get('current_page', 'dashboard')
    page_display_name = get_page_display_name(current_page)
    st.sidebar.markdown(f"**현재 페이지**: {page_display_name}")

def get_page_display_name(page_name):
    """페이지 내부명을 표시명으로 변환"""
    page_names = {
        "dashboard": "메인 대시보드",
        "statistics": "선수 통계",
        "attendance": "출석 관리",
        "news": "팀 소식",
        "gallery": "갤러리",
        "video_gallery": "동영상 갤러리",
        "schedule": "일정 관리",
        "players": "선수 관리",
        "finance": "재정 관리",
        "news_management": "소식 관리",
        "video_upload": "동영상 업로드",
        "video_logs": "비디오 로그",
        "admin_settings": "관리자 설정",
    }
    return page_names.get(page_name, page_name)

def render_main_content():
    """메인 콘텐츠 렌더링"""
    current_page = st.session_state.get('current_page', 'dashboard')

    # 페이지명 정규화 (한글 -> 영문)
    page_mapping = {
        "대시보드": "dashboard",
        "선수 통계": "statistics",
        "출석 관리": "attendance",
        "팀 소식": "news",
        "갤러리": "gallery",
        "일정 관리": "schedule",
        "선수 관리": "players",
        "팀 재정": "finance",
        "재정 관리": "finance"  # 추가된 매핑
    }

    normalized_page = page_mapping.get(current_page, current_page)

    try:
        if normalized_page == "dashboard":
            dashboard_page.render()
        elif normalized_page == "statistics":
            statistics_page.render()
        elif normalized_page == "attendance":
            attendance_page.render()
        elif normalized_page == "news":
            news_page.render()
        elif normalized_page == "gallery":
            gallery_page.render()
        elif normalized_page == "video_gallery":
            video_gallery.render_video_gallery_page()
        elif normalized_page == "schedule":
            schedule_page.render()
        elif normalized_page == "players":
            players_page.render()
        elif normalized_page == "finance":
            finance_page.render()
        elif normalized_page == "news_management":
            news_management.news_management_page.render()
        elif normalized_page == "video_upload":
            video_upload.render_video_upload_page()
        elif normalized_page == "video_logs":
            video_logs.render_video_logs_page()
        elif normalized_page == "admin_settings":
            admin_settings.render()
        else:
            st.error(f"알 수 없는 페이지: {current_page}")
            logger.warning(f"Unknown page requested: {current_page}")

    except Exception as e:
        st.error(f"페이지를 불러오는 중 오류가 발생했습니다: {e}")
        logger.error(f"Error rendering page {normalized_page}: {e}", exc_info=True)

def render_footer():
    """푸터 렌더링"""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🏗️ 아키텍처**")
        st.caption("• Repository Pattern")
        st.caption("• Service Layer")
        st.caption("• UI Component 분리")

    with col2:
        st.markdown("**⚡ 성능**")
        st.caption("• 관심사 분리")
        st.caption("• 모듈화 설계")
        st.caption("• 재사용 가능한 컴포넌트")

    with col3:
        st.markdown("**🔧 기술 스택**")
        st.caption("• Streamlit")
        st.caption("• SQLite")
        st.caption("• Plotly")

def check_database():
    """데이터베이스 초기화 확인 (최초 1회만)"""
    if 'db_initialized' not in st.session_state:
        try:
            init_complete_db()
            st.session_state['db_initialized'] = True
            logger.info("Database initialized successfully")
        except Exception as e:
            st.error(f"데이터베이스 초기화 실패: {e}")
            logger.error(f"Database initialization failed: {e}")

def main():
    """메인 애플리케이션"""

    # 데이터베이스 초기화 (최초 1회만)
    check_database()

    # 세션 상태 초기화
    initialize_session_state()

    # 모바일 사이드바 제어 제거됨

    # 사이드바 렌더링
    render_sidebar()

    # 메인 콘텐츠 렌더링
    render_main_content()

    # 푸터 렌더링
    #render_footer()

if __name__ == "__main__":
    main()