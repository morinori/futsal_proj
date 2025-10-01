# 🔧 Streamlit 풋살팀 플랫폼 리팩토링 계획

## 📋 현재 상태 분석

### 현재 코드 구조
```
app.py (단일 파일, ~1000+ 라인)
├── 설정 및 스타일
├── 데이터베이스 관련 함수들
├── UI 렌더링 함수들
├── 데이터 조회/조작 함수들
└── 메인 함수
```

### 주요 문제점
- **단일 파일 거대화**: 모든 기능이 하나의 파일에 집중
- **함수 책임 혼재**: UI, 비즈니스 로직, 데이터 액세스가 섞임
- **중복 코드**: 비슷한 데이터베이스 조작 패턴 반복
- **테스트 어려움**: 단위 테스트가 불가능한 구조
- **유지보수성**: 새로운 기능 추가 시 복잡도 증가

## 🎯 리팩토링 목표

### 1. 코드 분리 및 모듈화
- **관심사 분리** (Separation of Concerns)
- **단일 책임 원칙** (Single Responsibility Principle)
- **의존성 역전** (Dependency Inversion)

### 2. 확장성 및 유지보수성 향상
- 새로운 기능 추가 용이성
- 기존 기능 수정 시 사이드 이펙트 최소화
- 코드 재사용성 증대

### 3. 테스트 가능한 구조
- 단위 테스트 가능한 함수들
- 모킹 가능한 의존성 구조

## 🏗️ 새로운 프로젝트 구조

```
streamlit_team_platform/
├── README.md
├── requirements.txt
├── app.py                          # 메인 애플리케이션 엔트리포인트
├── config/
│   ├── __init__.py
│   ├── settings.py                 # 앱 설정 및 상수
│   └── database.py                 # 데이터베이스 설정
├── database/
│   ├── __init__.py
│   ├── connection.py               # DB 연결 관리
│   ├── models.py                   # 데이터 모델 정의
│   ├── repositories.py             # 데이터 액세스 계층
│   └── migrations.py               # 스키마 초기화 및 마이그레이션
├── services/
│   ├── __init__.py
│   ├── match_service.py            # 경기 관련 비즈니스 로직
│   ├── player_service.py           # 선수 관련 비즈니스 로직
│   ├── finance_service.py          # 재정 관련 비즈니스 로직
│   ├── news_service.py             # 소식 관련 비즈니스 로직
│   └── gallery_service.py          # 갤러리 관련 비즈니스 로직
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── calendar.py             # 달력 컴포넌트
│   │   ├── metrics.py              # 지표 카드 컴포넌트
│   │   └── forms.py                # 공통 폼 컴포넌트
│   └── pages/
│       ├── __init__.py
│       ├── dashboard.py            # 메인 대시보드
│       ├── schedule.py             # 일정 관리
│       ├── players.py              # 선수 관리
│       ├── statistics.py           # 통계
│       ├── news.py                 # 팀 소식
│       ├── gallery.py              # 갤러리
│       └── finance.py              # 재정 관리
├── utils/
│   ├── __init__.py
│   ├── validators.py               # 입력 검증 함수들
│   ├── formatters.py               # 데이터 포맷팅 함수들
│   └── security.py                 # 보안 관련 유틸리티
└── tests/
    ├── __init__.py
    ├── test_services/
    ├── test_ui/
    └── test_utils/
```

## 📦 모듈별 상세 구현 가이드

### 1. config/ - 설정 관리

#### config/settings.py
```python
"""애플리케이션 설정 관리"""
import os
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
    
    def __post_init__(self):
        if self.ALLOWED_EXTENSIONS is None:
            self.ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']
        
        # 디렉토리 생성
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

@dataclass
class UIConfig:
    """UI 관련 설정"""
    PAGE_TITLE: str = "⚽ 우리팀 플랫폼"
    LAYOUT: str = "wide"
    SIDEBAR_STATE: str = "expanded"
    
    # 달력 설정
    CALENDAR_START_HOUR: int = 6
    CALENDAR_END_HOUR: int = 23
    DEFAULT_MATCH_HOUR: int = 19

# 설정 인스턴스 생성
db_config = DatabaseConfig()
app_config = AppConfig()
ui_config = UIConfig()
```

#### config/database.py
```python
"""데이터베이스 스키마 정의 및 초기화"""

# 테이블 생성 쿼리들
CREATE_TABLES = {
    'players': """
        CREATE TABLE IF NOT EXISTS players(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT,
            phone TEXT,
            email TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    
    'fields': """
        CREATE TABLE IF NOT EXISTS fields(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            cost INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """,
    
    'matches': """
        CREATE TABLE IF NOT EXISTS matches(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER NOT NULL,
            match_date TEXT NOT NULL,
            match_time TEXT NOT NULL,
            opponent TEXT DEFAULT '',
            result TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(field_id) REFERENCES fields(id)
        );
    """,
    
    # ... 나머지 테이블들
}

# 샘플 데이터
SAMPLE_DATA = {
    'players': [
        ("김철수", "FW", "010-1234-5678", "kim@email.com"),
        ("이영희", "MF", "010-2345-6789", "lee@email.com"),
        ("박민수", "DF", "010-3456-7890", "park@email.com"),
        ("최준호", "GK", "010-4567-8901", "choi@email.com"),
        ("정수진", "MF", "010-5678-9012", "jung@email.com")
    ],
    
    'fields': [
        ("중앙 풋살장", "서울시 강남구 테헤란로 123", 100000),
        ("스포츠몬스터", "서울시 서초구 서초대로 456", 120000),
        ("킥오프 풋살장", "서울시 송파구 올림픽로 789", 80000)
    ],
    
    # ... 나머지 샘플 데이터
}
```

### 2. database/ - 데이터 계층

#### database/connection.py
```python
"""데이터베이스 연결 관리"""
import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator, List, Optional, Any
from config.settings import db_config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """데이터베이스 연결 및 쿼리 실행 관리"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or db_config.DB_PATH
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """안전한 데이터베이스 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch_all: bool = True) -> Optional[Any]:
        """안전한 쿼리 실행"""
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                
                # INSERT, UPDATE, DELETE 등의 경우 커밋
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    return cur.rowcount
                
                return cur.fetchall() if fetch_all else cur.fetchone()
                
        except sqlite3.Error as e:
            logger.error(f"Query execution error: {e}")
            return None

# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()
```

#### database/models.py
```python
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
    """팀 소식 모델"""
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
```

#### database/repositories.py
```python
"""데이터 액세스 계층 - Repository 패턴"""
from typing import List, Optional
from datetime import date
from database.connection import db_manager
from database.models import Match, Player, Field, PlayerStats, News, FinanceRecord

class MatchRepository:
    """경기 데이터 액세스"""
    
    def create(self, match: Match) -> bool:
        """경기 생성"""
        query = """
            INSERT INTO matches (field_id, match_date, match_time, opponent, result)
            VALUES (?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(
            query, 
            (match.field_id, str(match.match_date), match.match_time, match.opponent, match.result)
        )
        return result is not None and result > 0
    
    def get_by_id(self, match_id: int) -> Optional[Match]:
        """ID로 경기 조회"""
        query = """
            SELECT m.*, f.name as field_name 
            FROM matches m 
            JOIN fields f ON f.id = m.field_id 
            WHERE m.id = ?
        """
        result = db_manager.execute_query(query, (match_id,), fetch_all=False)
        return Match(**dict(result)) if result else None
    
    def get_for_month(self, year: int, month: int) -> List[Match]:
        """특정 월의 경기 목록"""
        query = """
            SELECT m.*, f.name as field_name
            FROM matches m
            JOIN fields f ON f.id = m.field_id
            WHERE strftime('%Y', m.match_date) = ? 
            AND strftime('%m', m.match_date) = ?
            ORDER BY m.match_date, m.match_time
        """
        results = db_manager.execute_query(query, (str(year), f"{month:02d}"))
        return [Match(**dict(row)) for row in results] if results else []
    
    def get_next_match(self) -> Optional[Match]:
        """다음 경기 조회"""
        query = """
            SELECT m.*, f.name as field_name 
            FROM matches m 
            JOIN fields f ON f.id = m.field_id 
            WHERE m.match_date >= date('now') 
            ORDER BY m.match_date, m.match_time 
            LIMIT 1
        """
        result = db_manager.execute_query(query, fetch_all=False)
        return Match(**dict(result)) if result else None
    
    def get_monthly_count(self) -> int:
        """이번 달 경기 수"""
        query = """
            SELECT COUNT(*) as count FROM matches 
            WHERE strftime('%Y-%m', match_date) = strftime('%Y-%m', 'now')
        """
        result = db_manager.execute_query(query, fetch_all=False)
        return result['count'] if result else 0

class PlayerRepository:
    """선수 데이터 액세스"""
    
    def create(self, player: Player) -> bool:
        """선수 생성"""
        query = """
            INSERT INTO players (name, position, phone, email, active)
            VALUES (?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(
            query, 
            (player.name, player.position, player.phone, player.email, player.active)
        )
        return result is not None and result > 0
    
    def get_all_active(self) -> List[Player]:
        """활성 선수 목록"""
        query = "SELECT * FROM players WHERE active=1 ORDER BY name"
        results = db_manager.execute_query(query)
        return [Player(**dict(row)) for row in results] if results else []
    
    def get_by_id(self, player_id: int) -> Optional[Player]:
        """ID로 선수 조회"""
        query = "SELECT * FROM players WHERE id = ?"
        result = db_manager.execute_query(query, (player_id,), fetch_all=False)
        return Player(**dict(result)) if result else None
    
    def get_total_count(self) -> int:
        """총 활성 선수 수"""
        query = "SELECT COUNT(*) as count FROM players WHERE active=1"
        result = db_manager.execute_query(query, fetch_all=False)
        return result['count'] if result else 0

class FieldRepository:
    """구장 데이터 액세스"""
    
    def create(self, field: Field) -> bool:
        """구장 생성"""
        query = "INSERT INTO fields (name, address, cost) VALUES (?, ?, ?)"
        result = db_manager.execute_query(query, (field.name, field.address, field.cost))
        return result is not None and result > 0
    
    def get_all(self) -> List[Field]:
        """모든 구장 목록"""
        query = "SELECT * FROM fields ORDER BY name"
        results = db_manager.execute_query(query)
        return [Field(**dict(row)) for row in results] if results else []

# Repository 인스턴스들
match_repo = MatchRepository()
player_repo = PlayerRepository()
field_repo = FieldRepository()
```

### 3. services/ - 비즈니스 로직

#### services/match_service.py
```python
"""경기 관련 비즈니스 로직"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from database.repositories import match_repo, field_repo
from database.models import Match
from utils.validators import validate_match_data
from utils.formatters import format_time_options

class MatchService:
    """경기 관련 서비스"""
    
    def __init__(self):
        self.match_repo = match_repo
        self.field_repo = field_repo
    
    def create_match(self, field_id: int, match_date: date, match_time: str, opponent: str = "") -> bool:
        """경기 생성"""
        # 데이터 검증
        validation_result = validate_match_data({
            'field_id': field_id,
            'match_date': match_date,
            'match_time': match_time,
            'opponent': opponent
        })
        
        if not validation_result.is_valid:
            raise ValueError(f"Invalid match data: {validation_result.errors}")
        
        # 경기 생성
        match = Match(
            field_id=field_id,
            match_date=match_date,
            match_time=match_time,
            opponent=opponent
        )
        
        return self.match_repo.create(match)
    
    def get_next_match(self) -> Optional[Dict[str, Any]]:
        """다음 경기 조회"""
        match = self.match_repo.get_next_match()
        if not match:
            return None
            
        return {
            'field_name': match.field_name,
            'match_date': match.match_date,
            'match_time': match.match_time,
            'opponent': match.opponent
        }
    
    def get_monthly_matches(self, year: int, month: int) -> List[Match]:
        """월별 경기 목록"""
        return self.match_repo.get_for_month(year, month)
    
    def get_monthly_count(self) -> int:
        """이번 달 경기 수"""
        return self.match_repo.get_monthly_count()
    
    def get_time_options(self) -> List[tuple]:
        """시간 선택 옵션 생성"""
        return format_time_options()
    
    def get_available_fields(self) -> List[Dict[str, Any]]:
        """사용 가능한 구장 목록"""
        fields = self.field_repo.get_all()
        return [
            {
                'id': field.id,
                'name': field.name,
                'address': field.address,
                'cost': field.cost,
                'display_name': f"{field.name} - {field.address}"
            }
            for field in fields
        ]

# 서비스 인스턴스
match_service = MatchService()
```

#### services/player_service.py
```python
"""선수 관련 비즈니스 로직"""
from typing import List, Dict, Any
from database.repositories import player_repo
from database.models import Player
from utils.validators import validate_player_data

class PlayerService:
    """선수 관련 서비스"""
    
    def __init__(self):
        self.player_repo = player_repo
    
    def create_player(self, name: str, position: str, phone: str = "", email: str = "") -> bool:
        """선수 생성"""
        # 데이터 검증
        validation_result = validate_player_data({
            'name': name,
            'position': position,
            'phone': phone,
            'email': email
        })
        
        if not validation_result.is_valid:
            raise ValueError(f"Invalid player data: {validation_result.errors}")
        
        player = Player(
            name=name,
            position=position,
            phone=phone,
            email=email
        )
        
        return self.player_repo.create(player)
    
    def get_all_players(self) -> List[Dict[str, Any]]:
        """모든 활성 선수 목록"""
        players = self.player_repo.get_all_active()
        return [
            {
                'id': player.id,
                'name': player.name,
                'position': player.position,
                'phone': player.phone,
                'email': player.email,
                'created_at': player.created_at
            }
            for player in players
        ]
    
    def get_total_count(self) -> int:
        """총 선수 수"""
        return self.player_repo.get_total_count()
    
    def get_position_options(self) -> List[str]:
        """포지션 선택 옵션"""
        return ["GK", "DF", "MF", "FW"]

# 서비스 인스턴스
player_service = PlayerService()
```

### 4. ui/ - 프레젠테이션 계층

#### ui/components/calendar.py
```python
"""달력 컴포넌트"""
import streamlit as st
import calendar
from datetime import datetime
from typing import List, Dict, Any
from services.match_service import match_service

class CalendarComponent:
    """달력 컴포넌트"""
    
    def __init__(self):
        self.match_service = match_service
    
    def render(self) -> None:
        """달력 렌더링"""
        year, month = self._handle_navigation()
        matches = self.match_service.get_monthly_matches(year, month)
        
        self._render_calendar_html(year, month, matches)
        self._render_match_summary(matches)
    
    def _handle_navigation(self) -> tuple[int, int]:
        """달력 네비게이션 처리"""
        today = datetime.now()
        
        # 세션 상태 초기화
        if 'calendar_year' not in st.session_state:
            st.session_state['calendar_year'] = today.year
        if 'calendar_month' not in st.session_state:
            st.session_state['calendar_month'] = today.month
        
        display_year = st.session_state['calendar_year']
        display_month = st.session_state['calendar_month']
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("◀ 이전"):
                if display_month == 1:
                    st.session_state['calendar_month'] = 12
                    st.session_state['calendar_year'] = display_year - 1
                else:
                    st.session_state['calendar_month'] = display_month - 1
                st.rerun()
        
        with col2:
            st.markdown(f"<h4 style='text-align: center;'>{display_year}년 {display_month}월</h4>", 
                       unsafe_allow_html=True)
        
        with col3:
            if st.button("다음 ▶"):
                if display_month == 12:
                    st.session_state['calendar_month'] = 1
                    st.session_state['calendar_year'] = display_year + 1
                else:
                    st.session_state['calendar_month'] = display_month + 1
                st.rerun()
        
        return display_year, display_month
    
    def _render_calendar_html(self, year: int, month: int, matches: List[Any]) -> None:
        """달력 HTML 생성 및 렌더링"""
        # 경기 일정을 날짜별로 그룹화
        matches_by_date = {}
        for match in matches:
            match_date = str(match.match_date)
            if match_date not in matches_by_date:
                matches_by_date[match_date] = []
            matches_by_date[match_date].append(match)
        
        # CSS 스타일
        self._render_calendar_styles()
        
        # 달력 생성
        cal = calendar.monthcalendar(year, month)
        today = datetime.now()
        
        # 요일 헤더
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        header_html = '<div class="calendar-container"><div class="calendar-header">'
        for day in weekdays:
            header_html += f'<div class="calendar-day-header">{day}</div>'
        header_html += '</div>'
        
        # 달력 그리드
        calendar_html = '<div class="calendar-grid">'
        
        for week in cal:
            for day in week:
                if day == 0:
                    calendar_html += '<div class="calendar-day"></div>'
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    
                    # 오늘인지 확인
                    is_today = (day == today.day and month == today.month and year == today.year)
                    
                    # 경기가 있는 날인지 확인
                    has_match = date_str in matches_by_date
                    
                    # CSS 클래스 설정
                    css_class = "calendar-day"
                    if is_today:
                        css_class += " today"
                    if has_match:
                        css_class += " has-match"
                    
                    calendar_html += f'<div class="{css_class}">'
                    calendar_html += f'<div class="calendar-day-number">{day}</div>'
                    
                    # 해당 날짜의 경기 표시
                    if has_match:
                        for match in matches_by_date[date_str][:2]:
                            time_str = match.match_time[:5]
                            field_name = match.field_name[:8] if match.field_name else "구장"
                            calendar_html += f'<div class="calendar-match">{time_str} {field_name}</div>'
                        
                        if len(matches_by_date[date_str]) > 2:
                            calendar_html += f'<div class="calendar-match">+{len(matches_by_date[date_str])-2}개</div>'
                    
                    calendar_html += '</div>'
        
        calendar_html += '</div></div>'
        
        st.markdown(header_html + calendar_html, unsafe_allow_html=True)
    
    def _render_calendar_styles(self) -> None:
        """달력 CSS 스타일"""
        st.markdown("""
        <style>
        .calendar-container {
            font-family: Arial, sans-serif;
        }
        .calendar-header {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 2px;
            margin-bottom: 5px;
        }
        .calendar-day-header {
            background-color: #f0f0f0;
            padding: 8px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ddd;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 2px;
        }
        .calendar-day {
            min-height: 80px;
            padding: 5px;
            border: 1px solid #ddd;
            background-color: white;
        }
        .calendar-day.today {
            background-color: #e3f2fd;
            border-color: #2196f3;
        }
        .calendar-day.has-match {
            background-color: #fff3e0;
            border-color: #ff9800;
        }
        .calendar-day-number {
            font-weight: bold;
            margin-bottom: 3px;
        }
        .calendar-match {
            font-size: 10px;
            background-color: #4caf50;
            color: white;
            padding: 1px 3px;
            border-radius: 3px;
            margin: 1px 0;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _render_match_summary(self, matches: List[Any]) -> None:
        """경기 요약 정보"""
        if matches:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📋 이번 달 경기 목록")
                today = datetime.now().date()
                
                for match in matches:
                    match_datetime = f"{match.match_date} {match.match_time}"
                    opponent_text = f" vs {match.opponent}" if match.opponent else ""
                    
                    # 경기가 지난 것인지 확인
                    from datetime import datetime
                    match_date_obj = datetime.strptime(str(match.match_date), '%Y-%m-%d').date()
                    is_past = match_date_obj < today
                    
                    icon = "✅" if is_past else "📅"
                    st.write(f"{icon} **{match_datetime}** - {match.field_name}{opponent_text}")
            
            with col2:
                st.markdown("### 📈 이번 달 요약")
                total_matches = len(matches)
                today = datetime.now().date()
                past_matches = len([m for m in matches 
                                  if datetime.strptime(str(m.match_date), '%Y-%m-%d').date() < today])
                upcoming_matches = total_matches - past_matches
                
                st.metric("총 경기", total_matches)
                st.metric("완료", past_matches)
                st.metric("예정", upcoming_matches)
        else:
            st.info("이번 달에 예정된 경기가 없습니다.")
            
            if st.button("📅 경기 일정 추가하기"):
                st.session_state['redirect_to'] = "📅 일정 관리"
                st.rerun()

# 컴포넌트 인스턴스
calendar_component = CalendarComponent()
```

#### ui/components/metrics.py
```python
"""지표 카드 컴포넌트"""
import streamlit as st
from typing import Dict, Any
from services.match_service import match_service
from services.player_service import player_service
from services.finance_service import finance_service

class MetricsComponent:
    """메인 지표 카드 컴포넌트"""
    
    def __init__(self):
        self.match_service = match_service
        self.player_service = player_service
        self.finance_service = finance_service
    
    def render_main_metrics(self) -> None:
        """메인 대시보드 지표들"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._render_next_match_metric()
        
        with col2:
            self._render_player_count_metric()
        
        with col3:
            self._render_monthly_matches_metric()
        
        with col4:
            self._render_team_balance_metric()
    
    def _render_next_match_metric(self) -> None:
        """다음 경기 지표"""
        next_match = self.match_service.get_next_match()
        if next_match:
            st.metric(
                "다음 경기", 
                next_match['field_name'], 
                f"{next_match['match_date']} {next_match['match_time']}"
            )
        else:
            st.metric("다음 경기", "예정 없음", "일정을 추가해주세요")
    
    def _render_player_count_metric(self) -> None:
        """팀원 수 지표"""
        total_players = self.player_service.get_total_count()
        st.metric("팀원 수", f"{total_players}명", "활성 멤버")
    
    def _render_monthly_matches_metric(self) -> None:
        """이번 달 경기 수 지표"""
        monthly_count = self.match_service.get_monthly_count()
        st.metric("이번 달 경기", f"{monthly_count}경기", "")
    
    def _render_team_balance_metric(self) -> None:
        """팀 잔고 지표"""
        balance = self.finance_service.get_team_balance()
        st.metric("팀 잔고", f"{balance:,}원", "")

# 컴포넌트 인스턴스
metrics_component = MetricsComponent()
```

#### ui/pages/dashboard.py
```python
"""메인 대시보드 페이지"""
import streamlit as st
from ui.components.calendar import calendar_component
from ui.components.metrics import metrics_component
from services.match_service import match_service
from services.news_service import news_service

class DashboardPage:
    """메인 대시보드 페이지"""
    
    def __init__(self):
        self.match_service = match_service
        self.news_service = news_service
    
    def render(self) -> None:
        """대시보드 렌더링"""
        self._render_header()
        self._render_metrics()
        self._render_main_content()
    
    def _render_header(self) -> None:
        """헤더 렌더링"""
        st.markdown("""
        <div class="main-header">
            <h1>⚽ 우리팀 플랫폼</h1>
            <p>일정 관리부터 통계, 갤러리까지 모든 것을 한 곳에서!</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_metrics(self) -> None:
        """지표 카드들 렌더링"""
        metrics_component.render_main_metrics()
        st.markdown("---")
    
    def _render_main_content(self) -> None:
        """메인 콘텐츠 렌더링"""
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.subheader("📅 이번 달 경기 일정")
            calendar_component.render()
        
        with col2:
            st.subheader("📊 최근 경기 통계")
            self._render_recent_stats()
            
            st.markdown("---")
            
            st.subheader("📢 팀 공지사항")
            self._render_recent_news()
    
    def _render_recent_stats(self) -> None:
        """최근 통계 렌더링"""
        recent_matches = self.match_service.get_recent_matches(5)
        
        if recent_matches:
            st.write("**최근 5경기**")
            for match in recent_matches:
                opponent = match.opponent or '팀내 경기'
                result = match.result or '결과 미입력'
                st.write(f"• {match.match_date} vs {opponent} - {result}")
        else:
            st.info("최근 경기 데이터가 없습니다.")
    
    def _render_recent_news(self) -> None:
        """최근 공지사항 렌더링"""
        recent_news = self.news_service.get_recent_news(3)
        
        if recent_news:
            for news in recent_news:
                st.write(f"**{news.title}**")
                st.caption(f"{news.created_at[:10]} - {news.author}")
                content = news.content[:100] + "..." if len(news.content) > 100 else news.content
                st.write(content)
                st.markdown("---")
        else:
            st.info("최근 공지사항이 없습니다.")

# 페이지 인스턴스
dashboard_page = DashboardPage()
```

#### ui/pages/schedule.py
```python
"""일정 관리 페이지"""
import streamlit as st
from datetime import datetime
from services.match_service import match_service
from services.field_service import field_service
from utils.validators import ValidationResult

class SchedulePage:
    """일정 관리 페이지"""
    
    def __init__(self):
        self.match_service = match_service
        self.field_service = field_service
    
    def render(self) -> None:
        """일정 관리 페이지 렌더링"""
        st.header("📅 일정 관리")
        
        tab1, tab2, tab3 = st.tabs(["경기 일정", "경기 추가", "필드 관리"])
        
        with tab1:
            self._render_match_schedule()
        
        with tab2:
            self._render_add_match()
        
        with tab3:
            self._render_field_management()
    
    def _render_match_schedule(self) -> None:
        """경기 일정 표시"""
        matches = self.match_service.get_all_matches()
        
        if matches:
            import pandas as pd
            
            # 데이터프레임 생성
            df_data = []
            for match in matches:
                df_data.append({
                    '날짜': match.match_date,
                    '시간': match.match_time,
                    '구장': match.field_name,
                    '상대팀': match.opponent or '-',
                    '결과': match.result or '-'
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("등록된 경기가 없습니다.")
    
    def _render_add_match(self) -> None:
        """경기 추가 폼"""
        fields = self.field_service.get_available_fields()
        
        if not fields:
            st.warning("먼저 구장을 등록해주세요.")
            if st.button("샘플 구장 추가"):
                self.field_service.create_sample_field()
                st.rerun()
            return
        
        with st.form("add_match_form"):
            # 구장 선택
            field_options = {field['display_name']: field['id'] for field in fields}
            selected_field = st.selectbox("구장 선택", options=list(field_options.keys()))
            
            # 날짜 입력
            match_date = st.date_input("경기 날짜", value=datetime.now().date())
            
            # 시간 선택
            time_options = self.match_service.get_time_options()
            selected_time_display = st.selectbox(
                "경기 시간",
                options=[display for _, display in time_options],
                index=13  # 기본값: 오후 7시
            )
            
            # 선택된 시간의 실제 값
            selected_time = next(time_str for time_str, display in time_options 
                               if display == selected_time_display)
            
            # 상대팀 입력
            opponent = st.text_input("상대팀 (선택사항)")
            
            # 폼 제출
            if st.form_submit_button("경기 추가"):
                try:
                    field_id = field_options[selected_field]
                    
                    success = self.match_service.create_match(
                        field_id=field_id,
                        match_date=match_date,
                        match_time=selected_time,
                        opponent=opponent
                    )
                    
                    if success:
                        st.success("경기가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error("경기 추가에 실패했습니다.")
                        
                except ValueError as e:
                    st.error(f"입력 데이터 오류: {e}")
                except Exception as e:
                    st.error(f"예상치 못한 오류: {e}")
    
    def _render_field_management(self) -> None:
        """필드 관리"""
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("새 구장 추가")
            self._render_add_field_form()
        
        with col2:
            st.subheader("등록된 구장")
            self._render_field_list()
    
    def _render_add_field_form(self) -> None:
        """구장 추가 폼"""
        with st.form("add_field_form"):
            name = st.text_input("구장명")
            address = st.text_input("주소")
            cost = st.number_input("대관료", min_value=0, step=10000)
            
            if st.form_submit_button("구장 추가"):
                if name:
                    try:
                        success = self.field_service.create_field(name, address, cost)
                        if success:
                            st.success("구장이 추가되었습니다!")
                            st.rerun()
                        else:
                            st.error("구장 추가에 실패했습니다.")
                    except Exception as e:
                        st.error(f"오류: {e}")
                else:
                    st.error("구장명을 입력해주세요.")
    
    def _render_field_list(self) -> None:
        """구장 목록 표시"""
        fields = self.field_service.get_all_fields()
        
        if fields:
            for field in fields:
                with st.expander(f"{field['name']}"):
                    st.write(f"**주소:** {field['address']}")
                    st.write(f"**대관료:** {field['cost']:,}원")
        else:
            st.info("등록된 구장이 없습니다.")

# 페이지 인스턴스
schedule_page = SchedulePage()
```

### 5. utils/ - 유틸리티

#### utils/validators.py
```python
"""입력 검증 함수들"""
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import date, datetime
import re

@dataclass
class ValidationResult:
    """검증 결과"""
    is_valid: bool
    errors: List[str]

def validate_match_data(data: Dict[str, Any]) -> ValidationResult:
    """경기 데이터 검증"""
    errors = []
    
    # 필수 필드 검증
    if not data.get('field_id'):
        errors.append("구장을 선택해주세요.")
    
    if not data.get('match_date'):
        errors.append("경기 날짜를 입력해주세요.")
    
    if not data.get('match_time'):
        errors.append("경기 시간을 선택해주세요.")
    
    # 날짜 검증
    match_date = data.get('match_date')
    if match_date and isinstance(match_date, date):
        if match_date < date.today():
            errors.append("과거 날짜는 선택할 수 없습니다.")
    
    # 시간 형식 검증
    match_time = data.get('match_time')
    if match_time and not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]# 🔧 Streamlit 풋살팀 플랫폼 리팩토링 계획

## 📋 현재 상태 분석

### 현재 코드 구조
```
app.py (단일 파일, ~1000+ 라인)
├── 설정 및 스타일
├── 데이터베이스 관련 함수들
├── UI 렌더링 함수들
├── 데이터 조회/조작 함수들
└── 메인 함수
```

### 주요 문제점
- **단일 파일 거대화**: 모든 기능이 하나의 파일에 집중
- **함수 책임 혼재**: UI, 비즈니스 로직, 데이터 액세스가 섞임
- **중복 코드**: 비슷한 데이터베이스 조작 패턴 반복
- **테스트 어려움**: 단위 테스트가 불가능한 구조
- **유지보수성**: 새로운 기능 추가 시 복잡도 증가

## 🎯 리팩토링 목표

### 1. 코드 분리 및 모듈화
- **관심사 분리** (Separation of Concerns)
- **단일 책임 원칙** (Single Responsibility Principle)
- **의존성 역전** (Dependency Inversion)

### 2. 확장성 및 유지보수성 향상
- 새로운 기능 추가 용이성
- 기존 기능 수정 시 사이드 이펙트 최소화
- 코드 재사용성 증대

### 3. 테스트 가능한 구조
- 단위 테스트 가능한 함수들
- 모킹 가능한 의존성 구조

## 🏗️ 새로운 프로젝트 구조

```
streamlit_team_platform/
├── README.md
├── requirements.txt
├── app.py                          # 메인 애플리케이션 엔트리포인트
├── config/
│   ├── __init__.py
│   ├── settings.py                 # 앱 설정 및 상수
│   └── database.py                 # 데이터베이스 설정
├── database/
│   ├── __init__.py
│   ├── connection.py               # DB 연결 관리
│   ├── models.py                   # 데이터 모델 정의
│   └── migrations.py               # 스키마 초기화 및 마이그레이션
├── services/
│   ├── __init__.py
│   ├── match_service.py            # 경기 관련 비즈니스 로직
│   ├── player_service.py           # 선수 관련 비즈니스 로직
│   ├── finance_service.py          # 재정 관련 비즈니스 로직
│   ├── news_service.py             # 소식 관련 비즈니스 로직
│   └── gallery_service.py          # 갤러리 관련 비즈니스 로직
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── calendar.py             # 달력 컴포넌트
│   │   ├── metrics.py              # 지표 카드 컴포넌트
│   │   └── forms.py                # 공통 폼 컴포넌트
│   └── pages/
│       ├── __init__.py
│       ├── dashboard.py            # 메인 대시보드
│       ├── schedule.py             # 일정 관리
│       ├── players.py              # 선수 관리
│       ├── statistics.py           # 통계
│       ├── news.py                 # 팀 소식
│       ├── gallery.py              # 갤러리
│       └── finance.py              # 재정 관리
├── utils/
│   ├── __init__.py
│   ├── validators.py               # 입력 검증 함수들
│   ├── formatters.py               # 데이터 포맷팅 함수들
│   └── security.py                 # 보안 관련 유틸리티
└── tests/
    ├── __init__.py
    ├── test_services/
    ├── test_ui/
    └── test_utils/
```

## 📦 모듈별 상세 계획

### 1. config/ - 설정 관리
```python
# config/settings.py
class AppConfig:
    DB_PATH = "team_platform.db"
    UPLOAD_DIR = "uploads"
    LOG_LEVEL = "INFO"
    
class UIConfig:
    PAGE_TITLE = "⚽ 우리팀 플랫폼"
    LAYOUT = "wide"
```

### 2. database/ - 데이터 계층
```python
# database/connection.py
class DatabaseManager:
    def __init__(self, db_path: str)
    def get_connection(self)
    def execute_query(self, query: str, params: tuple)
    def execute_transaction(self, queries: List[tuple])

# database/models.py
@dataclass
class Match:
    id: Optional[int]
    field_id: int
    match_date: date
    match_time: str
    opponent: str = ""
    result: str = ""

class MatchRepository:
    def create(self, match: Match) -> int
    def get_by_id(self, match_id: int) -> Optional[Match]
    def get_for_month(self, year: int, month: int) -> List[Match]
    def update(self, match: Match) -> bool
    def delete(self, match_id: int) -> bool
```

### 3. services/ - 비즈니스 로직
```python
# services/match_service.py
class MatchService:
    def __init__(self, match_repo: MatchRepository, field_repo: FieldRepository)
    
    def create_match(self, field_id: int, date: date, time: str, opponent: str) -> bool
    def get_next_match(self) -> Optional[Match]
    def get_monthly_matches(self, year: int, month: int) -> List[Match]
    def get_monthly_count(self) -> int
    def validate_match_data(self, data: dict) -> ValidationResult
```

### 4. ui/ - 프레젠테이션 계층
```python
# ui/components/calendar.py
class CalendarComponent:
    def __init__(self, match_service: MatchService)
    def render(self, year: int, month: int) -> None
    def _generate_calendar_html(self, matches: List[Match]) -> str
    def _handle_navigation(self) -> Tuple[int, int]

# ui/pages/dashboard.py
class DashboardPage:
    def __init__(self, services: dict)
    def render(self) -> None
    def _render_metrics(self) -> None
    def _render_calendar(self) -> None
    def _render_recent_stats(self) -> None
```

### 5. utils/ - 유틸리티
```python
# utils/validators.py
def validate_match_time(time_str: str) -> bool
def validate_file_path(file_path: str, allowed_dir: str) -> bool
def sanitize_input(user_input: str) -> str

# utils/formatters.py
def format_currency(amount: int) -> str
def format_date_korean(date: date) -> str
def format_time_display(time_str: str) -> str
```

## 🔄 마이그레이션 단계

### Phase 1: 기반 구조 설정
1. **프로젝트 구조 생성**
   - 디렉토리 및 `__init__.py` 파일 생성
   - 기본 설정 파일 작성

2. **설정 및 데이터베이스 계층 분리**
   - `config/` 모듈 구현
   - `database/` 모듈 구현
   - 기존 DB 코드 마이그레이션

### Phase 2: 서비스 계층 구현
1. **비즈니스 로직 분리**
   - 각 도메인별 서비스 클래스 구현
   - Repository 패턴 적용
   - 데이터 모델 정의

2. **서비스 단위 테스트 작성**
   - 핵심 비즈니스 로직 테스트
   - 모킹을 통한 의존성 분리

### Phase 3: UI 계층 리팩토링
1. **컴포넌트 분리**
   - 재사용 가능한 UI 컴포넌트 추출
   - 페이지별 모듈 분리

2. **의존성 주입 구현**
   - 서비스와 UI 계층 분리
   - 인터페이스 기반 의존성 관리

### Phase 4: 최적화 및 확장
1. **성능 최적화**
   - 쿼리 최적화
   - 캐싱 전략 구현
   - 메모리 사용량 최적화

2. **새로운 기능 추가**
   - 확장된 통계 기능
   - 실시간 알림
   - 데이터 내보내기/가져오기

## 🧪 테스트 전략

### 단위 테스트
```python
# tests/test_services/test_match_service.py
class TestMatchService:
    def test_create_match_success(self)
    def test_create_match_invalid_data(self)
    def test_get_next_match_exists(self)
    def test_get_next_match_none(self)
```

### 통합 테스트
```python
# tests/test_integration/test_match_workflow.py
class TestMatchWorkflow:
    def test_full_match_creation_workflow(self)
    def test_calendar_display_with_matches(self)
```

## 📊 예상 효과

### 개발 생산성 향상
- **모듈별 병렬 개발** 가능
- **코드 재사용성** 증대
- **버그 수정** 범위 최소화

### 코드 품질 향상
- **가독성** 향상 (함수당 평균 라인 수 50% 감소)
- **복잡도** 감소 (순환 복잡도 최대 10 이하)
- **테스트 커버리지** 80% 이상

### 유지보수성 향상
- **새로운 기능 추가** 시간 50% 단축
- **기존 기능 수정** 시 사이드 이펙트 최소화
- **문서화** 자동화 가능

## 🛠️ 리팩토링 체크리스트

### 코드 품질
- [ ] 함수당 라인 수 50라인 이하
- [ ] 클래스당 메서드 수 10개 이하
- [ ] 순환 복잡도 10 이하
- [ ] 중복 코드 제거

### 아키텍처
- [ ] 관심사 분리 완료
- [ ] 의존성 역전 적용
- [ ] 인터페이스 기반 설계
- [ ] 단일 책임 원칙 준수

### 테스트
- [ ] 단위 테스트 커버리지 80% 이상
- [ ] 통합 테스트 주요 워크플로우 커버
- [ ] 모킹 기반 테스트 구현
- [ ] CI/CD 파이프라인 구축

### 문서화
- [ ] README.md 업데이트
- [ ] API 문서 작성
- [ ] 아키텍처 다이어그램 작성
- [ ] 코드 주석 보완

## 🚀 다음 단계

1. **Phase 1 시작**: 기반 구조 설정
2. **점진적 마이그레이션**: 기능별 단계적 이관
3. **테스트 작성**: 각 단계마다 테스트 보완
4. **성능 모니터링**: 리팩토링 전후 성능 비교
5. **문서화**: 새로운 구조에 맞는 문서 작성

---

이 리팩토링을 통해 **유지보수 가능하고 확장 가능한 코드베이스**를 구축하여 팀 플랫폼의 지속적인 발전을 도모합니다., match_time):
        errors.append("올바른 시간 형식이 아닙니다. (HH:MM)")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)

def validate_player_data(data: Dict[str, Any]) -> ValidationResult:
    """선수 데이터 검증"""
    errors = []
    
    # 이름 검증
    name = data.get('name', '').strip()
    if not name:
        errors.append("이름을 입력해주세요.")
    elif len(name) < 2:
        errors.append("이름은 2글자 이상이어야 합니다.")
    
    # 포지션 검증
    position = data.get('position', '')
    valid_positions = ['GK', 'DF', 'MF', 'FW']
    if position not in valid_positions:
        errors.append(f"포지션은 {', '.join(valid_positions)} 중 하나여야 합니다.")
    
    # 전화번호 검증 (선택사항)
    phone = data.get('phone', '').strip()
    if phone and not re.match(r'^010-\d{4}-\d{4}# 🔧 Streamlit 풋살팀 플랫폼 리팩토링 계획

## 📋 현재 상태 분석

### 현재 코드 구조
```
app.py (단일 파일, ~1000+ 라인)
├── 설정 및 스타일
├── 데이터베이스 관련 함수들
├── UI 렌더링 함수들
├── 데이터 조회/조작 함수들
└── 메인 함수
```

### 주요 문제점
- **단일 파일 거대화**: 모든 기능이 하나의 파일에 집중
- **함수 책임 혼재**: UI, 비즈니스 로직, 데이터 액세스가 섞임
- **중복 코드**: 비슷한 데이터베이스 조작 패턴 반복
- **테스트 어려움**: 단위 테스트가 불가능한 구조
- **유지보수성**: 새로운 기능 추가 시 복잡도 증가

## 🎯 리팩토링 목표

### 1. 코드 분리 및 모듈화
- **관심사 분리** (Separation of Concerns)
- **단일 책임 원칙** (Single Responsibility Principle)
- **의존성 역전** (Dependency Inversion)

### 2. 확장성 및 유지보수성 향상
- 새로운 기능 추가 용이성
- 기존 기능 수정 시 사이드 이펙트 최소화
- 코드 재사용성 증대

### 3. 테스트 가능한 구조
- 단위 테스트 가능한 함수들
- 모킹 가능한 의존성 구조

## 🏗️ 새로운 프로젝트 구조

```
streamlit_team_platform/
├── README.md
├── requirements.txt
├── app.py                          # 메인 애플리케이션 엔트리포인트
├── config/
│   ├── __init__.py
│   ├── settings.py                 # 앱 설정 및 상수
│   └── database.py                 # 데이터베이스 설정
├── database/
│   ├── __init__.py
│   ├── connection.py               # DB 연결 관리
│   ├── models.py                   # 데이터 모델 정의
│   └── migrations.py               # 스키마 초기화 및 마이그레이션
├── services/
│   ├── __init__.py
│   ├── match_service.py            # 경기 관련 비즈니스 로직
│   ├── player_service.py           # 선수 관련 비즈니스 로직
│   ├── finance_service.py          # 재정 관련 비즈니스 로직
│   ├── news_service.py             # 소식 관련 비즈니스 로직
│   └── gallery_service.py          # 갤러리 관련 비즈니스 로직
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── calendar.py             # 달력 컴포넌트
│   │   ├── metrics.py              # 지표 카드 컴포넌트
│   │   └── forms.py                # 공통 폼 컴포넌트
│   └── pages/
│       ├── __init__.py
│       ├── dashboard.py            # 메인 대시보드
│       ├── schedule.py             # 일정 관리
│       ├── players.py              # 선수 관리
│       ├── statistics.py           # 통계
│       ├── news.py                 # 팀 소식
│       ├── gallery.py              # 갤러리
│       └── finance.py              # 재정 관리
├── utils/
│   ├── __init__.py
│   ├── validators.py               # 입력 검증 함수들
│   ├── formatters.py               # 데이터 포맷팅 함수들
│   └── security.py                 # 보안 관련 유틸리티
└── tests/
    ├── __init__.py
    ├── test_services/
    ├── test_ui/
    └── test_utils/
```

## 📦 모듈별 상세 계획

### 1. config/ - 설정 관리
```python
# config/settings.py
class AppConfig:
    DB_PATH = "team_platform.db"
    UPLOAD_DIR = "uploads"
    LOG_LEVEL = "INFO"
    
class UIConfig:
    PAGE_TITLE = "⚽ 우리팀 플랫폼"
    LAYOUT = "wide"
```

### 2. database/ - 데이터 계층
```python
# database/connection.py
class DatabaseManager:
    def __init__(self, db_path: str)
    def get_connection(self)
    def execute_query(self, query: str, params: tuple)
    def execute_transaction(self, queries: List[tuple])

# database/models.py
@dataclass
class Match:
    id: Optional[int]
    field_id: int
    match_date: date
    match_time: str
    opponent: str = ""
    result: str = ""

class MatchRepository:
    def create(self, match: Match) -> int
    def get_by_id(self, match_id: int) -> Optional[Match]
    def get_for_month(self, year: int, month: int) -> List[Match]
    def update(self, match: Match) -> bool
    def delete(self, match_id: int) -> bool
```

### 3. services/ - 비즈니스 로직
```python
# services/match_service.py
class MatchService:
    def __init__(self, match_repo: MatchRepository, field_repo: FieldRepository)
    
    def create_match(self, field_id: int, date: date, time: str, opponent: str) -> bool
    def get_next_match(self) -> Optional[Match]
    def get_monthly_matches(self, year: int, month: int) -> List[Match]
    def get_monthly_count(self) -> int
    def validate_match_data(self, data: dict) -> ValidationResult
```

### 4. ui/ - 프레젠테이션 계층
```python
# ui/components/calendar.py
class CalendarComponent:
    def __init__(self, match_service: MatchService)
    def render(self, year: int, month: int) -> None
    def _generate_calendar_html(self, matches: List[Match]) -> str
    def _handle_navigation(self) -> Tuple[int, int]

# ui/pages/dashboard.py
class DashboardPage:
    def __init__(self, services: dict)
    def render(self) -> None
    def _render_metrics(self) -> None
    def _render_calendar(self) -> None
    def _render_recent_stats(self) -> None
```

### 5. utils/ - 유틸리티
```python
# utils/validators.py
def validate_match_time(time_str: str) -> bool
def validate_file_path(file_path: str, allowed_dir: str) -> bool
def sanitize_input(user_input: str) -> str

# utils/formatters.py
def format_currency(amount: int) -> str
def format_date_korean(date: date) -> str
def format_time_display(time_str: str) -> str
```

## 🔄 마이그레이션 단계

### Phase 1: 기반 구조 설정
1. **프로젝트 구조 생성**
   - 디렉토리 및 `__init__.py` 파일 생성
   - 기본 설정 파일 작성

2. **설정 및 데이터베이스 계층 분리**
   - `config/` 모듈 구현
   - `database/` 모듈 구현
   - 기존 DB 코드 마이그레이션

### Phase 2: 서비스 계층 구현
1. **비즈니스 로직 분리**
   - 각 도메인별 서비스 클래스 구현
   - Repository 패턴 적용
   - 데이터 모델 정의

2. **서비스 단위 테스트 작성**
   - 핵심 비즈니스 로직 테스트
   - 모킹을 통한 의존성 분리

### Phase 3: UI 계층 리팩토링
1. **컴포넌트 분리**
   - 재사용 가능한 UI 컴포넌트 추출
   - 페이지별 모듈 분리

2. **의존성 주입 구현**
   - 서비스와 UI 계층 분리
   - 인터페이스 기반 의존성 관리

### Phase 4: 최적화 및 확장
1. **성능 최적화**
   - 쿼리 최적화
   - 캐싱 전략 구현
   - 메모리 사용량 최적화

2. **새로운 기능 추가**
   - 확장된 통계 기능
   - 실시간 알림
   - 데이터 내보내기/가져오기

## 🧪 테스트 전략

### 단위 테스트
```python
# tests/test_services/test_match_service.py
class TestMatchService:
    def test_create_match_success(self)
    def test_create_match_invalid_data(self)
    def test_get_next_match_exists(self)
    def test_get_next_match_none(self)
```

### 통합 테스트
```python
# tests/test_integration/test_match_workflow.py
class TestMatchWorkflow:
    def test_full_match_creation_workflow(self)
    def test_calendar_display_with_matches(self)
```

## 📊 예상 효과

### 개발 생산성 향상
- **모듈별 병렬 개발** 가능
- **코드 재사용성** 증대
- **버그 수정** 범위 최소화

### 코드 품질 향상
- **가독성** 향상 (함수당 평균 라인 수 50% 감소)
- **복잡도** 감소 (순환 복잡도 최대 10 이하)
- **테스트 커버리지** 80% 이상

### 유지보수성 향상
- **새로운 기능 추가** 시간 50% 단축
- **기존 기능 수정** 시 사이드 이펙트 최소화
- **문서화** 자동화 가능

## 🛠️ 리팩토링 체크리스트

### 코드 품질
- [ ] 함수당 라인 수 50라인 이하
- [ ] 클래스당 메서드 수 10개 이하
- [ ] 순환 복잡도 10 이하
- [ ] 중복 코드 제거

### 아키텍처
- [ ] 관심사 분리 완료
- [ ] 의존성 역전 적용
- [ ] 인터페이스 기반 설계
- [ ] 단일 책임 원칙 준수

### 테스트
- [ ] 단위 테스트 커버리지 80% 이상
- [ ] 통합 테스트 주요 워크플로우 커버
- [ ] 모킹 기반 테스트 구현
- [ ] CI/CD 파이프라인 구축

### 문서화
- [ ] README.md 업데이트
- [ ] API 문서 작성
- [ ] 아키텍처 다이어그램 작성
- [ ] 코드 주석 보완

## 🚀 다음 단계

1. **Phase 1 시작**: 기반 구조 설정
2. **점진적 마이그레이션**: 기능별 단계적 이관
3. **테스트 작성**: 각 단계마다 테스트 보완
4. **성능 모니터링**: 리팩토링 전후 성능 비교
5. **문서화**: 새로운 구조에 맞는 문서 작성

---

이 리팩토링을 통해 **유지보수 가능하고 확장 가능한 코드베이스**를 구축하여 팀 플랫폼의 지속적인 발전을 도모합니다., phone):
        errors.append("전화번호 형식이 올바르지 않습니다. (010-XXXX-XXXX)")
    
    # 이메일 검증 (선택사항)
    email = data.get('email', '').strip()
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}# 🔧 Streamlit 풋살팀 플랫폼 리팩토링 계획

## 📋 현재 상태 분석

### 현재 코드 구조
```
app.py (단일 파일, ~1000+ 라인)
├── 설정 및 스타일
├── 데이터베이스 관련 함수들
├── UI 렌더링 함수들
├── 데이터 조회/조작 함수들
└── 메인 함수
```

### 주요 문제점
- **단일 파일 거대화**: 모든 기능이 하나의 파일에 집중
- **함수 책임 혼재**: UI, 비즈니스 로직, 데이터 액세스가 섞임
- **중복 코드**: 비슷한 데이터베이스 조작 패턴 반복
- **테스트 어려움**: 단위 테스트가 불가능한 구조
- **유지보수성**: 새로운 기능 추가 시 복잡도 증가

## 🎯 리팩토링 목표

### 1. 코드 분리 및 모듈화
- **관심사 분리** (Separation of Concerns)
- **단일 책임 원칙** (Single Responsibility Principle)
- **의존성 역전** (Dependency Inversion)

### 2. 확장성 및 유지보수성 향상
- 새로운 기능 추가 용이성
- 기존 기능 수정 시 사이드 이펙트 최소화
- 코드 재사용성 증대

### 3. 테스트 가능한 구조
- 단위 테스트 가능한 함수들
- 모킹 가능한 의존성 구조

## 🏗️ 새로운 프로젝트 구조

```
streamlit_team_platform/
├── README.md
├── requirements.txt
├── app.py                          # 메인 애플리케이션 엔트리포인트
├── config/
│   ├── __init__.py
│   ├── settings.py                 # 앱 설정 및 상수
│   └── database.py                 # 데이터베이스 설정
├── database/
│   ├── __init__.py
│   ├── connection.py               # DB 연결 관리
│   ├── models.py                   # 데이터 모델 정의
│   └── migrations.py               # 스키마 초기화 및 마이그레이션
├── services/
│   ├── __init__.py
│   ├── match_service.py            # 경기 관련 비즈니스 로직
│   ├── player_service.py           # 선수 관련 비즈니스 로직
│   ├── finance_service.py          # 재정 관련 비즈니스 로직
│   ├── news_service.py             # 소식 관련 비즈니스 로직
│   └── gallery_service.py          # 갤러리 관련 비즈니스 로직
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── calendar.py             # 달력 컴포넌트
│   │   ├── metrics.py              # 지표 카드 컴포넌트
│   │   └── forms.py                # 공통 폼 컴포넌트
│   └── pages/
│       ├── __init__.py
│       ├── dashboard.py            # 메인 대시보드
│       ├── schedule.py             # 일정 관리
│       ├── players.py              # 선수 관리
│       ├── statistics.py           # 통계
│       ├── news.py                 # 팀 소식
│       ├── gallery.py              # 갤러리
│       └── finance.py              # 재정 관리
├── utils/
│   ├── __init__.py
│   ├── validators.py               # 입력 검증 함수들
│   ├── formatters.py               # 데이터 포맷팅 함수들
│   └── security.py                 # 보안 관련 유틸리티
└── tests/
    ├── __init__.py
    ├── test_services/
    ├── test_ui/
    └── test_utils/
```

## 📦 모듈별 상세 계획

### 1. config/ - 설정 관리
```python
# config/settings.py
class AppConfig:
    DB_PATH = "team_platform.db"
    UPLOAD_DIR = "uploads"
    LOG_LEVEL = "INFO"
    
class UIConfig:
    PAGE_TITLE = "⚽ 우리팀 플랫폼"
    LAYOUT = "wide"
```

### 2. database/ - 데이터 계층
```python
# database/connection.py
class DatabaseManager:
    def __init__(self, db_path: str)
    def get_connection(self)
    def execute_query(self, query: str, params: tuple)
    def execute_transaction(self, queries: List[tuple])

# database/models.py
@dataclass
class Match:
    id: Optional[int]
    field_id: int
    match_date: date
    match_time: str
    opponent: str = ""
    result: str = ""

class MatchRepository:
    def create(self, match: Match) -> int
    def get_by_id(self, match_id: int) -> Optional[Match]
    def get_for_month(self, year: int, month: int) -> List[Match]
    def update(self, match: Match) -> bool
    def delete(self, match_id: int) -> bool
```

### 3. services/ - 비즈니스 로직
```python
# services/match_service.py
class MatchService:
    def __init__(self, match_repo: MatchRepository, field_repo: FieldRepository)
    
    def create_match(self, field_id: int, date: date, time: str, opponent: str) -> bool
    def get_next_match(self) -> Optional[Match]
    def get_monthly_matches(self, year: int, month: int) -> List[Match]
    def get_monthly_count(self) -> int
    def validate_match_data(self, data: dict) -> ValidationResult
```

### 4. ui/ - 프레젠테이션 계층
```python
# ui/components/calendar.py
class CalendarComponent:
    def __init__(self, match_service: MatchService)
    def render(self, year: int, month: int) -> None
    def _generate_calendar_html(self, matches: List[Match]) -> str
    def _handle_navigation(self) -> Tuple[int, int]

# ui/pages/dashboard.py
class DashboardPage:
    def __init__(self, services: dict)
    def render(self) -> None
    def _render_metrics(self) -> None
    def _render_calendar(self) -> None
    def _render_recent_stats(self) -> None
```

### 5. utils/ - 유틸리티
```python
# utils/validators.py
def validate_match_time(time_str: str) -> bool
def validate_file_path(file_path: str, allowed_dir: str) -> bool
def sanitize_input(user_input: str) -> str

# utils/formatters.py
def format_currency(amount: int) -> str
def format_date_korean(date: date) -> str
def format_time_display(time_str: str) -> str
```

## 🔄 마이그레이션 단계

### Phase 1: 기반 구조 설정
1. **프로젝트 구조 생성**
   - 디렉토리 및 `__init__.py` 파일 생성
   - 기본 설정 파일 작성

2. **설정 및 데이터베이스 계층 분리**
   - `config/` 모듈 구현
   - `database/` 모듈 구현
   - 기존 DB 코드 마이그레이션

### Phase 2: 서비스 계층 구현
1. **비즈니스 로직 분리**
   - 각 도메인별 서비스 클래스 구현
   - Repository 패턴 적용
   - 데이터 모델 정의

2. **서비스 단위 테스트 작성**
   - 핵심 비즈니스 로직 테스트
   - 모킹을 통한 의존성 분리

### Phase 3: UI 계층 리팩토링
1. **컴포넌트 분리**
   - 재사용 가능한 UI 컴포넌트 추출
   - 페이지별 모듈 분리

2. **의존성 주입 구현**
   - 서비스와 UI 계층 분리
   - 인터페이스 기반 의존성 관리

### Phase 4: 최적화 및 확장
1. **성능 최적화**
   - 쿼리 최적화
   - 캐싱 전략 구현
   - 메모리 사용량 최적화

2. **새로운 기능 추가**
   - 확장된 통계 기능
   - 실시간 알림
   - 데이터 내보내기/가져오기

## 🧪 테스트 전략

### 단위 테스트
```python
# tests/test_services/test_match_service.py
class TestMatchService:
    def test_create_match_success(self)
    def test_create_match_invalid_data(self)
    def test_get_next_match_exists(self)
    def test_get_next_match_none(self)
```

### 통합 테스트
```python
# tests/test_integration/test_match_workflow.py
class TestMatchWorkflow:
    def test_full_match_creation_workflow(self)
    def test_calendar_display_with_matches(self)
```

## 📊 예상 효과

### 개발 생산성 향상
- **모듈별 병렬 개발** 가능
- **코드 재사용성** 증대
- **버그 수정** 범위 최소화

### 코드 품질 향상
- **가독성** 향상 (함수당 평균 라인 수 50% 감소)
- **복잡도** 감소 (순환 복잡도 최대 10 이하)
- **테스트 커버리지** 80% 이상

### 유지보수성 향상
- **새로운 기능 추가** 시간 50% 단축
- **기존 기능 수정** 시 사이드 이펙트 최소화
- **문서화** 자동화 가능

## 🛠️ 리팩토링 체크리스트

### 코드 품질
- [ ] 함수당 라인 수 50라인 이하
- [ ] 클래스당 메서드 수 10개 이하
- [ ] 순환 복잡도 10 이하
- [ ] 중복 코드 제거

### 아키텍처
- [ ] 관심사 분리 완료
- [ ] 의존성 역전 적용
- [ ] 인터페이스 기반 설계
- [ ] 단일 책임 원칙 준수

### 테스트
- [ ] 단위 테스트 커버리지 80% 이상
- [ ] 통합 테스트 주요 워크플로우 커버
- [ ] 모킹 기반 테스트 구현
- [ ] CI/CD 파이프라인 구축

### 문서화
- [ ] README.md 업데이트
- [ ] API 문서 작성
- [ ] 아키텍처 다이어그램 작성
- [ ] 코드 주석 보완

## 🚀 다음 단계

1. **Phase 1 시작**: 기반 구조 설정
2. **점진적 마이그레이션**: 기능별 단계적 이관
3. **테스트 작성**: 각 단계마다 테스트 보완
4. **성능 모니터링**: 리팩토링 전후 성능 비교
5. **문서화**: 새로운 구조에 맞는 문서 작성

---

이 리팩토링을 통해 **유지보수 가능하고 확장 가능한 코드베이스**를 구축하여 팀 플랫폼의 지속적인 발전을 도모합니다., email):
        errors.append("이메일 형식이 올바르지 않습니다.")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)

def validate_file_path(file_path: str, allowed_dir: str = "uploads") -> bool:
    """파일 경로 검증"""
    import os.path
    try:
        abs_path = os.path.abspath(file_path)
        allowed_path = os.path.abspath(allowed_dir)
        return abs_path.startswith(allowed_path)
    except Exception:
        return False

def sanitize_input(user_input: str) -> str:
    """사용자 입력 정제"""
    if not isinstance(user_input, str):
        return ""
    
    # HTML 태그 제거
    import html
    sanitized = html.escape(user_input.strip())
    
    # 특수 문자 제한
    # 필요에 따라 추가 정제 로직 구현
    
    return sanitized
```

#### utils/formatters.py
```python
"""데이터 포맷팅 함수들"""
from typing import List, Tuple
from datetime import date
from config.settings import ui_config

def format_currency(amount: int) -> str:
    """통화 포맷팅"""
    return f"{amount:,}원"

def format_date_korean(date_obj: date) -> str:
    """한국어 날짜 포맷팅"""
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[date_obj.weekday()]
    return f"{date_obj.year}년 {date_obj.month}월 {date_obj.day}일 ({weekday})"

def format_time_display(time_str: str) -> str:
    """시간 표시 포맷팅"""
    try:
        hour = int(time_str.split(':')[0])
        if hour < 12:
            return f"오전 {hour}시" if hour != 0 else "오전 12시"
        else:
            display_hour = hour - 12 if hour != 12 else 12
            return f"오후 {display_hour}시"
    except:
        return time_str

def format_time_options() -> List[Tuple[str, str]]:
    """시간 선택 옵션 생성"""
    time_options = []
    
    for hour in range(ui_config.CALENDAR_START_HOUR, ui_config.CALENDAR_END_HOUR + 1):
        time_str = f"{hour:02d}:00"
        display_time = format_time_display(time_str)
        time_options.append((time_str, display_time))
    
    return time_options

def format_phone_number(phone: str) -> str:
    """전화번호 포맷팅"""
    # 숫자만 추출
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 11 and digits.startswith('010'):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    return phone

def format_file_size(size_bytes: int) -> str:
    """파일 크기 포맷팅"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"
```

## 🔄 Claude Code 실행 가이드

### 📋 각 Phase별 통합 명령어

#### Phase 1: 기반 구조 설정
```bash
claude-code "Phase 1을 수행해줘:
1. README.md에 정의된 프로젝트 구조대로 모든 디렉토리와 __init__.py 파일 생성
2. config/settings.py와 config/database.py를 README.md 예시 코드 그대로 구현
3. 현재 app.py의 DB_PATH, UPLOAD_DIR 등 상수들을 config/settings.py로 이관
4. database/connection.py를 README.md 예시대로 구현하고 현재 app.py의 get_db_connection 함수를 DatabaseManager로 교체"
```

#### Phase 2: 데이터 계층 구현
```bash
claude-code "Phase 2를 수행해줘:
1. database/models.py를 README.md 예시대로 구현 (Player, Match, Field 등 모든 dataclass)
2. database/repositories.py를 README.md 예시대로 구현
3. 현재 app.py의 다음 함수들을 해당 Repository로 이관:
   - get_next_match, get_total_players, get_monthly_match_count → MatchRepository
   - get_players_list, add_player → PlayerRepository  
   - get_fields_list, add_field → FieldRepository
4. database/migrations.py 구현하고 init_complete_db 함수 이관
5. 기존 함수들이 새로운 Repository를 사용하도록 app.py 수정"
```

#### Phase 3: 서비스 계층 구현
```bash
claude-code "Phase 3을 수행해줘:
1. services/match_service.py를 README.md 예시대로 구현
2. services/player_service.py를 README.md 예시대로 구현
3. services/field_service.py, services/finance_service.py, services/news_service.py 구현
4. utils/validators.py와 utils/formatters.py를 README.md 예시대로 구현
5. 현재 app.py의 비즈니스 로직을 해당 서비스로 이관
6. 모든 UI 함수들이 Repository 대신 Service를 사용하도록 수정"
```

#### Phase 4: UI 계층 리팩토링
```bash
claude-code "Phase 4를 수행해줘:
1. ui/components/calendar.py를 README.md 예시대로 구현하고 render_calendar_view 함수 이관
2. ui/components/metrics.py 구현하고 메인 지표 관련 코드 이관
3. ui/pages/dashboard.py 구현하고 render_main_dashboard 함수 이관
4. ui/pages/schedule.py 구현하고 일정 관리 관련 함수들 이관
5. 나머지 페이지들(players.py, statistics.py, news.py, gallery.py, finance.py) 구현
6. app.py를 간단한 엔트리포인트로 정리 (페이지 라우팅만 담당)
7. 모든 import문 정리하고 순환 참조 해결"
```

### 🎯 Phase별 개별 실행 명령어 (상세 버전)

#### Phase 1 세부 명령어
```bash
# 1-1. 프로젝트 구조 생성
claude-code "프로젝트 구조 생성:
streamlit_team_platform/ 디렉토리에 config/, database/, services/, ui/, utils/, tests/ 폴더와 
각각의 __init__.py 파일을 생성해줘. ui/ 안에는 components/, pages/ 서브폴더도 만들어줘"

# 1-2. 설정 모듈 구현
claude-code "config/settings.py 구현:
README.md의 DatabaseConfig, AppConfig, UIConfig 클래스를 그대로 복사해서 구현하고,
현재 app.py의 DB_PATH, UPLOAD_DIR 상수들을 이 설정으로 교체해줘"
```

#### Phase 2 세부 명령어  
```bash
# 2-1. 데이터 모델 구현
claude-code "database/models.py 구현:
README.md의 Player, Match, Field, PlayerStats, News, FinanceRecord dataclass들을 그대로 구현해줘"

# 2-2. Repository 구현
claude-code "database/repositories.py 구현:
README.md의 MatchRepository, PlayerRepository, FieldRepository 클래스를 그대로 구현하고,
현재 app.py의 get_next_match, get_total_players 함수들을 해당 Repository 메서드로 이관해줘"
```

### 🚨 Claude Code 주의사항

#### ✅ 효과적인 명령어
```bash
claude-code "Phase 2를 완전히 수행해줘. README.md의 모든 예시 코드를 참고해서 
database/ 모듈을 완성하고 기존 app.py 함수들을 이관해줘"
```

#### ❌ 피해야 할 명령어  
```bash
claude-code "리팩토링 해줘"  # 너무 추상적
claude-code "코드 정리해줘"  # 구체적이지 않음
```

### 🔍 검증 명령어
```bash
# 각 Phase 완료 후 실행
claude-code "방금 수행한 리팩토링이 정상 작동하는지 확인하기 위한 
간단한 테스트 코드를 작성하고 실행해줘"

# 전체 완료 후 실행
claude-code "리팩토링된 전체 애플리케이션이 기존과 동일하게 작동하는지 
streamlit run app.py로 테스트하고 문제가 있으면 수정해줘"
```

### 💡 권장 실행 순서

1. **전체 Phase 한 번에**: `claude-code "Phase 2를 수행해줘"` (권장)
2. **문제 발생 시 세부 단위로**: 개별 명령어 사용
3. **검증**: 각 Phase 후 테스트 실행

---

**이제 "claude-code 'Phase 2를 수행해줘'"라고 간단히 명령하면 됩니다!** 🚀

## 🎯 리팩토링 완료 후 기대효과

### 개발 생산성 향상 (예상 개선율)
- **새 기능 개발 속도**: 50% 향상
- **버그 수정 시간**: 70% 단축  
- **코드 재사용성**: 80% 향상

### 코드 품질 지표
- **함수당 평균 라인 수**: 현재 50+ → 목표 20-
- **파일당 라인 수**: 현재 1000+ → 목표 200-
- **순환 복잡도**: 목표 10 이하
- **테스트 커버리지**: 목표 80%+

---

**이 README.md를 Claude Code에게 제공하면, 단계별로 체계적인 리팩토링을 진행할 수 있습니다!** 🚀# 🔧 Streamlit 풋살팀 플랫폼 리팩토링 계획

## 📋 현재 상태 분석

### 현재 코드 구조
```
app.py (단일 파일, ~1000+ 라인)
├── 설정 및 스타일
├── 데이터베이스 관련 함수들
├── UI 렌더링 함수들
├── 데이터 조회/조작 함수들
└── 메인 함수
```

### 주요 문제점
- **단일 파일 거대화**: 모든 기능이 하나의 파일에 집중
- **함수 책임 혼재**: UI, 비즈니스 로직, 데이터 액세스가 섞임
- **중복 코드**: 비슷한 데이터베이스 조작 패턴 반복
- **테스트 어려움**: 단위 테스트가 불가능한 구조
- **유지보수성**: 새로운 기능 추가 시 복잡도 증가

## 🎯 리팩토링 목표

### 1. 코드 분리 및 모듈화
- **관심사 분리** (Separation of Concerns)
- **단일 책임 원칙** (Single Responsibility Principle)
- **의존성 역전** (Dependency Inversion)

### 2. 확장성 및 유지보수성 향상
- 새로운 기능 추가 용이성
- 기존 기능 수정 시 사이드 이펙트 최소화
- 코드 재사용성 증대

### 3. 테스트 가능한 구조
- 단위 테스트 가능한 함수들
- 모킹 가능한 의존성 구조

## 🏗️ 새로운 프로젝트 구조

```
streamlit_team_platform/
├── README.md
├── requirements.txt
├── app.py                          # 메인 애플리케이션 엔트리포인트
├── config/
│   ├── __init__.py
│   ├── settings.py                 # 앱 설정 및 상수
│   └── database.py                 # 데이터베이스 설정
├── database/
│   ├── __init__.py
│   ├── connection.py               # DB 연결 관리
│   ├── models.py                   # 데이터 모델 정의
│   └── migrations.py               # 스키마 초기화 및 마이그레이션
├── services/
│   ├── __init__.py
│   ├── match_service.py            # 경기 관련 비즈니스 로직
│   ├── player_service.py           # 선수 관련 비즈니스 로직
│   ├── finance_service.py          # 재정 관련 비즈니스 로직
│   ├── news_service.py             # 소식 관련 비즈니스 로직
│   └── gallery_service.py          # 갤러리 관련 비즈니스 로직
├── ui/
│   ├── __init__.py
│   ├── components/
│   │   ├── __init__.py
│   │   ├── calendar.py             # 달력 컴포넌트
│   │   ├── metrics.py              # 지표 카드 컴포넌트
│   │   └── forms.py                # 공통 폼 컴포넌트
│   └── pages/
│       ├── __init__.py
│       ├── dashboard.py            # 메인 대시보드
│       ├── schedule.py             # 일정 관리
│       ├── players.py              # 선수 관리
│       ├── statistics.py           # 통계
│       ├── news.py                 # 팀 소식
│       ├── gallery.py              # 갤러리
│       └── finance.py              # 재정 관리
├── utils/
│   ├── __init__.py
│   ├── validators.py               # 입력 검증 함수들
│   ├── formatters.py               # 데이터 포맷팅 함수들
│   └── security.py                 # 보안 관련 유틸리티
└── tests/
    ├── __init__.py
    ├── test_services/
    ├── test_ui/
    └── test_utils/
```

## 📦 모듈별 상세 계획

### 1. config/ - 설정 관리
```python
# config/settings.py
class AppConfig:
    DB_PATH = "team_platform.db"
    UPLOAD_DIR = "uploads"
    LOG_LEVEL = "INFO"
    
class UIConfig:
    PAGE_TITLE = "⚽ 우리팀 플랫폼"
    LAYOUT = "wide"
```

### 2. database/ - 데이터 계층
```python
# database/connection.py
class DatabaseManager:
    def __init__(self, db_path: str)
    def get_connection(self)
    def execute_query(self, query: str, params: tuple)
    def execute_transaction(self, queries: List[tuple])

# database/models.py
@dataclass
class Match:
    id: Optional[int]
    field_id: int
    match_date: date
    match_time: str
    opponent: str = ""
    result: str = ""

class MatchRepository:
    def create(self, match: Match) -> int
    def get_by_id(self, match_id: int) -> Optional[Match]
    def get_for_month(self, year: int, month: int) -> List[Match]
    def update(self, match: Match) -> bool
    def delete(self, match_id: int) -> bool
```

### 3. services/ - 비즈니스 로직
```python
# services/match_service.py
class MatchService:
    def __init__(self, match_repo: MatchRepository, field_repo: FieldRepository)
    
    def create_match(self, field_id: int, date: date, time: str, opponent: str) -> bool
    def get_next_match(self) -> Optional[Match]
    def get_monthly_matches(self, year: int, month: int) -> List[Match]
    def get_monthly_count(self) -> int
    def validate_match_data(self, data: dict) -> ValidationResult
```

### 4. ui/ - 프레젠테이션 계층
```python
# ui/components/calendar.py
class CalendarComponent:
    def __init__(self, match_service: MatchService)
    def render(self, year: int, month: int) -> None
    def _generate_calendar_html(self, matches: List[Match]) -> str
    def _handle_navigation(self) -> Tuple[int, int]

# ui/pages/dashboard.py
class DashboardPage:
    def __init__(self, services: dict)
    def render(self) -> None
    def _render_metrics(self) -> None
    def _render_calendar(self) -> None
    def _render_recent_stats(self) -> None
```

### 5. utils/ - 유틸리티
```python
# utils/validators.py
def validate_match_time(time_str: str) -> bool
def validate_file_path(file_path: str, allowed_dir: str) -> bool
def sanitize_input(user_input: str) -> str

# utils/formatters.py
def format_currency(amount: int) -> str
def format_date_korean(date: date) -> str
def format_time_display(time_str: str) -> str
```

## 🔄 마이그레이션 단계

### Phase 1: 기반 구조 설정
1. **프로젝트 구조 생성**
   - 디렉토리 및 `__init__.py` 파일 생성
   - 기본 설정 파일 작성

2. **설정 및 데이터베이스 계층 분리**
   - `config/` 모듈 구현
   - `database/` 모듈 구현
   - 기존 DB 코드 마이그레이션

### Phase 2: 서비스 계층 구현
1. **비즈니스 로직 분리**
   - 각 도메인별 서비스 클래스 구현
   - Repository 패턴 적용
   - 데이터 모델 정의

2. **서비스 단위 테스트 작성**
   - 핵심 비즈니스 로직 테스트
   - 모킹을 통한 의존성 분리

### Phase 3: UI 계층 리팩토링
1. **컴포넌트 분리**
   - 재사용 가능한 UI 컴포넌트 추출
   - 페이지별 모듈 분리

2. **의존성 주입 구현**
   - 서비스와 UI 계층 분리
   - 인터페이스 기반 의존성 관리

### Phase 4: 최적화 및 확장
1. **성능 최적화**
   - 쿼리 최적화
   - 캐싱 전략 구현
   - 메모리 사용량 최적화

2. **새로운 기능 추가**
   - 확장된 통계 기능
   - 실시간 알림
   - 데이터 내보내기/가져오기

## 🧪 테스트 전략

### 단위 테스트
```python
# tests/test_services/test_match_service.py
class TestMatchService:
    def test_create_match_success(self)
    def test_create_match_invalid_data(self)
    def test_get_next_match_exists(self)
    def test_get_next_match_none(self)
```

### 통합 테스트
```python
# tests/test_integration/test_match_workflow.py
class TestMatchWorkflow:
    def test_full_match_creation_workflow(self)
    def test_calendar_display_with_matches(self)
```

## 📊 예상 효과

### 개발 생산성 향상
- **모듈별 병렬 개발** 가능
- **코드 재사용성** 증대
- **버그 수정** 범위 최소화

### 코드 품질 향상
- **가독성** 향상 (함수당 평균 라인 수 50% 감소)
- **복잡도** 감소 (순환 복잡도 최대 10 이하)
- **테스트 커버리지** 80% 이상

### 유지보수성 향상
- **새로운 기능 추가** 시간 50% 단축
- **기존 기능 수정** 시 사이드 이펙트 최소화
- **문서화** 자동화 가능

## 🛠️ 리팩토링 체크리스트

### 코드 품질
- [ ] 함수당 라인 수 50라인 이하
- [ ] 클래스당 메서드 수 10개 이하
- [ ] 순환 복잡도 10 이하
- [ ] 중복 코드 제거

### 아키텍처
- [ ] 관심사 분리 완료
- [ ] 의존성 역전 적용
- [ ] 인터페이스 기반 설계
- [ ] 단일 책임 원칙 준수

### 테스트
- [ ] 단위 테스트 커버리지 80% 이상
- [ ] 통합 테스트 주요 워크플로우 커버
- [ ] 모킹 기반 테스트 구현
- [ ] CI/CD 파이프라인 구축

### 문서화
- [ ] README.md 업데이트
- [ ] API 문서 작성
- [ ] 아키텍처 다이어그램 작성
- [ ] 코드 주석 보완

## 🚀 다음 단계

1. **Phase 1 시작**: 기반 구조 설정
2. **점진적 마이그레이션**: 기능별 단계적 이관
3. **테스트 작성**: 각 단계마다 테스트 보완
4. **성능 모니터링**: 리팩토링 전후 성능 비교
5. **문서화**: 새로운 구조에 맞는 문서 작성

---

이 리팩토링을 통해 **유지보수 가능하고 확장 가능한 코드베이스**를 구축하여 팀 플랫폼의 지속적인 발전을 도모합니다.