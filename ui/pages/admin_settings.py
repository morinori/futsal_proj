"""관리자 설정 페이지"""
import streamlit as st
from utils.auth_utils import require_admin_access, get_current_admin
from services.auth_service import auth_service


def render():
    """관리자 설정 페이지 렌더링"""
    require_admin_access()

    st.header("⚙️ 관리자 설정")

    current_admin = get_current_admin()
    if not current_admin:
        st.error("관리자 정보를 불러올 수 없습니다.")
        return

    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["👥 관리자 목록", "➕ 새 관리자 추가", "🔒 비밀번호 변경"])

    with tab1:
        render_admin_list()

    with tab2:
        render_add_admin_form()

    with tab3:
        render_change_password_form(current_admin)


def render_admin_list():
    """관리자 목록 표시"""
    st.subheader("👥 현재 관리자 목록")

    try:
        admins = auth_service.get_all_admins()

        if not admins:
            st.info("등록된 관리자가 없습니다.")
            return

        for idx, admin in enumerate(admins):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

            with col1:
                st.text(admin['name'])

            with col2:
                st.text(admin['username'])

            with col3:
                st.text(admin['role'])

            with col4:
                current_admin = get_current_admin()
                # 본인은 비활성화 불가
                if admin['id'] != current_admin['id']:
                    if st.button("🚫", key=f"deactivate_{admin['id']}", help="비활성화"):
                        if st.session_state.get(f'confirm_deactivate_{admin["id"]}', False):
                            if auth_service.deactivate_admin(admin['id']):
                                st.success(f"{admin['name']} 관리자가 비활성화되었습니다.")
                                st.rerun()
                            else:
                                st.error("비활성화에 실패했습니다.")
                            st.session_state[f'confirm_deactivate_{admin["id"]}'] = False
                        else:
                            st.session_state[f'confirm_deactivate_{admin["id"]}'] = True
                            st.warning(f"{admin['name']} 관리자를 비활성화하시겠습니까? 다시 버튼을 클릭해주세요.")

        # 헤더 추가
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.caption("**이름**")
        with col2:
            st.caption("**사용자명**")
        with col3:
            st.caption("**역할**")
        with col4:
            st.caption("**관리**")

    except Exception as e:
        st.error(f"관리자 목록을 불러오는데 실패했습니다: {str(e)}")


def render_add_admin_form():
    """새 관리자 추가 폼"""
    st.subheader("➕ 새 관리자 계정 추가")

    with st.form("add_admin_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input(
                "사용자명",
                placeholder="영문, 숫자 조합",
                help="로그인시 사용할 사용자명"
            )
            name = st.text_input(
                "실명",
                placeholder="홍길동",
                help="실제 이름 또는 별명"
            )

        with col2:
            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="8자 이상 권장",
                help="안전한 비밀번호를 설정해주세요"
            )
            password_confirm = st.text_input(
                "비밀번호 확인",
                type="password",
                placeholder="비밀번호 재입력"
            )

        role = st.selectbox(
            "역할",
            ["admin", "manager", "captain"],
            help="관리자 권한 레벨"
        )

        submitted = st.form_submit_button("관리자 추가", width="stretch")

        if submitted:
            # 입력 검증
            if not all([username, name, password, password_confirm]):
                st.error("모든 필드를 입력해주세요.")
                return

            if password != password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
                return

            if len(password) < 6:
                st.error("비밀번호는 최소 6자 이상이어야 합니다.")
                return

            # 관리자 생성
            try:
                success = auth_service.create_admin(username, password, name, role)
                if success:
                    st.success(f"✅ {name} 관리자 계정이 성공적으로 생성되었습니다!")
                    st.info(f"**로그인 정보**\n- 사용자명: `{username}`\n- 비밀번호: [생성한 비밀번호를 사용하세요]")

                    # 폼 초기화를 위해 rerun
                    st.balloons()
                else:
                    st.error("관리자 계정 생성에 실패했습니다. 사용자명이 이미 존재할 수 있습니다.")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")


def render_change_password_form(current_admin):
    """비밀번호 변경 폼"""
    st.subheader("🔒 비밀번호 변경")
    st.info(f"현재 로그인: **{current_admin['name']}** ({current_admin['username']})")

    with st.form("change_password_form"):
        old_password = st.text_input(
            "현재 비밀번호",
            type="password",
            placeholder="현재 사용중인 비밀번호"
        )

        col1, col2 = st.columns(2)
        with col1:
            new_password = st.text_input(
                "새 비밀번호",
                type="password",
                placeholder="새로운 비밀번호"
            )
        with col2:
            new_password_confirm = st.text_input(
                "새 비밀번호 확인",
                type="password",
                placeholder="새 비밀번호 재입력"
            )

        submitted = st.form_submit_button("비밀번호 변경", width="stretch")

        if submitted:
            # 입력 검증
            if not all([old_password, new_password, new_password_confirm]):
                st.error("모든 필드를 입력해주세요.")
                return

            if new_password != new_password_confirm:
                st.error("새 비밀번호가 일치하지 않습니다.")
                return

            if len(new_password) < 6:
                st.error("새 비밀번호는 최소 6자 이상이어야 합니다.")
                return

            if old_password == new_password:
                st.error("새 비밀번호는 현재 비밀번호와 달라야 합니다.")
                return

            # 비밀번호 변경
            try:
                success = auth_service.change_password(
                    current_admin['id'],
                    old_password,
                    new_password
                )

                if success:
                    st.success("✅ 비밀번호가 성공적으로 변경되었습니다!")
                    st.info("보안을 위해 다시 로그인해주세요.")
                else:
                    st.error("비밀번호 변경에 실패했습니다. 현재 비밀번호를 확인해주세요.")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    render()