"""동영상 갤러리 페이지 (공개)"""
import streamlit as st
from database.repositories import video_repo
import logging

logger = logging.getLogger(__name__)

# 반응형 CSS 스타일
RESPONSIVE_CSS = """
<style>
.video-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin: 20px 0;
}

@media (max-width: 768px) {
    .video-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
}

.video-card {
    cursor: pointer;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}

.video-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.video-thumbnail {
    width: 100%;
    aspect-ratio: 16/9;
    object-fit: cover;
}

.video-info {
    padding: 10px;
    background: #f8f9fa;
}

.video-title {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 5px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.video-meta {
    font-size: 12px;
    color: #666;
}
</style>
"""

def render_video_gallery_page():
    """동영상 갤러리 페이지 렌더링"""

    # 제목과 필터를 같은 줄에 배치
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("🎬 동영상 갤러리")

    with col2:
        # 경기 일정 필터 드롭다운
        from database.repositories import match_repo

        # 영상이 있는 경기만 가져오기
        all_videos = video_repo.get_completed_videos()
        match_ids_with_videos = set(v['match_id'] for v in all_videos if v.get('match_id'))
        has_unlinked_videos = any(v.get('match_id') is None for v in all_videos)

        # 드롭다운 옵션 생성 (전체 + 영상 있는 경기만)
        filter_options = ["전체 영상"]
        match_dict = {}

        for match_id in match_ids_with_videos:
            match = match_repo.get_by_id(match_id)
            if match:
                match_date = match['match_date'].split()[0] if ' ' in match['match_date'] else match['match_date']
                field_name = match.get('field_name', '미정')
                match_label = f"{match_date} vs {match['opponent']} @{field_name}"
                filter_options.append(match_label)
                match_dict[match_label] = match['id']

        # 경기 연결 안 된 영상이 있으면 옵션 추가
        if has_unlinked_videos:
            filter_options.append("정보 없음")
            match_dict["정보 없음"] = None

        # 날짜순 정렬 (최신순, "전체 영상"과 "정보 없음"은 고정 위치)
        sorted_matches = sorted([opt for opt in filter_options if opt not in ["전체 영상", "정보 없음"]], reverse=True)
        filter_options = ["전체 영상"] + sorted_matches + (["정보 없음"] if has_unlinked_videos else [])

        # 세션 상태 초기화
        if 'video_filter' not in st.session_state:
            st.session_state['video_filter'] = "전체 영상"

        # 필터 선택
        selected_filter = st.selectbox(
            "경기 선택",
            options=filter_options,
            index=filter_options.index(st.session_state['video_filter']) if st.session_state['video_filter'] in filter_options else 0,
            key="match_filter"
        )

        # 필터 변경 시 페이지 리셋
        if selected_filter != st.session_state.get('video_filter'):
            st.session_state['video_filter'] = selected_filter
            st.session_state['video_page'] = 1

    st.write("")  # 공백

    # CSS 적용
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)

    # 동영상 목록 조회 (필터 적용)
    if st.session_state['video_filter'] == "전체 영상":
        videos = video_repo.get_completed_videos()
    elif st.session_state['video_filter'] == "정보 없음":
        # 경기 연결 안 된 영상만 필터링
        videos = [v for v in video_repo.get_completed_videos() if v.get('match_id') is None]
    else:
        # 선택된 경기의 ID로 필터링
        selected_match_id = match_dict[st.session_state['video_filter']]
        videos = video_repo.get_videos_by_match(selected_match_id)

    if not videos:
        st.info("아직 업로드된 동영상이 없습니다.")
        return

    # 페이징 설정 (12개씩)
    videos_per_page = 12
    total_pages = (len(videos) - 1) // videos_per_page + 1

    if 'video_page' not in st.session_state:
        st.session_state['video_page'] = 1

    # 선택된 비디오 ID 추적 (인라인 확장용)
    if 'selected_video_id' not in st.session_state:
        st.session_state['selected_video_id'] = None

    # 페이지 네비게이션
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.session_state['video_page'] > 1:
                if st.button("◀ 이전"):
                    st.session_state['video_page'] -= 1
                    st.rerun()

        with col2:
            st.markdown(f"<h4 style='text-align: center;'>{st.session_state['video_page']} / {total_pages}</h4>",
                       unsafe_allow_html=True)

        with col3:
            if st.session_state['video_page'] < total_pages:
                if st.button("다음 ▶"):
                    st.session_state['video_page'] += 1
                    st.rerun()

    # 현재 페이지 동영상 계산
    start_idx = (st.session_state['video_page'] - 1) * videos_per_page
    end_idx = start_idx + videos_per_page
    current_videos = videos[start_idx:end_idx]

    # 그리드 레이아웃으로 썸네일 표시 (인라인 확장 방식)
    render_video_grid_inline(current_videos)

    # 하단 페이지 네비게이션
    if total_pages > 1:
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.session_state['video_page'] > 1:
                if st.button("◀ 이전", key="prev_bottom"):
                    st.session_state['video_page'] -= 1
                    st.rerun()

        with col2:
            st.markdown(f"<h4 style='text-align: center;'>{st.session_state['video_page']} / {total_pages}</h4>",
                       unsafe_allow_html=True)

        with col3:
            if st.session_state['video_page'] < total_pages:
                if st.button("다음 ▶", key="next_bottom"):
                    st.session_state['video_page'] += 1
                    st.rerun()


def render_video_grid_inline(videos: list):
    """비디오 그리드 렌더링 (항상 플레이어 표시)"""
    cols_per_row = 4

    for i in range(0, len(videos), cols_per_row):
        # 플레이어 그리드 표시
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(videos):
                with cols[j]:
                    render_video_player_card(videos[i + j])


def render_video_player_card(video: dict):
    """비디오 플레이어 카드 렌더링 (항상 플레이어 표시)"""
    import os
    from PIL import Image

    # 썸네일 크기로 플레이어 높이 계산
    thumbnail_path = video.get('thumbnail_path', f"uploads/thumbnails/{video['id']}.jpg")
    player_height = 500  # 기본 높이

    if os.path.exists(thumbnail_path):
        try:
            with Image.open(thumbnail_path) as img:
                width, height = img.size
                aspect_ratio = height / width
                estimated_column_width = 280  # 4열 기준 예상 너비
                player_height = int(estimated_column_width * aspect_ratio)
        except Exception as e:
            pass

    # 플레이어 렌더링 (autoplay 제거, 수동 재생)
    render_simple_player(video['hls_path'], video['thumbnail_path'], video['id'], player_height)

    # 제목
    st.markdown(f"**{video['title'][:30]}{'...' if len(video['title']) > 30 else ''}**")

    # 메타 정보 (3줄로 구성)
    # 1줄: 재생시간
    if video.get('duration'):
        minutes, seconds = divmod(video['duration'], 60)
        st.caption(f"⏱️ {minutes}분 {seconds}초")
    else:
        st.caption("⏱️ -")

    # 2줄: 경기 정보 (경기장 포함)
    if video.get('match_date') and video.get('opponent'):
        field_info = f" @ {video.get('field_name')}" if video.get('field_name') else ""
        st.caption(f"🏆 {video['match_date']} vs {video['opponent']}{field_info}")
    else:
        st.caption("🏆 경기 정보 없음")

    # 3줄: 업로드 일시
    if video.get('created_at'):
        # YYYY-MM-DD HH:MM:SS 형식에서 날짜와 시간 추출
        upload_datetime = video['created_at']
        if len(upload_datetime) >= 16:
            upload_date = upload_datetime[:10]  # YYYY-MM-DD
            upload_time = upload_datetime[11:16]  # HH:MM
            st.caption(f"📅 {upload_date} {upload_time}")
        else:
            st.caption(f"📅 {upload_datetime[:10]}")
    else:
        st.caption("📅 -")

    st.divider()


def render_simple_player(hls_path: str, poster_path: str = None, video_id: int = None, height: int = 500):
    """간단한 HLS 플레이어 렌더링 (autoplay 없음)"""

    # 고유 플레이어 ID
    player_id = f"video-player-{video_id}" if video_id else "video-player"

    # Nginx를 통한 HLS 경로 (웹 접근 가능)
    web_hls_path = f"/futsal/uploads/videos/hls/{video_id}/master.m3u8"
    web_poster_path = f"/futsal/uploads/thumbnails/{video_id}.jpg" if poster_path else ""

    # video.js 기반 HLS 플레이어 (상세 로깅 포함)
    player_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
        <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }}
            .video-js {{
                width: 100% !important;
                height: 100% !important;
            }}
        </style>
    </head>
    <body>
        <video
            id="{player_id}"
            class="video-js vjs-default-skin vjs-big-play-centered"
            controls
            preload="metadata"
            {f'poster="{web_poster_path}"' if web_poster_path else ''}
            data-setup='{{}}'>
            <source src="{web_hls_path}" type="application/x-mpegURL" />
            <p class="vjs-no-js">
                HLS 플레이어를 로드하려면 JavaScript를 활성화해주세요.
            </p>
        </video>
        <script>
            var player = videojs('{player_id}');
            var videoId = {video_id};

            // 로그를 콘솔에만 기록 (간단한 클라이언트 로깅)
            function logToConsole(level, eventType, message, details) {{
                var logData = {{
                    video_id: videoId,
                    level: level,
                    event_type: eventType,
                    message: message,
                    details: details || {{}},
                    timestamp: new Date().toISOString()
                }};

                if (level === 'error') {{
                    console.error('[Video Log]', logData);
                }} else if (level === 'warn') {{
                    console.warn('[Video Log]', logData);
                }} else {{
                    console.log('[Video Log]', logData);
                }}
            }}

            // 플레이어 초기화
            logToConsole('info', 'player_init', 'Player initialized', {{
                hls_path: '{web_hls_path}',
                poster_path: '{web_poster_path}'
            }});

            // 재생 시작
            player.on('play', function() {{
                logToConsole('info', 'play', 'Video playback started');
            }});

            // 재생 가능 상태
            player.on('canplay', function() {{
                logToConsole('info', 'canplay', 'Video can start playing');
            }});

            // 로딩 시작
            player.on('loadstart', function() {{
                logToConsole('info', 'loadstart', 'Video loading started');
            }});

            // 메타데이터 로드 완료
            player.on('loadedmetadata', function() {{
                logToConsole('info', 'loadedmetadata', 'Metadata loaded', {{
                    duration: player.duration(),
                    videoWidth: player.videoWidth(),
                    videoHeight: player.videoHeight()
                }});
            }});

            // 버퍼링
            player.on('waiting', function() {{
                logToConsole('warn', 'waiting', 'Buffering/waiting for data');
            }});

            // 정지 (버퍼링 완료)
            player.on('stalled', function() {{
                logToConsole('warn', 'stalled', 'Media data fetching stalled');
            }});

            // 에러 처리
            player.on('error', function() {{
                var error = player.error();
                var errorDetails = {{
                    code: error ? error.code : 'unknown',
                    message: error ? error.message : 'Unknown error',
                    type: error ? error.type : 'unknown'
                }};

                console.error('Video.js error:', error);
                logToConsole('error', 'playback_error', 'Video playback error', errorDetails);
            }});

            // HLS 관련 에러 (tech-specific)
            if (player.tech_ && player.tech_.hls) {{
                player.tech_.hls.on('error', function(event, data) {{
                    logToConsole('error', 'hls_error', 'HLS-specific error', {{
                        type: data.type,
                        details: data.details,
                        fatal: data.fatal
                    }});
                }});
            }}

            // 페이지 언로드 시 (사용자가 페이지 떠날 때)
            window.addEventListener('beforeunload', function() {{
                logToConsole('info', 'page_unload', 'User leaving page', {{
                    currentTime: player.currentTime(),
                    duration: player.duration()
                }});
            }});
        </script>
    </body>
    </html>
    """

    # 동적으로 계산된 높이 사용
    st.components.v1.html(player_html, height=height, scrolling=False)


def render_inline_hls_player(hls_path: str, poster_path: str = None, video_id: int = None, height: int = 500):
    """인라인 HLS 플레이어 렌더링 (썸네일과 동일한 크기)"""

    # 고유 플레이어 ID
    player_id = f"video-player-{video_id}" if video_id else "video-player"

    # Nginx를 통한 HLS 경로 (웹 접근 가능)
    web_hls_path = f"/futsal/uploads/videos/hls/{video_id}/master.m3u8"
    web_poster_path = f"/futsal/uploads/thumbnails/{video_id}.jpg" if poster_path else ""

    # video.js 기반 HLS 플레이어 (썸네일과 정확히 동일한 크기)
    player_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
        <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }}
            .video-js {{
                width: 100% !important;
                height: 100% !important;
            }}
        </style>
    </head>
    <body>
        <video
            id="{player_id}"
            class="video-js vjs-default-skin vjs-big-play-centered"
            controls
            preload="auto"
            autoplay
            {f'poster="{web_poster_path}"' if web_poster_path else ''}
            data-setup='{{}}'>
            <source src="{web_hls_path}" type="application/x-mpegURL" />
            <p class="vjs-no-js">
                HLS 플레이어를 로드하려면 JavaScript를 활성화해주세요.
            </p>
        </video>
        <script>
            var player = videojs('{player_id}');
            player.on('error', function() {{
                console.error('Video.js error:', player.error());
            }});
        </script>
    </body>
    </html>
    """

    # 동적으로 계산된 높이 사용
    st.components.v1.html(player_html, height=height, scrolling=False)