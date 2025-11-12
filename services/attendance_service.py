"""출석 관련 비즈니스 로직"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from database.repositories import attendance_repo, match_repo
from database.models import Attendance

class AttendanceService:
    """출석 관련 서비스"""

    def __init__(self):
        self.attendance_repo = attendance_repo
        self.match_repo = match_repo

    def create_attendance_for_match(self, match_id: int) -> bool:
        """새 경기 생성 시 모든 선수의 출석 상태 생성"""
        return self.attendance_repo.create_for_match(match_id)

    def is_attendance_locked(self, match_id: int, *, now: Optional[datetime] = None) -> bool:
        """경기 출석 변경이 잠금되었는지 확인"""
        from datetime import timezone, timedelta as td

        # 한국 표준시(KST) = UTC+9
        KST = timezone(td(hours=9))

        if now is None:
            # 현재 시간을 KST로 변환
            now = datetime.now(timezone.utc).astimezone(KST).replace(tzinfo=None)

        # 경기 정보 조회
        match = self.match_repo.get_by_id(match_id)
        if not match:
            return False

        lock_minutes = match.get('attendance_lock_minutes', 0)

        # -1이면 즉시 마감 (항상 잠금)
        if lock_minutes == -1:
            return True

        # 출석 마감 시간이 0이면 제한 없음
        if lock_minutes == 0:
            return False

        try:
            # 경기 시작 시간 계산 (데이터베이스에 KST로 저장됨)
            match_date_str = match['match_date']
            match_time_str = match['match_time']
            match_datetime = datetime.strptime(f"{match_date_str} {match_time_str}", "%Y-%m-%d %H:%M")

            # 과거 경기는 항상 잠금
            if match_datetime < now:
                return True

            # 마감 시간 계산
            lock_minutes = match.get('attendance_lock_minutes', 0)
            lock_datetime = match_datetime - timedelta(minutes=lock_minutes)

            # 현재 시간이 마감 시간을 지났는지 확인
            return now >= lock_datetime
        except (ValueError, KeyError) as e:
            # 시간 정보가 없거나 오류가 있는 경우 잠금 처리하지 않음
            return False

    def update_player_status(self, match_id: int, player_id: int, status: str) -> bool:
        """선수 개인의 출석 상태 변경"""
        valid_statuses = ['present', 'absent', 'pending']
        if status not in valid_statuses:
            raise ValueError(f"잘못된 상태값입니다: {status}")

        # 출석 변경이 잠금되었는지 확인
        if self.is_attendance_locked(match_id):
            return False

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
                'updated_at': att.get('updated_at', ''),
                'created_at': att.get('created_at', ''),
                'has_responded': self._has_player_responded(att)
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
        total = summary.get('total', 0) or (
            summary.get('present', 0) + summary.get('absent', 0) + summary.get('pending', 0)
        )

        return {
            'total_players': total,
            'present_count': summary['present'],
            'absent_count': summary['absent'],
            'pending_count': summary['pending'],
            'unresponded_count': summary.get('unresponded', 0),
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

    def _has_player_responded(self, att: Dict[str, Any]) -> bool:
        """선수가 기본값(자동 불참) 이후에 직접 응답했는지 여부"""
        status = att.get('status')
        if status != 'absent':
            return True

        updated_at = att.get('updated_at')
        created_at = att.get('created_at')
        if not updated_at or not created_at:
            return False

        return updated_at != created_at

# 서비스 인스턴스
attendance_service = AttendanceService()
