"""데이터 액세스 계층 - Repository 패턴"""
from typing import List, Optional, Dict, Any
from datetime import date
import json
from database.connection import db_manager
from database.models import Match, Player, Field, PlayerStats, News, FinanceRecord, Gallery, Attendance, Admin, Video, TeamDistribution

class MatchRepository:
    """경기 데이터 액세스"""

    def create(self, match: Match) -> bool:
        """경기 생성"""
        query = """
            INSERT INTO matches (field_id, match_date, match_time, opponent, result, attendance_lock_minutes, attendance_capacity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(
            query,
            (match.field_id, str(match.match_date), match.match_time, match.opponent, match.result, match.attendance_lock_minutes, match.attendance_capacity)
        )
        return result is not None and result > 0

    def get_by_id(self, match_id: int) -> Optional[Dict[str, Any]]:
        """ID로 경기 조회"""
        query = """
            SELECT m.*, f.name as field_name
            FROM matches m
            JOIN fields f ON f.id = m.field_id
            WHERE m.id = ?
        """
        result = db_manager.execute_query(query, (match_id,), fetch_all=False)
        return dict(result) if result else None

    def get_for_month(self, year: int, month: int) -> List[Dict[str, Any]]:
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
        return [dict(row) for row in results] if results else []

    def get_next_match(self) -> Optional[Dict[str, Any]]:
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
        return dict(result) if result else None

    def get_monthly_count(self) -> int:
        """이번 달 경기 수"""
        query = """
            SELECT COUNT(*) as count FROM matches
            WHERE strftime('%Y-%m', match_date) = strftime('%Y-%m', 'now')
        """
        result = db_manager.execute_query(query, fetch_all=False)
        return result['count'] if result else 0

    def get_all(self) -> List[Dict[str, Any]]:
        """모든 경기 목록"""
        query = """
            SELECT m.*, f.name as field_name
            FROM matches m
            JOIN fields f ON f.id = m.field_id
            ORDER BY m.match_date DESC, m.match_time DESC
        """
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

    def get_all_matches(self) -> List[Dict[str, Any]]:
        """모든 경기 목록 (별칭 메서드)"""
        return self.get_all()

    def get_recent_matches(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 경기"""
        query = """
            SELECT m.*, f.name as field_name
            FROM matches m
            JOIN fields f ON f.id = m.field_id
            WHERE m.match_date <= date('now')
            ORDER BY m.match_date DESC, m.match_time DESC
            LIMIT ?
        """
        results = db_manager.execute_query(query, (limit,))
        return [dict(row) for row in results] if results else []

    def get_latest_match(self) -> Optional[Dict[str, Any]]:
        """가장 최근에 생성된 경기 조회"""
        query = """
            SELECT m.*, f.name as field_name
            FROM matches m
            JOIN fields f ON f.id = m.field_id
            ORDER BY m.created_at DESC
            LIMIT 1
        """
        result = db_manager.execute_query(query, fetch_all=False)
        return dict(result) if result else None

    def update(self, match: Match) -> bool:
        """경기 정보 업데이트"""
        query = """
            UPDATE matches
            SET field_id = ?, match_date = ?, match_time = ?, opponent = ?, result = ?, attendance_lock_minutes = ?, attendance_capacity = ?
            WHERE id = ?
        """
        result = db_manager.execute_query(
            query,
            (match.field_id, str(match.match_date), match.match_time, match.opponent, match.result, match.attendance_lock_minutes, match.attendance_capacity, match.id)
        )
        return result is not None and result > 0

    def delete(self, match_id: int) -> bool:
        """경기 삭제"""
        query = "DELETE FROM matches WHERE id = ?"
        result = db_manager.execute_query(query, (match_id,))
        return result is not None and result > 0

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

    def get_all_active(self) -> List[Dict[str, Any]]:
        """활성 선수 목록"""
        query = "SELECT * FROM players WHERE active=1 ORDER BY name"
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

    def get_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """ID로 선수 조회"""
        query = "SELECT * FROM players WHERE id = ?"
        result = db_manager.execute_query(query, (player_id,), fetch_all=False)
        return dict(result) if result else None

    def get_total_count(self) -> int:
        """총 활성 선수 수"""
        query = "SELECT COUNT(*) as count FROM players WHERE active=1"
        result = db_manager.execute_query(query, fetch_all=False)
        return result['count'] if result else 0

    def get_detailed_stats(self, player_id: int) -> Dict[str, Any]:
        """선수 상세 통계 (마무리한 경기만)"""
        # 골, 어시스트 등 통계 (마무리한 경기만)
        stats_query = """
            SELECT
                COALESCE(SUM(ps.goals), 0) as total_goals,
                COALESCE(SUM(ps.assists), 0) as total_assists,
                COALESCE(SUM(ps.saves), 0) as total_saves,
                COALESCE(SUM(ps.yellow_cards), 0) as total_yellow_cards,
                COALESCE(SUM(ps.red_cards), 0) as total_red_cards,
                COALESCE(SUM(ps.mvp), 0) as total_mvp
            FROM player_stats ps
            JOIN matches m ON m.id = ps.match_id
            WHERE ps.player_id = ? AND m.match_date < date('now')
        """
        stats_result = db_manager.execute_query(stats_query, (player_id,), fetch_all=False)
        result = dict(stats_result) if stats_result else {}

        # 출석률 계산 (마무리한 경기만)
        attendance_query = """
            SELECT
                COUNT(*) as total_matches,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_matches
            FROM attendance a
            JOIN matches m ON m.id = a.match_id
            WHERE a.player_id = ? AND m.match_date < date('now')
        """
        attendance_result = db_manager.execute_query(attendance_query, (player_id,), fetch_all=False)
        attendance = dict(attendance_result) if attendance_result else {'total_matches': 0, 'present_matches': 0}

        if attendance['total_matches'] > 0:
            result['attendance_rate'] = (attendance['present_matches'] / attendance['total_matches']) * 100
        else:
            result['attendance_rate'] = 0

        return result

    def update(self, player_id: int, name: str, position: str, phone: str = "", email: str = "") -> bool:
        """선수 정보 수정"""
        query = """
            UPDATE players
            SET name = ?, position = ?, phone = ?, email = ?
            WHERE id = ?
        """
        result = db_manager.execute_query(query, (name, position, phone, email, player_id))
        return result is not None and result > 0

    def delete(self, player_id: int) -> bool:
        """선수 완전 삭제 (개인정보보호)"""
        query = "DELETE FROM players WHERE id = ?"
        result = db_manager.execute_query(query, (player_id,))
        return result is not None and result > 0

class FieldRepository:
    """구장 데이터 액세스"""

    def create(self, field: Field) -> bool:
        """구장 생성"""
        query = "INSERT INTO fields (name, address, cost) VALUES (?, ?, ?)"
        result = db_manager.execute_query(query, (field.name, field.address, field.cost))
        return result is not None and result > 0

    def get_all(self) -> List[Dict[str, Any]]:
        """모든 구장 목록"""
        query = "SELECT * FROM fields ORDER BY name"
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

class PlayerStatsRepository:
    """선수 통계 데이터 액세스"""

    def save_stats(self, player_id: int, match_id: int, goals: int, assists: int,
                   saves: int, yellow_cards: int, red_cards: int, mvp: bool) -> bool:
        """선수 통계 저장"""
        query = """
            INSERT OR REPLACE INTO player_stats
            (player_id, match_id, goals, assists, saves, yellow_cards, red_cards, mvp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(
            query, (player_id, match_id, goals, assists, saves, yellow_cards, red_cards, mvp)
        )
        return result is not None and result > 0

    def get_leaderboard_data(self) -> Dict[str, List]:
        """순위표 데이터 (마무리한 경기만)"""
        # 득점왕 (마무리한 경기만)
        goals_query = """
            SELECT
                ROW_NUMBER() OVER (ORDER BY SUM(ps.goals) DESC) as rank,
                p.name,
                SUM(ps.goals) as total_goals,
                COUNT(DISTINCT ps.match_id) as matches_played
            FROM player_stats ps
            JOIN players p ON p.id = ps.player_id
            JOIN matches m ON m.id = ps.match_id
            WHERE ps.goals > 0 AND m.match_date < date('now')
            GROUP BY ps.player_id, p.name
            ORDER BY total_goals DESC
            LIMIT 10
        """
        goals_results = db_manager.execute_query(goals_query)
        goals_data = [list(row) for row in goals_results] if goals_results else []

        # 어시스트왕 (마무리한 경기만)
        assists_query = """
            SELECT
                ROW_NUMBER() OVER (ORDER BY SUM(ps.assists) DESC) as rank,
                p.name,
                SUM(ps.assists) as total_assists,
                COUNT(DISTINCT ps.match_id) as matches_played
            FROM player_stats ps
            JOIN players p ON p.id = ps.player_id
            JOIN matches m ON m.id = ps.match_id
            WHERE ps.assists > 0 AND m.match_date < date('now')
            GROUP BY ps.player_id, p.name
            ORDER BY total_assists DESC
            LIMIT 10
        """
        assists_results = db_manager.execute_query(assists_query)
        assists_data = [list(row) for row in assists_results] if assists_results else []

        # MVP (마무리한 경기만)
        mvp_query = """
            SELECT
                ROW_NUMBER() OVER (ORDER BY SUM(ps.mvp) DESC) as rank,
                p.name,
                SUM(ps.mvp) as mvp_count
            FROM player_stats ps
            JOIN players p ON p.id = ps.player_id
            JOIN matches m ON m.id = ps.match_id
            WHERE ps.mvp = 1 AND m.match_date < date('now')
            GROUP BY ps.player_id, p.name
            ORDER BY mvp_count DESC
            LIMIT 10
        """
        mvp_results = db_manager.execute_query(mvp_query)
        mvp_data = [list(row) for row in mvp_results] if mvp_results else []

        return {
            'goals': goals_data,
            'assists': assists_data,
            'mvp': mvp_data
        }

    def get_team_average_stats(self) -> Dict[str, float]:
        """팀 평균 통계 (마무리한 경기만)"""
        # 경기당 평균 골 (마무리한 경기만)
        goals_query = """
            SELECT AVG(total_goals) as avg_goals
            FROM (
                SELECT SUM(ps.goals) as total_goals
                FROM player_stats ps
                JOIN matches m ON m.id = ps.match_id
                WHERE m.match_date < date('now')
                GROUP BY ps.match_id
            )
        """
        goals_result = db_manager.execute_query(goals_query, fetch_all=False)

        # 평균 출석률 (마무리한 경기만)
        attendance_query = """
            SELECT
                AVG(CASE WHEN a.status = 'present' THEN 100.0 ELSE 0 END) as avg_attendance
            FROM attendance a
            JOIN matches m ON m.id = a.match_id
            WHERE m.match_date < date('now')
        """
        attendance_result = db_manager.execute_query(attendance_query, fetch_all=False)

        # 총 마무리한 경기수
        matches_query = "SELECT COUNT(*) as total_matches FROM matches WHERE match_date < date('now')"
        matches_result = db_manager.execute_query(matches_query, fetch_all=False)

        return {
            'avg_goals_per_match': goals_result['avg_goals'] if goals_result and goals_result['avg_goals'] else 0,
            'avg_attendance_rate': attendance_result['avg_attendance'] if attendance_result and attendance_result['avg_attendance'] else 0,
            'total_matches': matches_result['total_matches'] if matches_result else 0
        }

class NewsRepository:
    """소식 데이터 액세스"""

    def create(self, title: str, content: str, author: str, pinned: bool, category: str) -> bool:
        """팀 소식 추가"""
        query = """
            INSERT INTO news (title, content, author, pinned, category)
            VALUES (?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(query, (title, content, author, pinned, category))
        return result is not None and result > 0

    def get_all(self) -> List[Dict[str, Any]]:
        """팀 소식 조회"""
        query = "SELECT * FROM news ORDER BY pinned DESC, created_at DESC"
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

    def get_recent(self, limit: int = 3) -> List[Dict[str, Any]]:
        """최근 팀 소식"""
        query = "SELECT * FROM news ORDER BY created_at DESC LIMIT ?"
        results = db_manager.execute_query(query, (limit,))
        return [dict(row) for row in results] if results else []

    def delete(self, news_id: int) -> bool:
        """소식 삭제"""
        query = "DELETE FROM news WHERE id = ?"
        result = db_manager.execute_query(query, (news_id,))
        return result is not None and result > 0

    def toggle_pinned(self, news_id: int) -> bool:
        """소식 고정 상태 토글"""
        query = """
            UPDATE news
            SET pinned = NOT pinned
            WHERE id = ?
        """
        result = db_manager.execute_query(query, (news_id,))
        return result is not None and result > 0

    def get_by_id(self, news_id: int) -> Optional[Dict[str, Any]]:
        """ID로 소식 조회"""
        query = "SELECT * FROM news WHERE id = ?"
        result = db_manager.execute_query(query, (news_id,), fetch_all=False)
        return dict(result) if result else None

    def update(self, news_id: int, title: str, content: str, author: str, pinned: bool, category: str) -> bool:
        """소식 수정"""
        query = """
            UPDATE news
            SET title = ?, content = ?, author = ?, pinned = ?, category = ?
            WHERE id = ?
        """
        result = db_manager.execute_query(query, (title, content, author, pinned, category, news_id))
        return result is not None and result > 0

class GalleryRepository:
    """갤러리 데이터 액세스"""

    def create(self, title: str, description: str, file_path: str, match_id: Optional[int] = None) -> bool:
        """갤러리 사진 추가"""
        query = """
            INSERT INTO gallery (title, description, file_path, match_id)
            VALUES (?, ?, ?, ?)
        """
        result = db_manager.execute_query(query, (title, description, file_path, match_id))
        return result is not None and result > 0

    def get_all(self) -> List[Dict[str, Any]]:
        """갤러리 사진 조회"""
        query = "SELECT * FROM gallery ORDER BY upload_date DESC"
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

    def delete(self, gallery_id: int) -> bool:
        """갤러리 사진 삭제"""
        query = "DELETE FROM gallery WHERE id = ?"
        result = db_manager.execute_query(query, (gallery_id,))
        return result is not None and result > 0

    def get_by_id(self, gallery_id: int) -> Optional[Dict[str, Any]]:
        """ID로 갤러리 사진 조회"""
        query = "SELECT * FROM gallery WHERE id = ?"
        result = db_manager.execute_query(query, (gallery_id,), fetch_all=False)
        return dict(result) if result else None

    def get_by_file_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        """파일 경로로 갤러리 사진 조회"""
        query = "SELECT * FROM gallery WHERE file_path = ?"
        result = db_manager.execute_query(query, (file_path,), fetch_all=False)
        return dict(result) if result else None

class FinanceRepository:
    """재정 데이터 액세스"""

    def create(self, date: str, description: str, amount: int, transaction_type: str, category: str) -> bool:
        """재정 기록 추가"""
        query = """
            INSERT INTO finances (date, description, amount, type, category)
            VALUES (?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(query, (date, description, amount, transaction_type, category))
        return result is not None and result > 0

    def get_summary(self) -> Dict[str, int]:
        """재정 요약"""
        query = """
            SELECT
                COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) as total_expense
            FROM finances
        """
        result = db_manager.execute_query(query, fetch_all=False)
        return dict(result) if result else {'total_income': 0, 'total_expense': 0}

    def get_monthly_data(self) -> List[Dict[str, Any]]:
        """월별 재정 데이터"""
        query = """
            SELECT
                strftime('%Y-%m', date) as month,
                SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
            FROM finances
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

    def get_expense_by_category(self) -> List[Dict[str, Any]]:
        """카테고리별 지출"""
        query = """
            SELECT category, SUM(amount) as amount
            FROM finances
            WHERE type = 'expense'
            GROUP BY category
        """
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """모든 거래 내역"""
        query = "SELECT * FROM finances ORDER BY date DESC"
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

    def get_team_balance(self) -> int:
        """팀 잔고"""
        query = """
            SELECT
                COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) as balance
            FROM finances
        """
        result = db_manager.execute_query(query, fetch_all=False)
        return result['balance'] if result else 0

    def delete(self, finance_id: int) -> bool:
        """재정 기록 삭제"""
        query = "DELETE FROM finances WHERE id = ?"
        result = db_manager.execute_query(query, (finance_id,))
        return result is not None and result > 0

    def get_by_id(self, finance_id: int) -> Optional[Dict[str, Any]]:
        """ID로 재정 기록 조회"""
        query = "SELECT * FROM finances WHERE id = ?"
        result = db_manager.execute_query(query, (finance_id,), fetch_all=False)
        return dict(result) if result else None

class AttendanceRepository:
    """출석 데이터 액세스"""

    def create_for_match(self, match_id: int) -> bool:
        """경기에 대한 모든 선수의 출석 상태 생성 (기본값: pending)"""
        # 먼저 활성 선수 수 확인
        count_query = "SELECT COUNT(*) as count FROM players WHERE active = 1"
        count_result = db_manager.execute_query(count_query, fetch_all=False)
        active_player_count = count_result['count'] if count_result else 0

        if active_player_count == 0:
            return False

        # 이미 출석 데이터가 있는지 확인
        existing_query = "SELECT COUNT(*) as count FROM attendance WHERE match_id = ?"
        existing_result = db_manager.execute_query(existing_query, (match_id,), fetch_all=False)
        existing_count = existing_result['count'] if existing_result else 0

        if existing_count >= active_player_count:
            return True  # 이미 모든 선수의 출석 데이터가 있음

        # 출석 데이터 생성 (기본값: absent)
        query = """
            INSERT OR IGNORE INTO attendance (match_id, player_id, status)
            SELECT ?, id, 'absent' FROM players WHERE active = 1
        """
        result = db_manager.execute_query(query, (match_id,))

        # 생성 후 실제 데이터 개수 확인
        final_query = "SELECT COUNT(*) as count FROM attendance WHERE match_id = ?"
        final_result = db_manager.execute_query(final_query, (match_id,), fetch_all=False)
        final_count = final_result['count'] if final_result else 0

        return final_count >= active_player_count

    def update_status(self, match_id: int, player_id: int, status: str) -> bool:
        """특정 선수의 출석 상태 업데이트"""
        query = """
            UPDATE attendance
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE match_id = ? AND player_id = ?
        """
        result = db_manager.execute_query(query, (status, match_id, player_id))
        return result is not None and result > 0

    def get_by_match(self, match_id: int) -> List[Dict[str, Any]]:
        """특정 경기의 모든 선수 출석 현황"""
        query = """
            SELECT a.*, p.name as player_name, m.match_date, m.match_time, f.name as field_name
            FROM attendance a
            JOIN players p ON p.id = a.player_id
            JOIN matches m ON m.id = a.match_id
            JOIN fields f ON f.id = m.field_id
            WHERE a.match_id = ?
            ORDER BY p.name
        """
        results = db_manager.execute_query(query, (match_id,))
        return [dict(row) for row in results] if results else []

    def get_upcoming_by_player(self, player_id: int) -> List[Dict[str, Any]]:
        """특정 선수의 예정된 경기 출석 현황"""
        query = """
            SELECT a.*, p.name as player_name, m.match_date, m.match_time, f.name as field_name
            FROM attendance a
            JOIN players p ON p.id = a.player_id
            JOIN matches m ON m.id = a.match_id
            JOIN fields f ON f.id = m.field_id
            WHERE a.player_id = ? AND m.match_date >= date('now')
            ORDER BY m.match_date, m.match_time
        """
        results = db_manager.execute_query(query, (player_id,))
        return [dict(row) for row in results] if results else []

    def get_summary_by_match(self, match_id: int) -> Dict[str, int]:
        """경기별 출석 요약 (참석/불참/미정/미응답 인원수)"""
        query = """
            SELECT
                SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) AS present,
                SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) AS absent,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'absent' AND updated_at = created_at THEN 1 ELSE 0 END) AS unresponded,
                COUNT(*) AS total
            FROM attendance
            WHERE match_id = ?
        """

        result = db_manager.execute_query(query, (match_id,), fetch_all=False)

        if not result:
            return {'present': 0, 'absent': 0, 'pending': 0, 'unresponded': 0, 'total': 0}

        return {
            'present': result['present'] or 0,
            'absent': result['absent'] or 0,
            'pending': result['pending'] or 0,
            'unresponded': result['unresponded'] or 0,
            'total': result['total'] or 0
        }

    def get_for_match(self, match_id: int) -> List[Dict[str, Any]]:
        """특정 경기의 출석 정보 (기존 메소드 유지)"""
        query = """
            SELECT a.*, p.name as player_name
            FROM attendance a
            JOIN players p ON p.id = a.player_id
            WHERE a.match_id = ?
        """
        results = db_manager.execute_query(query, (match_id,))
        return [dict(row) for row in results] if results else []

    def count_present(self, match_id: int) -> int:
        """특정 경기의 현재 참석 인원 수"""
        query = """
            SELECT COUNT(*) as count
            FROM attendance
            WHERE match_id = ? AND status = 'present'
        """
        result = db_manager.execute_query(query, (match_id,), fetch_all=False)
        return result['count'] if result else 0

class AdminRepository:
    """관리자 데이터 액세스"""

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """사용자명으로 관리자 조회"""
        query = "SELECT * FROM admins WHERE username = ? AND is_active = 1"
        result = db_manager.execute_query(query, (username,), fetch_all=False)
        return dict(result) if result else None

    def get_by_id(self, admin_id: int) -> Optional[Dict[str, Any]]:
        """ID로 관리자 조회"""
        query = "SELECT * FROM admins WHERE id = ? AND is_active = 1"
        result = db_manager.execute_query(query, (admin_id,), fetch_all=False)
        return dict(result) if result else None

    def create(self, admin: Admin) -> bool:
        """관리자 생성"""
        query = """
            INSERT INTO admins (username, password_hash, name, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(
            query,
            (admin.username, admin.password_hash, admin.name, admin.role, admin.is_active)
        )
        return result is not None and result > 0

    def update_last_login(self, admin_id: int) -> bool:
        """마지막 로그인 시간 업데이트"""
        query = "UPDATE admins SET last_login = CURRENT_TIMESTAMP WHERE id = ?"
        result = db_manager.execute_query(query, (admin_id,))
        return result is not None and result > 0

    def update_password(self, admin_id: int, new_password_hash: str) -> bool:
        """비밀번호 업데이트"""
        query = "UPDATE admins SET password_hash = ? WHERE id = ?"
        result = db_manager.execute_query(query, (new_password_hash, admin_id))
        return result is not None and result > 0

    def get_all_active(self) -> List[Dict[str, Any]]:
        """모든 활성 관리자 목록"""
        query = "SELECT * FROM admins WHERE is_active = 1 ORDER BY name"
        results = db_manager.execute_query(query)
        return [dict(row) for row in results] if results else []

    def deactivate(self, admin_id: int) -> bool:
        """관리자 비활성화"""
        query = "UPDATE admins SET is_active = 0 WHERE id = ?"
        result = db_manager.execute_query(query, (admin_id,))
        return result is not None and result > 0

class VideoRepository:
    """동영상 데이터 액세스"""

    def create(self, video) -> Optional[int]:
        """동영상 메타데이터 생성 및 ID 반환"""
        import logging
        logger = logging.getLogger(__name__)

        query = """
            INSERT INTO videos (title, description, original_filename, file_size,
                               duration, status, match_id, uploaded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        result = db_manager.execute_query(
            query,
            (video.title, video.description, video.original_filename, video.file_size,
             video.duration, video.status, video.match_id, video.uploaded_by)
        )

        logger.info(f"Video INSERT result (lastrowid): {result}")

        # lastrowid 반환 (새로 생성된 video_id)
        return result if result and result > 0 else None

    def update_processing_status(self, video_id: int, status: str, hls_path: Optional[str] = None,
                                 thumbnail_path: Optional[str] = None, duration: Optional[int] = None) -> bool:
        """동영상 처리 상태 업데이트"""
        import logging
        logger = logging.getLogger(__name__)

        query = """
            UPDATE videos
            SET status = ?, hls_path = ?, thumbnail_path = ?, duration = ?,
                processed_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE processed_at END
            WHERE id = ?
        """

        logger.info(f"Executing UPDATE for video_id={video_id}")
        logger.info(f"Parameters: status={status}, hls_path={hls_path}, thumbnail={thumbnail_path}, duration={duration}")

        result = db_manager.execute_query(
            query,
            (status, hls_path, thumbnail_path, duration, status, video_id)
        )

        logger.info(f"UPDATE result (rowcount): {result}")

        # rowcount가 0이어도 성공으로 간주 (이미 같은 값일 수 있음)
        return result is not None

    def update_info(self, video_id: int, description: str, match_id: Optional[int] = None) -> bool:
        """동영상 정보 업데이트 (설명, 연결 경기)"""
        import logging
        logger = logging.getLogger(__name__)

        query = """
            UPDATE videos
            SET description = ?, match_id = ?
            WHERE id = ?
        """

        logger.info(f"Updating video info - video_id: {video_id}, description: {description[:50] if description else 'None'}, match_id: {match_id}")

        result = db_manager.execute_query(query, (description, match_id, video_id))

        logger.info(f"Update result: {result}")

        return result is not None and result >= 0

    def get_by_id(self, video_id: int) -> Optional[Dict[str, Any]]:
        """ID로 동영상 조회"""
        query = """
            SELECT v.*, a.name as uploader_name, m.match_date, m.opponent
            FROM videos v
            LEFT JOIN admins a ON a.id = v.uploaded_by
            LEFT JOIN matches m ON m.id = v.match_id
            WHERE v.id = ?
        """
        result = db_manager.execute_query(query, (video_id,), fetch_all=False)
        return dict(result) if result else None

    def get_all(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """모든 동영상 목록 (상태 필터링 가능)"""
        if status_filter:
            query = """
                SELECT v.*, a.name as uploader_name, m.match_date, m.match_time, m.opponent, f.name as field_name
                FROM videos v
                LEFT JOIN admins a ON a.id = v.uploaded_by
                LEFT JOIN matches m ON m.id = v.match_id
                LEFT JOIN fields f ON f.id = m.field_id
                WHERE v.status = ?
                ORDER BY v.created_at DESC
            """
            results = db_manager.execute_query(query, (status_filter,))
        else:
            query = """
                SELECT v.*, a.name as uploader_name, m.match_date, m.match_time, m.opponent, f.name as field_name
                FROM videos v
                LEFT JOIN admins a ON a.id = v.uploaded_by
                LEFT JOIN matches m ON m.id = v.match_id
                LEFT JOIN fields f ON f.id = m.field_id
                ORDER BY v.created_at DESC
            """
            results = db_manager.execute_query(query)

        return [dict(row) for row in results] if results else []

    def get_by_match(self, match_id: int) -> List[Dict[str, Any]]:
        """특정 경기의 동영상 목록"""
        query = """
            SELECT v.*, a.name as uploader_name, m.match_date, m.match_time, m.opponent, f.name as field_name
            FROM videos v
            LEFT JOIN admins a ON a.id = v.uploaded_by
            LEFT JOIN matches m ON m.id = v.match_id
            LEFT JOIN fields f ON f.id = m.field_id
            WHERE v.match_id = ? AND v.status = 'completed'
            ORDER BY v.created_at DESC
        """
        results = db_manager.execute_query(query, (match_id,))
        return [dict(row) for row in results] if results else []

    def get_videos_by_match(self, match_id: int) -> List[Dict[str, Any]]:
        """특정 경기의 동영상 목록 (별칭 메서드)"""
        return self.get_by_match(match_id)

    def get_completed_videos(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """완료된 동영상 목록"""
        query = """
            SELECT v.*, a.name as uploader_name, m.match_date, m.match_time, m.opponent, f.name as field_name
            FROM videos v
            LEFT JOIN admins a ON a.id = v.uploaded_by
            LEFT JOIN matches m ON m.id = v.match_id
            LEFT JOIN fields f ON f.id = m.field_id
            WHERE v.status = 'completed'
            ORDER BY v.created_at DESC
        """
        params = ()
        if limit:
            # SQL Injection 방지: 파라미터 바인딩 사용
            limit = max(1, min(int(limit), 1000))  # 1~1000 범위로 제한
            query += " LIMIT ?"
            params = (limit,)

        results = db_manager.execute_query(query, params)
        return [dict(row) for row in results] if results else []

    def delete(self, video_id: int) -> bool:
        """동영상 메타데이터 삭제"""
        query = "DELETE FROM videos WHERE id = ?"
        result = db_manager.execute_query(query, (video_id,))
        return result is not None and result > 0

    def get_total_count(self) -> int:
        """총 동영상 수"""
        query = "SELECT COUNT(*) as count FROM videos WHERE status = 'completed'"
        result = db_manager.execute_query(query, fetch_all=False)
        return result['count'] if result else 0

    def get_total_duration(self) -> int:
        """총 동영상 재생 시간 (초)"""
        query = "SELECT COALESCE(SUM(duration), 0) as total FROM videos WHERE status = 'completed'"
        result = db_manager.execute_query(query, fetch_all=False)
        return result['total'] if result else 0

class TeamDistributionRepository:
    """팀 구성 데이터 액세스"""

    def save(self, match_id: int, team_data: Dict[str, Any], created_by: Optional[int] = None) -> bool:
        """팀 구성 저장 (이미 있으면 업데이트)"""
        team_data_json = json.dumps(team_data, ensure_ascii=False)

        # 기존 데이터 확인
        existing = self.get_by_match_id(match_id)

        if existing:
            # 업데이트
            query = """
                UPDATE team_distributions
                SET team_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE match_id = ?
            """
            result = db_manager.execute_query(query, (team_data_json, match_id))
        else:
            # 생성
            query = """
                INSERT INTO team_distributions (match_id, team_data, created_by)
                VALUES (?, ?, ?)
            """
            result = db_manager.execute_query(query, (match_id, team_data_json, created_by))

        return result is not None and result > 0

    def get_by_match_id(self, match_id: int) -> Optional[Dict[str, Any]]:
        """경기별 팀 구성 조회"""
        query = """
            SELECT id, match_id, team_data, created_by, created_at, updated_at
            FROM team_distributions
            WHERE match_id = ?
        """
        result = db_manager.execute_query(query, (match_id,), fetch_all=False)

        if result:
            data = dict(result)
            # JSON 파싱
            try:
                data['team_data'] = json.loads(data['team_data'])
            except json.JSONDecodeError:
                data['team_data'] = None
            return data
        return None

    def delete(self, match_id: int) -> bool:
        """팀 구성 삭제"""
        query = "DELETE FROM team_distributions WHERE match_id = ?"
        result = db_manager.execute_query(query, (match_id,))
        return result is not None and result > 0

    def get_all(self) -> List[Dict[str, Any]]:
        """모든 팀 구성 조회"""
        query = """
            SELECT td.*, m.match_date, m.match_time
            FROM team_distributions td
            JOIN matches m ON m.id = td.match_id
            ORDER BY m.match_date DESC, m.match_time DESC
        """
        results = db_manager.execute_query(query)

        if results:
            data_list = []
            for row in results:
                data = dict(row)
                try:
                    data['team_data'] = json.loads(data['team_data'])
                except json.JSONDecodeError:
                    data['team_data'] = None
                data_list.append(data)
            return data_list
        return []

# Repository 인스턴스들
match_repo = MatchRepository()
player_repo = PlayerRepository()
field_repo = FieldRepository()
player_stats_repo = PlayerStatsRepository()
news_repo = NewsRepository()
gallery_repo = GalleryRepository()
finance_repo = FinanceRepository()
attendance_repo = AttendanceRepository()
admin_repo = AdminRepository()
video_repo = VideoRepository()
team_distribution_repo = TeamDistributionRepository()
