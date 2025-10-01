"""동영상 업로드 및 HLS 트랜스코딩 서비스"""
import os
import subprocess
import json
import logging
import shutil
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class VideoService:
    """동영상 업로드 및 트랜스코딩 서비스"""

    # 지원 동영상 포맷
    ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}

    # 최대 파일 크기 (2GB)
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

    # HLS 해상도 설정 (height:bitrate)
    # 720p 단일 해상도로 운영 (필요시 480p 추가 가능)
    HLS_VARIANTS = {
        '720p': {'height': 720, 'bitrate': '2500k', 'audio_bitrate': '128k'}
        # '480p': {'height': 480, 'bitrate': '1000k', 'audio_bitrate': '96k'},
        # '360p': {'height': 360, 'bitrate': '600k', 'audio_bitrate': '64k'}
    }

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.video_original_dir = self.upload_dir / "videos" / "original"
        self.video_hls_dir = self.upload_dir / "videos" / "hls"
        self.thumbnail_dir = self.upload_dir / "thumbnails"

        # 디렉토리 생성
        self._ensure_directories()

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.video_original_dir.mkdir(parents=True, exist_ok=True)
        self.video_hls_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def validate_uploaded_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """업로드된 파일 검증 (UploadedFile 객체용)"""
        # 확장자 체크
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(self.ALLOWED_EXTENSIONS)}"

        # 파일 크기 체크
        if file_size > self.MAX_FILE_SIZE:
            return False, f"파일 크기가 너무 큽니다. 최대 크기: {self.MAX_FILE_SIZE / (1024**3):.1f}GB"

        return True, "검증 성공"

    def validate_video_file(self, file_path: str) -> Tuple[bool, str]:
        """저장된 동영상 파일 검증 (파일 경로용)"""
        # 파일 존재 체크
        if not os.path.exists(file_path):
            return False, "파일이 존재하지 않습니다."

        # 확장자 체크
        ext = Path(file_path).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"지원하지 않는 파일 형식입니다."

        return True, "검증 성공"

    def get_video_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """FFprobe로 동영상 정보 추출"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"FFprobe failed: {result.stderr}")
                return None

            info = json.loads(result.stdout)

            # 동영상 스트림 찾기
            video_stream = next((s for s in info.get('streams', []) if s['codec_type'] == 'video'), None)
            if not video_stream:
                return None

            # 재생 시간 (초)
            duration = float(info.get('format', {}).get('duration', 0))

            # FPS 계산 (eval 제거 - 보안 취약점 방지)
            fps = 0.0
            try:
                fps_str = video_stream.get('r_frame_rate', '0/1')
                if '/' in fps_str:
                    numerator, denominator = fps_str.split('/', 1)
                    fps = float(numerator) / float(denominator) if float(denominator) != 0 else 0.0
                else:
                    fps = float(fps_str)
            except (ValueError, ZeroDivisionError, TypeError):
                fps = 0.0

            return {
                'duration': int(duration),
                'width': video_stream.get('width'),
                'height': video_stream.get('height'),
                'codec': video_stream.get('codec_name'),
                'fps': fps
            }

        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None

    def save_uploaded_video(self, uploaded_file, video_id: int) -> Tuple[bool, str, Optional[str]]:
        """업로드된 동영상을 원본 디렉토리에 저장"""
        try:
            # 파일명 생성 (video_id + 확장자)
            ext = Path(uploaded_file.name).suffix.lower()
            original_filename = f"{video_id}{ext}"
            original_path = self.video_original_dir / original_filename

            # 파일 저장
            with open(original_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            logger.info(f"Video saved: {original_path}")
            return True, "동영상 저장 완료", str(original_path)

        except Exception as e:
            logger.error(f"Error saving video: {e}")
            return False, f"동영상 저장 실패: {str(e)}", None

    def generate_thumbnail(self, video_path: str, video_id: int, timestamp: float = 5.0) -> Tuple[bool, Optional[str]]:
        """동영상 썸네일 생성 (5초 지점)"""
        try:
            thumbnail_filename = f"{video_id}.jpg"
            thumbnail_path = self.thumbnail_dir / thumbnail_filename

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(timestamp),  # 5초 지점
                '-vframes', '1',  # 1 프레임만
                '-vf', 'scale=640:-1',  # 가로 640px, 세로 비율 유지
                '-q:v', '2',  # 품질 (1-31, 낮을수록 고품질)
                '-y',  # 덮어쓰기
                str(thumbnail_path)
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=30)

            if result.returncode == 0 and thumbnail_path.exists():
                logger.info(f"Thumbnail generated: {thumbnail_path}")
                return True, str(thumbnail_path)
            else:
                logger.error(f"Thumbnail generation failed: {result.stderr.decode()}")
                return False, None

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return False, None

    def transcode_to_hls(self, video_path: str, video_id: int) -> Tuple[bool, Optional[str], str]:
        """HLS 다중 해상도 트랜스코딩 (완전 자동화)"""
        try:
            # HLS 출력 디렉토리
            hls_video_dir = self.video_hls_dir / str(video_id)
            hls_video_dir.mkdir(parents=True, exist_ok=True)

            segments_dir = hls_video_dir / "segments"
            segments_dir.mkdir(exist_ok=True)

            # 마스터 플레이리스트 경로
            master_playlist_path = hls_video_dir / "master.m3u8"

            # 각 해상도별 트랜스코딩
            variant_playlists = []

            for variant_name, settings in self.HLS_VARIANTS.items():
                variant_playlist = f"{variant_name}.m3u8"
                variant_playlist_path = hls_video_dir / variant_playlist
                segment_pattern = segments_dir / f"{variant_name}_%03d.ts"

                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-vf', f"scale=-2:{settings['height']}",  # 높이 고정, 가로 비율 유지
                    '-c:v', 'libx264',  # H.264 코덱
                    '-b:v', settings['bitrate'],  # 비디오 비트레이트
                    '-c:a', 'aac',  # AAC 오디오
                    '-b:a', settings['audio_bitrate'],  # 오디오 비트레이트
                    '-hls_time', '6',  # 세그먼트 길이 (초)
                    '-hls_list_size', '0',  # 모든 세그먼트 포함
                    '-hls_segment_filename', str(segment_pattern),
                    '-hls_segment_type', 'mpegts',  # 세그먼트 타입
                    '-hls_base_url', 'segments/',  # 플레이리스트에서 세그먼트 경로 프리픽스
                    '-f', 'hls',
                    '-y',
                    str(variant_playlist_path)
                ]

                logger.info(f"Transcoding {variant_name}...")
                result = subprocess.run(cmd, capture_output=True, timeout=600)

                if result.returncode != 0:
                    logger.error(f"Transcoding {variant_name} failed: {result.stderr.decode()}")
                    return False, None, f"{variant_name} 트랜스코딩 실패"

                # 마스터 플레이리스트에 추가할 정보
                variant_playlists.append({
                    'name': variant_name,
                    'playlist': variant_playlist,
                    'bandwidth': int(settings['bitrate'].replace('k', '000')),
                    'resolution': f"?x{settings['height']}"  # 정확한 가로 해상도는 동적으로 결정됨
                })

            # 마스터 플레이리스트 생성
            self._create_master_playlist(master_playlist_path, variant_playlists)

            logger.info(f"HLS transcoding completed: {master_playlist_path}")
            return True, str(master_playlist_path), "트랜스코딩 완료"

        except subprocess.TimeoutExpired:
            logger.error("Transcoding timeout")
            return False, None, "트랜스코딩 시간 초과 (10분)"

        except Exception as e:
            logger.error(f"Error during transcoding: {e}")
            return False, None, f"트랜스코딩 오류: {str(e)}"

    def _create_master_playlist(self, master_path: Path, variants: list):
        """HLS 마스터 플레이리스트 생성"""
        with open(master_path, 'w') as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:3\n\n")

            for variant in variants:
                # RESOLUTION 제거 (BANDWIDTH만 사용 - 더 안정적)
                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={variant['bandwidth']}\n")
                f.write(f"{variant['playlist']}\n\n")

    def process_video_complete(self, uploaded_file, video_id: int) -> Dict[str, Any]:
        """동영상 완전 자동 처리 (업로드 → 트랜스코딩 → 썸네일)"""
        result = {
            'success': False,
            'original_path': None,
            'hls_path': None,
            'thumbnail_path': None,
            'duration': None,
            'message': ''
        }

        try:
            # 1. 업로드 파일 검증
            file_size = uploaded_file.size
            is_valid, message = self.validate_uploaded_file(uploaded_file.name, file_size)
            if not is_valid:
                result['message'] = message
                return result

            # 2. 원본 저장
            success, message, original_path = self.save_uploaded_video(uploaded_file, video_id)
            if not success:
                result['message'] = message
                return result

            result['original_path'] = original_path

            # 2-1. 저장된 파일 검증
            is_valid, message = self.validate_video_file(original_path)
            if not is_valid:
                result['message'] = message
                return result

            # 3. 동영상 정보 추출
            video_info = self.get_video_info(original_path)
            if video_info:
                result['duration'] = video_info['duration']

            # 4. 썸네일 생성
            thumb_success, thumbnail_path = self.generate_thumbnail(original_path, video_id)
            if thumb_success:
                result['thumbnail_path'] = thumbnail_path

            # 5. HLS 트랜스코딩
            hls_success, hls_path, hls_message = self.transcode_to_hls(original_path, video_id)
            if not hls_success:
                result['message'] = hls_message
                return result

            result['hls_path'] = hls_path

            # 6. 원본 파일 삭제 (HLS 처리 완료 후 스토리지 절약)
            try:
                if original_path and os.path.exists(original_path):
                    os.remove(original_path)
                    logger.info(f"Original file deleted after HLS processing: {original_path}")
            except Exception as e:
                logger.warning(f"Failed to delete original file: {e}")
                # 원본 삭제 실패해도 처리는 성공으로 간주

            result['success'] = True
            result['message'] = "동영상 처리 완료"

            return result

        except Exception as e:
            logger.error(f"Error in complete video processing: {e}")
            result['message'] = f"처리 중 오류 발생: {str(e)}"
            return result

    def delete_video_files(self, video_id: int):
        """동영상 관련 모든 파일 삭제"""
        try:
            # 원본 파일 삭제
            for ext in self.ALLOWED_EXTENSIONS:
                original_path = self.video_original_dir / f"{video_id}{ext}"
                if original_path.exists():
                    original_path.unlink()
                    logger.info(f"Deleted original: {original_path}")

            # HLS 디렉토리 삭제
            hls_dir = self.video_hls_dir / str(video_id)
            if hls_dir.exists():
                shutil.rmtree(hls_dir)
                logger.info(f"Deleted HLS directory: {hls_dir}")

            # 썸네일 삭제
            thumbnail_path = self.thumbnail_dir / f"{video_id}.jpg"
            if thumbnail_path.exists():
                thumbnail_path.unlink()
                logger.info(f"Deleted thumbnail: {thumbnail_path}")

        except Exception as e:
            logger.error(f"Error deleting video files: {e}")