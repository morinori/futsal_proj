"""데이터 모델 정의"""
from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass
class Player:
    """선수 모델"""
    name: str
    position: str
    phone: str = ""
    email: str = ""
    active: bool = True
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class Field:
    """구장 모델"""
    name: str
    address: str = ""
    cost: int = 0
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class Match:
    """경기 모델"""
    field_id: int
    match_date: date
    match_time: str
    opponent: str = ""
    result: str = ""
    attendance_lock_minutes: int = 0
    id: Optional[int] = None
    created_at: Optional[str] = None

    # 조인된 필드
    field_name: Optional[str] = None

@dataclass
class PlayerStats:
    """선수 통계 모델"""
    player_id: int
    match_id: int
    goals: int = 0
    assists: int = 0
    saves: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    mvp: bool = False
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class News:
    """소식 모델"""
    title: str
    content: str
    author: str
    pinned: bool = False
    category: str = "general"
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class FinanceRecord:
    """재정 기록 모델"""
    date: str
    description: str
    amount: int
    type: str  # 'income' or 'expense'
    category: str = "match"
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class Gallery:
    """갤러리 모델"""
    title: str
    description: str
    file_path: str
    match_id: Optional[int] = None
    id: Optional[int] = None
    upload_date: Optional[str] = None

@dataclass
class Attendance:
    """출석 모델"""
    match_id: int
    player_id: int
    status: str = "absent"  # present, absent, pending
    id: Optional[int] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None

    # 조인된 필드
    player_name: Optional[str] = None
    match_date: Optional[str] = None
    match_time: Optional[str] = None
    field_name: Optional[str] = None

@dataclass
class Admin:
    """관리자 모델"""
    username: str
    password_hash: str
    name: str
    role: str = "admin"
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[str] = None
    last_login: Optional[str] = None

@dataclass
class Video:
    """동영상 모델"""
    title: str
    description: str
    original_filename: str
    file_size: int  # bytes
    duration: Optional[int] = None  # seconds
    status: str = "pending"  # pending, processing, completed, failed
    hls_path: Optional[str] = None  # HLS master.m3u8 경로
    thumbnail_path: Optional[str] = None
    match_id: Optional[int] = None
    uploaded_by: Optional[int] = None  # admin_id
    id: Optional[int] = None
    created_at: Optional[str] = None
    processed_at: Optional[str] = None

@dataclass
class TeamDistribution:
    """팀 구성 모델"""
    match_id: int
    team_data: str  # JSON 형식
    created_by: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None