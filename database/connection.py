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

                # INSERT의 경우 lastrowid 반환
                if query.strip().upper().startswith('INSERT'):
                    conn.commit()
                    return cur.lastrowid

                # UPDATE, DELETE 등의 경우 커밋 및 rowcount 반환
                if query.strip().upper().startswith(('UPDATE', 'DELETE')):
                    conn.commit()
                    return cur.rowcount

                return cur.fetchall() if fetch_all else cur.fetchone()

        except sqlite3.Error as e:
            logger.error(f"Query execution error: {e}")
            return None

# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()