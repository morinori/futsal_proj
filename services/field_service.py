"""구장 관련 비즈니스 로직"""
from typing import List, Dict, Any, Optional
from database.repositories import field_repo
from database.models import Field
from utils.validators import validate_field_data
from utils.formatters import format_currency, format_field_display_name

class FieldService:
    """구장 관련 서비스"""

    def __init__(self):
        self.field_repo = field_repo

    def create_field(self, name: str, address: str = "", cost: int = 0) -> bool:
        """구장 생성"""
        # 데이터 검증
        validation_result = validate_field_data({
            'name': name,
            'address': address,
            'cost': cost
        })

        if not validation_result.is_valid:
            raise ValueError(f"Invalid field data: {', '.join(validation_result.errors)}")

        field = Field(
            name=name,
            address=address,
            cost=cost
        )

        return self.field_repo.create(field)

    def get_all_fields(self) -> List[Dict[str, Any]]:
        """모든 구장 목록"""
        fields = self.field_repo.get_all()
        return [
            {
                'id': field['id'],
                'name': field['name'],
                'address': field['address'],
                'cost': field['cost'],
                'cost_display': format_currency(field['cost']),
                'display_name': format_field_display_name(field['name'], field['address']),
                'created_at': field['created_at']
            }
            for field in fields
        ]

    def get_field_by_id(self, field_id: int) -> Optional[Dict[str, Any]]:
        """ID로 구장 조회"""
        # Repository에 get_by_id 메서드가 없으므로 전체 목록에서 찾기
        fields = self.get_all_fields()
        for field in fields:
            if field['id'] == field_id:
                return field
        return None

    def get_fields_for_selection(self) -> List[Dict[str, Any]]:
        """선택용 구장 목록"""
        fields = self.get_all_fields()
        return [
            {
                'id': field['id'],
                'display_name': field['display_name'],
                'cost_display': field['cost_display']
            }
            for field in fields
        ]

    def check_field_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """구장명 중복 체크"""
        all_fields = self.get_all_fields()
        for field in all_fields:
            if field['name'] == name and (exclude_id is None or field['id'] != exclude_id):
                return True
        return False

    def get_field_statistics(self) -> Dict[str, Any]:
        """구장 통계"""
        fields = self.get_all_fields()

        if not fields:
            return {
                'total_fields': 0,
                'average_cost': 0,
                'min_cost': 0,
                'max_cost': 0,
                'total_cost': 0
            }

        costs = [field['cost'] for field in fields if field['cost'] > 0]

        return {
            'total_fields': len(fields),
            'average_cost': sum(costs) // len(costs) if costs else 0,
            'min_cost': min(costs) if costs else 0,
            'max_cost': max(costs) if costs else 0,
            'total_cost': sum(costs)
        }

    def get_fields_by_cost_range(self, min_cost: int = 0, max_cost: int = 1000000) -> List[Dict[str, Any]]:
        """가격대별 구장 목록"""
        all_fields = self.get_all_fields()
        return [
            field for field in all_fields
            if min_cost <= field['cost'] <= max_cost
        ]

    def search_fields(self, search_term: str) -> List[Dict[str, Any]]:
        """구장 검색 (이름 또는 주소)"""
        all_fields = self.get_all_fields()
        search_term = search_term.lower().strip()

        if not search_term:
            return all_fields

        return [
            field for field in all_fields
            if (search_term in field['name'].lower() or
                search_term in field['address'].lower())
        ]

# 서비스 인스턴스
field_service = FieldService()