"""데이터베이스 마이그레이션 및 초기화"""
import sqlite3
import logging
from contextlib import contextmanager
from config.settings import db_config

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """안전한 데이터베이스 연결 컨텍스트 매니저"""
    conn = None
    try:
        conn = sqlite3.connect(db_config.DB_PATH)
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

def init_complete_db():
    """완전한 데이터베이스 초기화"""
    with get_db_connection() as conn:
        cur = conn.cursor()

        # 플레이어 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS players(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT,
                phone TEXT,
                email TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 필드 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fields(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                cost INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 경기 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS matches(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER NOT NULL,
                match_date TEXT NOT NULL,
                match_time TEXT NOT NULL,
                opponent TEXT DEFAULT '',
                result TEXT DEFAULT '',
                attendance_lock_minutes INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(field_id) REFERENCES fields(id)
            );
        """)

        # 기존 테이블에 attendance_lock_minutes 컬럼 추가 (마이그레이션)
        try:
            cur.execute("ALTER TABLE matches ADD COLUMN attendance_lock_minutes INTEGER NOT NULL DEFAULT 0")
            logger.info("Added attendance_lock_minutes column to matches table")
        except sqlite3.OperationalError as e:
            # 컬럼이 이미 존재하는 경우 무시
            if "duplicate column" in str(e).lower():
                logger.info("attendance_lock_minutes column already exists")
            else:
                raise

        # 출석 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                status TEXT CHECK(status IN ('present','absent','pending')) DEFAULT 'absent',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(match_id) REFERENCES matches(id),
                FOREIGN KEY(player_id) REFERENCES players(id),
                UNIQUE(match_id, player_id)
            );
        """)

        # 선수 통계 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS player_stats(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                match_id INTEGER NOT NULL,
                goals INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                saves INTEGER DEFAULT 0,
                yellow_cards INTEGER DEFAULT 0,
                red_cards INTEGER DEFAULT 0,
                mvp INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(player_id) REFERENCES players(id),
                FOREIGN KEY(match_id) REFERENCES matches(id),
                UNIQUE(player_id, match_id)
            );
        """)

        # 팀 소식/공지 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS news(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                pinned INTEGER DEFAULT 0,
                category TEXT DEFAULT 'general'
            );
        """)

        # 사진 갤러리 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gallery(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                file_path TEXT NOT NULL,
                upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
                match_id INTEGER DEFAULT NULL,
                FOREIGN KEY(match_id) REFERENCES matches(id)
            );
        """)

        # 팀 재정 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS finances(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount INTEGER NOT NULL,
                type TEXT CHECK(type IN ('income','expense')) NOT NULL,
                category TEXT DEFAULT 'match',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 관리자 테이블
        create_admins_table(cur)

        # 동영상 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                original_filename TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                duration INTEGER DEFAULT NULL,
                status TEXT CHECK(status IN ('pending','processing','completed','failed')) DEFAULT 'pending',
                hls_path TEXT DEFAULT NULL,
                thumbnail_path TEXT DEFAULT NULL,
                match_id INTEGER DEFAULT NULL,
                uploaded_by INTEGER DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                processed_at TEXT DEFAULT NULL,
                FOREIGN KEY(match_id) REFERENCES matches(id),
                FOREIGN KEY(uploaded_by) REFERENCES admins(id)
            );
        """)

        # 비디오 재생 로그 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS video_logs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                level TEXT CHECK(level IN ('info','warn','error')) DEFAULT 'info',
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT DEFAULT NULL,
                user_agent TEXT DEFAULT NULL,
                ip_address TEXT DEFAULT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                url TEXT DEFAULT NULL,
                FOREIGN KEY(video_id) REFERENCES videos(id)
            );
        """)

        # 비디오 로그 인덱스 (빠른 조회를 위해)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_logs_video_id
            ON video_logs(video_id);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_logs_timestamp
            ON video_logs(timestamp DESC);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_video_logs_level
            ON video_logs(level);
        """)

        # 팀 구성 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS team_distributions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                team_data TEXT NOT NULL,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(match_id) REFERENCES matches(id),
                FOREIGN KEY(created_by) REFERENCES admins(id),
                UNIQUE(match_id)
            );
        """)

        # 초기 샘플 데이터 삽입
        create_sample_data(cur)

        conn.commit()

def create_admins_table(cur):
    """관리자 테이블 생성 및 기본 관리자 데이터 삽입"""
    import bcrypt
    import secrets

    # 관리자 테이블 생성
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT DEFAULT NULL,
            is_active INTEGER DEFAULT 1
        );
    """)

    # 기본 관리자 계정이 없는 경우 생성
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        # 보안 강화: 랜덤 비밀번호 생성
        admin_password_raw = secrets.token_urlsafe(12)
        captain_password_raw = secrets.token_urlsafe(12)
        manager_password_raw = secrets.token_urlsafe(12)

        # 비밀번호 해시 생성
        admin_password = bcrypt.hashpw(admin_password_raw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        captain_password = bcrypt.hashpw(captain_password_raw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        manager_password = bcrypt.hashpw(manager_password_raw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        default_admins = [
            ('admin', admin_password, '시스템 관리자'),
            ('captain', captain_password, '김팀장'),
            ('manager', manager_password, '이총무')
        ]

        cur.executemany(
            "INSERT INTO admins (username, password_hash, name) VALUES (?, ?, ?)",
            default_admins
        )

        # 초기 비밀번호를 콘솔에 출력 (보안상 한 번만 표시)
        print("\n" + "="*60)
        print("🔐 초기 관리자 계정이 생성되었습니다.")
        print("="*60)
        print(f"👤 admin     (시스템 관리자): {admin_password_raw}")
        print(f"👤 captain   (김팀장):        {captain_password_raw}")
        print(f"👤 manager   (이총무):        {manager_password_raw}")
        print("="*60)
        print("⚠️  이 비밀번호들을 안전한 곳에 저장하고 즉시 변경하세요!")
        print("="*60 + "\n")

def create_sample_data(cur):
    """초기 샘플 데이터 생성"""
    try:
        # 샘플 플레이어 데이터
        cur.execute("SELECT COUNT(*) FROM players")
        if cur.fetchone()[0] == 0:
            players = [
                ("김철수", "FW", "010-1234-5678", "kim@email.com"),
                ("이영희", "MF", "010-2345-6789", "lee@email.com"),
                ("박민수", "DF", "010-3456-7890", "park@email.com"),
                ("최준호", "GK", "010-4567-8901", "choi@email.com"),
                ("정수진", "MF", "010-5678-9012", "jung@email.com")
            ]
            cur.executemany(
                "INSERT INTO players (name, position, phone, email) VALUES (?, ?, ?, ?)",
                players
            )

        # 샘플 필드 데이터
        cur.execute("SELECT COUNT(*) FROM fields")
        if cur.fetchone()[0] == 0:
            fields = [
                ("중앙 풋살장", "서울시 강남구 테헤란로 123", 100000),
                ("스포츠몬스터", "서울시 서초구 서초대로 456", 120000),
                ("킥오프 풋살장", "서울시 송파구 올림픽로 789", 80000)
            ]
            cur.executemany(
                "INSERT INTO fields (name, address, cost) VALUES (?, ?, ?)",
                fields
            )

        # 샘플 재정 데이터
        cur.execute("SELECT COUNT(*) FROM finances")
        if cur.fetchone()[0] == 0:
            finances = [
                ("2024-01-15", "회비 수납", 500000, "income", "dues"),
                ("2024-01-20", "풋살장 대관료", 100000, "expense", "match"),
                ("2024-02-10", "회비 수납", 600000, "income", "dues"),
                ("2024-02-25", "풋살장 대관료", 120000, "expense", "match"),
                ("2024-03-05", "유니폼 제작비", 300000, "expense", "equipment")
            ]
            cur.executemany(
                "INSERT INTO finances (date, description, amount, type, category) VALUES (?, ?, ?, ?, ?)",
                finances
            )

    except sqlite3.Error as e:
        logger.error(f"Error creating sample data: {e}")