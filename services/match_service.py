"""경기 관련 비즈니스 로직"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from database.repositories import match_repo, field_repo
from database.models import Match
from utils.validators import validate_match_data
from utils.formatters import format_time_options, format_field_display_name

class MatchService:
    """경기 관련 서비스"""

    def __init__(self):
        self.match_repo = match_repo
        self.field_repo = field_repo

    def create_match(self, field_id: int, match_date: date, match_time: str, opponent: str = "") -> bool:
        """경기 생성 (출석 상태 자동 생성 포함)"""
        # 데이터 검증
        validation_result = validate_match_data({
            'field_id': field_id,
            'match_date': match_date,
            'match_time': match_time,
            'opponent': opponent
        })

        if not validation_result.is_valid:
            raise ValueError(f"Invalid match data: {', '.join(validation_result.errors)}")

        # 경기 생성
        match = Match(
            field_id=field_id,
            match_date=match_date,
            match_time=match_time,
            opponent=opponent
        )

        # 경기 생성
        success = self.match_repo.create(match)

        if success:
            # 방금 생성된 경기 ID 조회
            latest_match = self.match_repo.get_latest_match()
            if latest_match:
                # 모든 활성 선수에 대한 출석 상태 생성
                from services.attendance_service import attendance_service
                attendance_service.create_attendance_for_match(latest_match['id'])

        return success

    def get_next_match(self) -> Optional[Dict[str, Any]]:
        """다음 경기 조회"""
        match = self.match_repo.get_next_match()
        if not match:
            return None

        return match

    def get_monthly_matches(self, year: int, month: int) -> List[Dict[str, Any]]:
        """월별 경기 목록"""
        return self.match_repo.get_for_month(year, month)

    def get_monthly_count(self) -> int:
        """이번 달 경기 수"""
        return self.match_repo.get_monthly_count()

    def get_all_matches(self) -> List[Dict[str, Any]]:
        """모든 경기 목록"""
        return self.match_repo.get_all()

    def get_recent_matches(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 경기"""
        return self.match_repo.get_recent_matches(limit)

    def get_time_options(self) -> List[tuple]:
        """시간 선택 옵션 생성"""
        return format_time_options()

    def get_available_fields(self) -> List[Dict[str, Any]]:
        """사용 가능한 구장 목록"""
        fields = self.field_repo.get_all()
        return [
            {
                'id': field['id'],
                'name': field['name'],
                'address': field['address'],
                'cost': field['cost'],
                'display_name': format_field_display_name(field['name'], field['address'])
            }
            for field in fields
        ]

    def get_matches_for_calendar(self, year: int, month: int) -> Dict[str, List[Dict[str, Any]]]:
        """달력용 경기 데이터 (날짜별로 그룹화)"""
        matches = self.get_monthly_matches(year, month)
        matches_by_date = {}

        for match in matches:
            match_date = match['match_date']
            if match_date not in matches_by_date:
                matches_by_date[match_date] = []
            matches_by_date[match_date].append(match)

        return matches_by_date

    def validate_match_time_conflict(self, field_id: int, match_date: date, match_time: str, exclude_match_id: Optional[int] = None) -> bool:
        """동일 구장, 날짜, 시간에 다른 경기가 있는지 확인"""
        monthly_matches = self.get_monthly_matches(match_date.year, match_date.month)

        for match in monthly_matches:
            if (match['field_id'] == field_id and
                match['match_date'] == str(match_date) and
                match['match_time'] == match_time):
                # 수정 중인 경기는 제외
                if exclude_match_id and match['id'] == exclude_match_id:
                    continue
                return True

        return False

    def update_match(self, match_id: int, field_id: int, match_date: date, match_time: str, opponent: str = "", result: str = "") -> bool:
        """경기 정보 업데이트"""
        # 데이터 검증
        validation_result = validate_match_data({
            'field_id': field_id,
            'match_date': match_date,
            'match_time': match_time,
            'opponent': opponent,
            'result': result
        })

        if not validation_result.is_valid:
            raise ValueError(f"Invalid match data: {', '.join(validation_result.errors)}")

        # 경기 정보 업데이트
        updated_match = Match(
            id=match_id,
            field_id=field_id,
            match_date=match_date,
            match_time=match_time,
            opponent=opponent,
            result=result
        )

        return self.match_repo.update(updated_match)

    def delete_match(self, match_id: int) -> bool:
        """경기 삭제"""
        return self.match_repo.delete(match_id)

# 서비스 인스턴스
match_service = MatchService()