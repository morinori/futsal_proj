"""사진 갤러리 페이지"""
import streamlit as st
import os
from services.match_service import match_service
from database.repositories import gallery_repo
from config.settings import app_config
from utils.file_security import validate_upload_file, sanitize_input, is_safe_path

class GalleryPage:
    """사진 갤러리 페이지"""

    def __init__(self):
        self.match_service = match_service
        self.gallery_repo = gallery_repo

    def render(self) -> None:
        """갤러리 페이지 렌더링"""
        st.header("📸 사진 갤러리")

        # 탭 구성
        tab1, tab2 = st.tabs(["🖼️ 갤러리", "📤 업로드"])

        with tab1:
            self._render_photo_gallery()

        with tab2:
            self._render_photo_upload()

    def _render_photo_gallery(self) -> None:
        """사진 갤러리 표시"""
        st.subheader("🖼️ 팀 사진 갤러리")

        try:
            photos = self.gallery_repo.get_all()

            if not photos:
                st.info("업로드된 사진이 없습니다.")
                return

            # 검색 및 필터
            col1, col2 = st.columns([2, 1])

            with col1:
                search_term = st.text_input("사진 검색", placeholder="제목이나 설명으로 검색...")

            with col2:
                # 경기별 필터
                matches = self.match_service.get_all_matches()
                match_filter_options = ["전체"] + [
                    f"{match['match_date']} vs {match.get('opponent', '팀내 경기')}"
                    for match in matches[:20]  # 최근 20경기
                ]
                match_filter = st.selectbox("경기별 필터", match_filter_options)

            # 필터링된 사진 목록
            filtered_photos = photos

            if search_term:
                filtered_photos = [
                    photo for photo in filtered_photos
                    if search_term.lower() in photo['title'].lower() or
                       search_term.lower() in photo['description'].lower()
                ]

            if match_filter != "전체":
                # 선택된 경기의 match_id 찾기
                selected_match_id = None
                for i, match in enumerate(matches[:20]):
                    match_display = f"{match['match_date']} vs {match.get('opponent', '팀내 경기')}"
                    if match_display == match_filter:
                        selected_match_id = match['id']
                        break

                if selected_match_id:
                    filtered_photos = [
                        photo for photo in filtered_photos
                        if photo.get('match_id') == selected_match_id
                    ]

            st.write(f"**총 {len(filtered_photos)}장의 사진**")

            # 사진 그리드 표시
            if filtered_photos:
                self._render_photo_grid(filtered_photos)
            else:
                st.info("검색 조건에 맞는 사진이 없습니다.")

        except Exception as e:
            st.error(f"갤러리를 불러오는 중 오류가 발생했습니다: {e}")

    def _render_photo_grid(self, photos: list) -> None:
        """사진 그리드 렌더링"""
        # 페이징
        photos_per_page = 12
        total_pages = (len(photos) - 1) // photos_per_page + 1

        if 'gallery_page' not in st.session_state:
            st.session_state['gallery_page'] = 1

        # 페이지 네비게이션
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                if st.session_state['gallery_page'] > 1:
                    if st.button("◀ 이전"):
                        st.session_state['gallery_page'] -= 1
                        st.rerun()

            with col2:
                st.markdown(f"<h4 style='text-align: center;'>{st.session_state['gallery_page']} / {total_pages}</h4>",
                           unsafe_allow_html=True)

            with col3:
                if st.session_state['gallery_page'] < total_pages:
                    if st.button("다음 ▶"):
                        st.session_state['gallery_page'] += 1
                        st.rerun()

        # 현재 페이지 사진 계산
        start_idx = (st.session_state['gallery_page'] - 1) * photos_per_page
        end_idx = start_idx + photos_per_page
        current_photos = photos[start_idx:end_idx]

        # 2열 그리드로 사진 표시 (모바일 대응)
        for i in range(0, len(current_photos), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(current_photos):
                    with col:
                        self._render_photo_item(current_photos[i + j])

    def _render_photo_item(self, photo: dict) -> None:
        """개별 사진 아이템 렌더링"""
        try:
            if os.path.exists(photo['file_path']):
                # 사진 표시
                st.image(photo['file_path'], width="stretch")

                # 사진 정보
                with st.expander(f"📷 {photo['title'][:20]}..."):
                    # XSS 방지를 위한 안전한 출력
                    safe_title = sanitize_input(photo['title'])
                    safe_description = sanitize_input(photo['description'] or '설명 없음')
                    upload_date = photo.get('upload_date', '미상')[:10]

                    st.write(f"**제목**: {safe_title}")
                    st.write(f"**설명**: {safe_description}")
                    st.write(f"**업로드일**: {upload_date}")

                    # 연관 경기 정보
                    if photo.get('match_id'):
                        try:
                            matches = self.match_service.get_all_matches()
                            match = next((m for m in matches if m['id'] == photo['match_id']), None)
                            if match:
                                st.write(f"**연관 경기**: {match['match_date']} vs {match.get('opponent', '팀내 경기')}")
                        except:
                            st.write("**연관 경기**: 정보 없음")

                    # 삭제 버튼
                    delete_key = f"delete_confirm_{photo['id']}"

                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False

                    if not st.session_state[delete_key]:
                        if st.button("🗑️ 삭제", key=f"delete_photo_{photo['id']}", type="secondary"):
                            st.session_state[delete_key] = True
                            st.rerun()
                    else:
                        st.warning("⚠️ 정말 삭제하시겠습니까?")
                        col_del1, col_del2 = st.columns(2)

                        with col_del1:
                            if st.button("✅ 확인", key=f"confirm_yes_{photo['id']}", type="primary"):
                                try:
                                    # 경로 보안 검증
                                    if not is_safe_path(photo['file_path'], app_config.UPLOAD_DIR):
                                        st.error("잘못된 파일 경로입니다.")
                                        st.session_state[delete_key] = False
                                        return

                                    # 파일 시스템에서 삭제
                                    if os.path.exists(photo['file_path']):
                                        os.remove(photo['file_path'])

                                    # 데이터베이스에서 삭제
                                    success = self.gallery_repo.delete(photo['id'])

                                    if success:
                                        st.success("사진이 삭제되었습니다!")
                                        st.session_state[delete_key] = False
                                        st.rerun()
                                    else:
                                        st.error("데이터베이스에서 삭제에 실패했습니다.")
                                        st.session_state[delete_key] = False
                                except Exception as e:
                                    st.error(f"사진 삭제 중 오류가 발생했습니다: {e}")
                                    st.session_state[delete_key] = False

                        with col_del2:
                            if st.button("❌ 취소", key=f"confirm_no_{photo['id']}", type="secondary"):
                                st.session_state[delete_key] = False
                                st.rerun()

            else:
                st.error(f"사진 파일을 찾을 수 없습니다: {photo['title']}")

        except Exception as e:
            st.error(f"사진을 표시하는 중 오류가 발생했습니다: {e}")

    def _render_photo_upload(self) -> None:
        """사진 업로드"""
        st.subheader("📤 사진 업로드")

        # 업로드 디렉토리 확인 및 생성
        if not os.path.exists(app_config.UPLOAD_DIR):
            try:
                os.makedirs(app_config.UPLOAD_DIR)
            except Exception as e:
                st.error(f"업로드 디렉토리를 생성할 수 없습니다: {e}")
                return

        with st.form("photo_upload_form"):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("사진 제목 *", max_chars=100)
                description = st.text_area("사진 설명", height=100, max_chars=500)

            with col2:
                # 연관 경기 선택 (선택사항)
                matches = self.match_service.get_all_matches()
                match_options = ["연관 없음"] + [
                    f"{match['match_date']} vs {match.get('opponent', '팀내 경기')}"
                    for match in matches[:20]
                ]
                selected_match = st.selectbox("연관 경기 (선택사항)", match_options)

            # 파일 업로드 (보안 강화)
            max_size_mb = app_config.MAX_FILE_SIZE // (1024 * 1024)
            allowed_types = app_config.ALLOWED_EXTENSIONS
            uploaded_file = st.file_uploader(
                "사진 파일 선택 *",
                type=allowed_types,
                help=f"{', '.join([ext.upper() for ext in allowed_types])} 형식만 업로드 가능합니다. (최대 {max_size_mb}MB)"
            )

            st.markdown("*표시된 항목은 필수입니다.")

            # 미리보기
            if uploaded_file is not None:
                st.markdown("### 📖 미리보기")
                st.image(uploaded_file, width=300)

            if st.form_submit_button("📤 업로드", type="primary"):
                if title and uploaded_file is not None:
                    try:
                        # 입력 데이터 보안 검증
                        safe_title = sanitize_input(title)
                        safe_description = sanitize_input(description) if description else ""

                        # 파일 데이터 읽기
                        file_data = uploaded_file.read()

                        # 파일 보안 검증
                        validation_result = validate_upload_file(file_data, uploaded_file.name)

                        if not validation_result['is_valid']:
                            st.error(f"파일 업로드 실패: {validation_result['error_message']}")
                            return

                        safe_filename = validation_result['safe_filename']
                        file_path = os.path.join(app_config.UPLOAD_DIR, safe_filename)

                        # 경로 보안 검증
                        if not is_safe_path(file_path, app_config.UPLOAD_DIR):
                            st.error("잘못된 파일 경로입니다.")
                            return

                        # 파일이 이미 존재하는지 확인 (중복 방지)
                        if os.path.exists(file_path):
                            existing_photo = self.gallery_repo.get_by_file_path(file_path)
                            if existing_photo:
                                st.warning("이미 동일한 사진이 업로드되어 있습니다!")
                                return

                        # 파일 저장 (보안 권한으로)
                        with open(file_path, "wb") as f:
                            f.write(file_data)
                        os.chmod(file_path, 0o644)  # 읽기 전용 권한 설정

                        # 연관 경기 ID 찾기
                        match_id = None
                        if selected_match != "연관 없음":
                            for i, match in enumerate(matches[:20]):
                                match_display = f"{match['match_date']} vs {match.get('opponent', '팀내 경기')}"
                                if match_display == selected_match:
                                    match_id = match['id']
                                    break

                        # 데이터베이스에 저장 (정화된 데이터 사용)
                        success = self.gallery_repo.create(safe_title, safe_description, file_path, match_id)

                        if success:
                            st.success("사진이 성공적으로 업로드되었습니다!")
                            st.rerun()
                        else:
                            st.error("사진 업로드에 실패했습니다.")

                    except Exception as e:
                        st.error(f"업로드 중 오류가 발생했습니다: {e}")
                else:
                    st.error("사진 제목과 파일을 모두 입력해주세요.")

    def render_gallery_summary(self) -> None:
        """갤러리 요약 (대시보드용)"""
        try:
            photos = self.gallery_repo.get_all()

            if photos:
                st.subheader("📸 최근 사진")

                # 최근 사진 4장 표시
                recent_photos = photos[:4]
                cols = st.columns(4)

                for i, photo in enumerate(recent_photos):
                    with cols[i]:
                        if os.path.exists(photo['file_path']):
                            st.image(photo['file_path'], width="stretch")
                            # XSS 방지를 위한 안전한 출력
                            safe_title = sanitize_input(photo['title'])
                            display_title = safe_title[:15] + "..." if len(safe_title) > 15 else safe_title
                            st.caption(display_title)
                        else:
                            st.warning("이미지 없음")

                # 더 보기 버튼
                if len(photos) > 4:
                    if st.button("📸 모든 사진 보기"):
                        st.session_state['current_page'] = "갤러리"
                        st.rerun()

            else:
                st.info("업로드된 사진이 없습니다.")

        except Exception as e:
            st.error(f"갤러리 요약을 불러오는 중 오류가 발생했습니다: {e}")

    def render_gallery_stats(self) -> None:
        """갤러리 통계"""
        try:
            photos = self.gallery_repo.get_all()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("총 사진 수", f"{len(photos)}장")

            with col2:
                # 이번 달 업로드된 사진 수
                from datetime import datetime
                current_month = datetime.now().strftime('%Y-%m')
                this_month_photos = [
                    photo for photo in photos
                    if photo.get('upload_date', '').startswith(current_month)
                ]
                st.metric("이번 달 업로드", f"{len(this_month_photos)}장")

            with col3:
                # 경기 연관 사진 수
                match_photos = [photo for photo in photos if photo.get('match_id')]
                st.metric("경기 관련 사진", f"{len(match_photos)}장")

        except Exception as e:
            st.error(f"갤러리 통계를 불러오는 중 오류가 발생했습니다: {e}")

# 페이지 인스턴스
gallery_page = GalleryPage()