"""UI 페이지 모듈"""

from .dashboard import dashboard_page
from .schedule import schedule_page
from .players import players_page
from .statistics import statistics_page
from .attendance import attendance_page
from .news import news_page
from .gallery import gallery_page
from .finance import finance_page
from . import admin_settings
from . import video_upload
from . import video_gallery
from . import news_management

__all__ = [
    'dashboard_page',
    'schedule_page',
    'players_page',
    'statistics_page',
    'attendance_page',
    'news_page',
    'gallery_page',
    'finance_page',
    'admin_settings',
    'video_upload',
    'video_gallery',
    'news_management'
]