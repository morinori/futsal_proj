"""애플리케이션 설정 관리"""
import os
import logging
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    DB_PATH: str = "team_platform.db"
    BACKUP_PATH: str = "backups/"

@dataclass
class AppConfig:
    """앱 전반 설정"""
    UPLOAD_DIR: str = "uploads"
    LOG_LEVEL: str = "INFO"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = None

    # 보안 설정
    ALLOWED_MIME_TYPES: dict = None
    MAX_FILENAME_LENGTH: int = 100
    SCAN_FILE_CONTENT: bool = True

    def __post_init__(self):
        if self.ALLOWED_EXTENSIONS is None:
            # gif 제거 - 보안상 위험
            self.ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']

        if self.ALLOWED_MIME_TYPES is None:
            # 허용된 MIME 타입과 매직 바이트 정의
            self.ALLOWED_MIME_TYPES = {
                'png': {
                    'mime': ['image/png'],
                    'magic_bytes': [b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a']
                },
                'jpg': {
                    'mime': ['image/jpeg'],
                    'magic_bytes': [b'\xff\xd8\xff']
                },
                'jpeg': {
                    'mime': ['image/jpeg'],
                    'magic_bytes': [b'\xff\xd8\xff']
                }
            }

        # 디렉토리 생성 (보안 권한 설정)
        os.makedirs(self.UPLOAD_DIR, mode=0o755, exist_ok=True)

        # 로깅 설정
        logging.basicConfig(level=getattr(logging, self.LOG_LEVEL))

@dataclass
class UIConfig:
    """UI 관련 설정"""
    PAGE_TITLE: str = "⚽ 신공사차 일정관리 시스템"
    LAYOUT: str = "wide"
    SIDEBAR_STATE: str = "auto"  # 화면 크기에 따라 자동 결정 (데스크탑: 펼침, 모바일: 접힘)

    # 달력 설정
    CALENDAR_START_HOUR: int = 6
    CALENDAR_END_HOUR: int = 23
    DEFAULT_MATCH_HOUR: int = 19

# 설정 인스턴스 생성
db_config = DatabaseConfig()
app_config = AppConfig()
ui_config = UIConfig()