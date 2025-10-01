"""출석 관련 비즈니스 로직"""
from typing import List, Dict, Any
from database.repositories import attendance_repo
from database.models import Attendance

class AttendanceService:
    """출석 관련 서비스"""

    def __init__(self):
        self.attendance_repo = attendance_repo

    def create_attendance_for_match(self, match_id: int) -> bool:
        """새 경기 생성 시 모든 선수의 출석 상태 생성"""
        return self.attendance_repo.create_for_match(match_id)

    def update_player_status(self, match_id: int, player_id: int, status: str) -> bool:
        """선수 개인의 출석 상태 변경"""
        valid_statuses = ['present', 'absent', 'pending']
        if status not in valid_statuses:
            raise ValueError(f"잘못된 상태값입니다: {status}")

        return self.attendance_repo.update_status(match_id, player_id, status)

    def get_match_attendance(self, match_id: int) -> List[Dict[str, Any]]:
        """경기별 전체 출석 현황 (관리자용)"""
        attendances = self.attendance_repo.get_by_match(match_id)

        return [
            {
                'player_id': att['player_id'],
                'player_name': att['player_name'],
                'status': att['status'],
                'status_display': self._get_status_display(att['status']),
                'updated_at': att.get('updated_at', '')
            }
            for att in attendances
        ]

    def get_player_upcoming_matches(self, player_id: int) -> List[Dict[str, Any]]:
        """개인의 예정된 경기 출석 현황"""
        attendances = self.attendance_repo.get_upcoming_by_player(player_id)

        return [
            {
                'match_id': att['match_id'],
                'match_date': att['match_date'],
                'match_time': att['match_time'],
                'field_name': att['field_name'],
                'status': att['status'],
                'status_display': self._get_status_display(att['status'])
            }
            for att in attendances
        ]

    def get_attendance_summary(self, match_id: int) -> Dict[str, Any]:
        """경기 출석 요약 통계"""
        summary = self.attendance_repo.get_summary_by_match(match_id)
        total = sum(summary.values())

        return {
            'total_players': total,
            'present_count': summary['present'],
            'absent_count': summary['absent'],
            'pending_count': summary['pending'],
            'present_rate': (summary['present'] / total * 100) if total > 0 else 0
        }

    def _get_status_display(self, status: str) -> str:
        """상태값을 사용자 친화적 텍스트로 변환"""
        status_map = {
            'present': '✅ 참석',
            'absent': '❌ 불참',
            'pending': '❓ 미정'
        }
        return status_map.get(status, status)

    def get_status_options(self) -> List[tuple]:
        """출석 상태 선택 옵션"""
        return [
            ('present', '✅ 참석'),
            ('absent', '❌ 불참'),
            ('pending', '❓ 미정')
        ]

# 서비스 인스턴스
attendance_service = AttendanceService()