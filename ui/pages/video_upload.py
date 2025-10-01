"""동영상 업로드 페이지 (관리자 전용)"""
import streamlit as st
from pathlib import Path
from services.video_service import VideoService
from database.repositories import video_repo, match_repo
from database.models import Video
from utils.auth_utils import require_admin_access
import logging

logger = logging.getLogger(__name__)

def render_video_upload_page():
    """동영상 업로드 페이지 렌더링"""
    # 관리자 권한 확인
    require_admin_access()

    st.title("🎥 동영상 업로드")
    st.write("경기 영상을 업로드하면 자동으로 HLS 스트리밍으로 변환됩니다.")

    # 비디오 서비스 초기화
    video_service = VideoService()

    # 업로드 폼
    with st.form("video_upload_form"):
        st.subheader("📤 동영상 업로드")

        # 제목
        title = st.text_input("제목*", placeholder="예: 2024년 봄 리그 결승전")

        # 설명
        description = st.text_area("설명", placeholder="동영상에 대한 설명을 입력하세요")

        # 경기 선택 (선택사항)
        matches = match_repo.get_all()
        match_options = ["선택 안함"] + [
            f"{m['match_date']} {m['match_time']} - {m['opponent'] or '팀내 경기'} @ {m.get('field_name', '미정')}"
            for m in matches
        ]
        match_ids = [None] + [m['id'] for m in matches]

        selected_match_idx = st.selectbox(
            "연결할 경기 (선택사항)",
            range(len(match_options)),
            format_func=lambda x: match_options[x]
        )
        selected_match_id = match_ids[selected_match_idx]

        # 파일 업로드
        uploaded_file = st.file_uploader(
            "동영상 파일 선택*",
            type=['mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v'],
            help="최대 2GB까지 업로드 가능합니다."
        )

        # 업로드 버튼
        submit_button = st.form_submit_button("🚀 업로드 및 자동 처리 시작", width="stretch")

        if submit_button:
            # 필수 필드 검증
            if not title:
                st.error("제목을 입력해주세요.")
            elif not uploaded_file:
                st.error("동영상 파일을 선택해주세요.")
            else:
                # 업로드 및 처리 시작
                process_video_upload(
                    video_service,
                    uploaded_file,
                    title,
                    description,
                    selected_match_id
                )

    # 구분선
    st.divider()

    # 업로드된 동영상 목록
    render_uploaded_videos_list()


def process_video_upload(video_service: VideoService, uploaded_file, title: str,
                        description: str, match_id: int = None):
    """동영상 업로드 및 자동 처리"""

    # 진행 상태 표시
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 1단계: 메타데이터 생성
        status_text.text("📝 동영상 메타데이터 생성 중...")
        progress_bar.progress(10)

        admin_id = st.session_state.get('admin_id')

        video = Video(
            title=title,
            description=description,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            status='pending',
            match_id=match_id,
            uploaded_by=admin_id
        )

        video_id = video_repo.create(video)

        if not video_id:
            st.error("❌ 동영상 메타데이터 생성 실패")
            return

        progress_bar.progress(20)

        # 2단계: 상태를 processing으로 변경
        status_text.text("⚙️ 동영상 처리 시작...")
        video_repo.update_processing_status(video_id, 'processing')
        progress_bar.progress(30)

        # 3단계: 완전 자동 처리 (업로드 → 트랜스코딩 → 썸네일)
        status_text.text("🎬 동영상 자동 처리 중 (업로드 → HLS 변환 → 썸네일 생성)...")
        status_text.caption("⚠️ 이 작업은 동영상 길이에 따라 수 분이 소요될 수 있습니다.")

        result = video_service.process_video_complete(uploaded_file, video_id)

        progress_bar.progress(90)

        # 4단계: 결과 처리
        if result['success']:
            # DB 업데이트
            logger.info(f"Updating video {video_id} status to completed")
            logger.info(f"HLS path: {result['hls_path']}")
            logger.info(f"Thumbnail path: {result['thumbnail_path']}")
            logger.info(f"Duration: {result['duration']}")

            update_success = video_repo.update_processing_status(
                video_id,
                'completed',
                result['hls_path'],
                result['thumbnail_path'],
                result['duration']
            )

            logger.info(f"DB update result: {update_success}")

            progress_bar.progress(100)
            status_text.text("✅ 동영상 처리 완료!")

            st.success(f"""
            ✅ **동영상 업로드 및 처리 완료!**

            - 📁 원본 저장: {result['original_path']}
            - 🎥 HLS 변환: {result['hls_path']}
            - 🖼️ 썸네일: {result['thumbnail_path']}
            - ⏱️ 재생시간: {result['duration']}초
            - 🔄 DB 업데이트: {'성공' if update_success else '실패'}

            동영상이 갤러리에 공개되었습니다.
            """)

            # 페이지 새로고침
            st.rerun()

        else:
            # 실패 처리
            video_repo.update_processing_status(video_id, 'failed')
            st.error(f"❌ 동영상 처리 실패: {result['message']}")

    except Exception as e:
        logger.error(f"Error in video upload process: {e}")

        # 에러 발생 시 상태를 failed로 업데이트 (video_id가 있는 경우만)
        if 'video_id' in locals() and video_id:
            video_repo.update_processing_status(video_id, 'failed')

        st.error(f"❌ 동영상 업로드 중 오류 발생: {str(e)}")


def render_uploaded_videos_list():
    """업로드된 동영상 목록 표시"""
    # 총 동영상 개수 조회
    total_videos = video_repo.get_total_count()

    # 제목과 통계를 같은 줄에 표시
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📋 업로드된 동영상 목록")
    with col2:
        st.metric("총 동영상", f"{total_videos}개", label_visibility="visible")

    # 상태 필터
    status_filter = st.selectbox(
        "상태 필터",
        ["전체", "완료", "처리 중", "대기 중", "실패"],
        key="video_status_filter"
    )

    status_map = {
        "완료": "completed",
        "처리 중": "processing",
        "대기 중": "pending",
        "실패": "failed"
    }

    filter_value = status_map.get(status_filter)

    # 동영상 목록 조회
    videos = video_repo.get_all(status_filter=filter_value)

    if not videos:
        st.info("업로드된 동영상이 없습니다.")
        return

    # 동영상 카드 표시
    for video in videos:
        with st.expander(f"🎥 {video['title']}", expanded=False):
            # 수정 모드 체크
            edit_key = f"edit_mode_{video['id']}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False

            if not st.session_state[edit_key]:
                # 보기 모드
                render_video_view_mode(video)
            else:
                # 수정 모드
                render_video_edit_mode(video)


def render_video_view_mode(video: dict):
    """동영상 보기 모드"""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.write(f"**설명:** {video['description'] or '없음'}")
        st.write(f"**파일명:** {video['original_filename']}")
        st.write(f"**크기:** {video['file_size'] / (1024**2):.2f} MB")

        if video['duration']:
            minutes, seconds = divmod(video['duration'], 60)
            st.write(f"**재생시간:** {minutes}분 {seconds}초")

        if video['match_date']:
            field_info = f" @ {video.get('field_name', '')}" if video.get('field_name') else ""
            st.write(f"**연결 경기:** {video['match_date']} {video.get('match_time', '')} - {video['opponent']}{field_info}")

        st.write(f"**업로드:** {video['uploader_name']} ({video['created_at']})")

    with col2:
        # 상태 표시
        status_icons = {
            'completed': '✅',
            'processing': '⚙️',
            'pending': '⏳',
            'failed': '❌'
        }
        status_names = {
            'completed': '완료',
            'processing': '처리 중',
            'pending': '대기 중',
            'failed': '실패'
        }

        st.write(f"**상태:** {status_icons.get(video['status'])} {status_names.get(video['status'])}")

        # 수정 버튼
        if st.button("✏️ 수정", key=f"edit_video_{video['id']}", width="stretch"):
            st.session_state[f"edit_mode_{video['id']}"] = True
            st.rerun()

        # 재처리 버튼 (pending/failed 상태일 때만)
        if video['status'] in ['pending', 'failed']:
            if st.button("🔄 재처리", key=f"retry_video_{video['id']}", width="stretch"):
                retry_video_processing(video['id'])

        # 삭제 버튼
        if st.button("🗑️ 삭제", key=f"delete_video_{video['id']}", width="stretch"):
            delete_video(video['id'])


def render_video_edit_mode(video: dict):
    """동영상 수정 모드"""
    with st.form(f"edit_form_{video['id']}"):
        st.subheader("✏️ 동영상 정보 수정")

        # 제목 (수정 불가 - 표시만)
        st.text_input("제목 (수정 불가)", value=video['title'], disabled=True)

        # 설명 수정
        new_description = st.text_area(
            "설명",
            value=video['description'] or '',
            placeholder="동영상에 대한 설명을 입력하세요"
        )

        # 연결 경기 수정
        matches = match_repo.get_all()
        match_options = ["선택 안함"] + [
            f"{m['match_date']} {m['match_time']} - {m['opponent'] or '팀내 경기'} @ {m.get('field_name', '미정')}"
            for m in matches
        ]
        match_ids = [None] + [m['id'] for m in matches]

        # 현재 선택된 경기 찾기
        current_match_idx = 0
        if video.get('match_id'):
            try:
                current_match_idx = match_ids.index(video['match_id'])
            except ValueError:
                current_match_idx = 0

        selected_match_idx = st.selectbox(
            "연결할 경기",
            range(len(match_options)),
            format_func=lambda x: match_options[x],
            index=current_match_idx
        )
        new_match_id = match_ids[selected_match_idx]

        # 버튼
        col1, col2 = st.columns(2)
        with col1:
            save_button = st.form_submit_button("💾 저장", width="stretch", type="primary")
        with col2:
            cancel_button = st.form_submit_button("❌ 취소", width="stretch")

        if save_button:
            # 동영상 정보 업데이트
            update_video_info(video['id'], new_description, new_match_id)

        if cancel_button:
            st.session_state[f"edit_mode_{video['id']}"] = False
            st.rerun()


def update_video_info(video_id: int, description: str, match_id: int = None):
    """동영상 정보 업데이트"""
    try:
        success = video_repo.update_info(video_id, description, match_id)

        if success:
            st.success("✅ 동영상 정보가 수정되었습니다!")
            st.session_state[f"edit_mode_{video_id}"] = False
            st.rerun()
        else:
            st.error("❌ 동영상 정보 수정에 실패했습니다.")

    except Exception as e:
        logger.error(f"Error updating video info: {e}")
        st.error(f"❌ 동영상 정보 수정 중 오류 발생: {str(e)}")


def retry_video_processing(video_id: int):
    """대기 중/실패한 동영상 재처리"""
    try:
        # 동영상 정보 조회
        video = video_repo.get_by_id(video_id)
        if not video:
            st.error("동영상 정보를 찾을 수 없습니다.")
            return

        # 원본 파일 경로 확인
        video_service = VideoService()
        original_path = video_service.video_original_dir / f"{video_id}{Path(video['original_filename']).suffix.lower()}"

        logger.info(f"Checking original file: {original_path}")
        logger.info(f"File exists: {original_path.exists()}")

        if not original_path.exists():
            st.error(f"원본 파일을 찾을 수 없습니다: {original_path}")
            st.info("경로를 확인하고 있습니다...")
            video_repo.update_processing_status(video_id, 'failed')
            return

        # 이미 처리된 파일이 있는지 확인
        hls_dir = video_service.video_hls_dir / str(video_id)
        master_playlist = hls_dir / "master.m3u8"
        thumbnail_path_obj = video_service.thumbnail_dir / f"{video_id}.jpg"

        logger.info(f"Checking HLS: {master_playlist.exists()}")
        logger.info(f"Checking thumbnail: {thumbnail_path_obj.exists()}")

        # 이미 처리 완료된 경우 DB만 업데이트
        if master_playlist.exists() and thumbnail_path_obj.exists():
            st.info("✅ 처리된 파일 발견! DB 업데이트만 수행합니다...")

            video_info = video_service.get_video_info(str(original_path))
            duration = video_info['duration'] if video_info else None

            update_success = video_repo.update_processing_status(
                video_id,
                'completed',
                str(master_playlist),
                str(thumbnail_path_obj),
                duration
            )

            if update_success:
                st.success("✅ DB 업데이트 완료!")
                st.rerun()
            else:
                st.error("❌ DB 업데이트 실패")
            return

        # 파일이 없으면 재처리
        video_repo.update_processing_status(video_id, 'processing')

        # 진행 상태 표시
        with st.spinner("🎬 동영상 재처리 중..."):
            # 동영상 정보 추출
            video_info = video_service.get_video_info(str(original_path))
            duration = video_info['duration'] if video_info else None

            # 썸네일 생성
            thumb_success, thumbnail_path = video_service.generate_thumbnail(str(original_path), video_id)

            # HLS 트랜스코딩
            hls_success, hls_path, hls_message = video_service.transcode_to_hls(str(original_path), video_id)

            if hls_success:
                # 성공 처리
                video_repo.update_processing_status(
                    video_id,
                    'completed',
                    hls_path,
                    thumbnail_path,
                    duration
                )
                st.success("✅ 동영상 재처리 완료!")
                st.rerun()
            else:
                # 실패 처리
                video_repo.update_processing_status(video_id, 'failed')
                st.error(f"❌ 재처리 실패: {hls_message}")

    except Exception as e:
        logger.error(f"Error retrying video processing: {e}")
        video_repo.update_processing_status(video_id, 'failed')
        st.error(f"❌ 재처리 중 오류 발생: {str(e)}")


def delete_video(video_id: int):
    """동영상 삭제"""
    try:
        # 파일 삭제
        video_service = VideoService()
        video_service.delete_video_files(video_id)

        # DB 삭제
        if video_repo.delete(video_id):
            st.success("동영상이 삭제되었습니다.")
            st.rerun()
        else:
            st.error("동영상 삭제 실패")

    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        st.error(f"동영상 삭제 중 오류 발생: {str(e)}")