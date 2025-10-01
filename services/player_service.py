"""선수 관련 비즈니스 로직"""
from typing import List, Dict, Any, Optional
from database.repositories import player_repo, player_stats_repo
from database.models import Player
from utils.validators import validate_player_data
from utils.formatters import format_position_display, format_phone_number

class PlayerService:
    """선수 관련 서비스"""

    def __init__(self):
        self.player_repo = player_repo
        self.player_stats_repo = player_stats_repo

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
            raise ValueError(f"Invalid player data: {', '.join(validation_result.errors)}")

        # 전화번호 포맷팅
        formatted_phone = format_phone_number(phone) if phone else ""

        player = Player(
            name=name,
            position=position,
            phone=formatted_phone,
            email=email
        )

        return self.player_repo.create(player)

    def get_all_players(self) -> List[Dict[str, Any]]:
        """모든 활성 선수 목록"""
        players = self.player_repo.get_all_active()
        return [
            {
                'id': player['id'],
                'name': player['name'],
                'position': player['position'],
                'position_display': format_position_display(player['position']),
                'phone': player['phone'],
                'email': player['email'],
                'created_at': player['created_at']
            }
            for player in players
        ]

    def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """ID로 선수 조회"""
        player = self.player_repo.get_by_id(player_id)
        if not player:
            return None

        return {
            'id': player['id'],
            'name': player['name'],
            'position': player['position'],
            'position_display': format_position_display(player['position']),
            'phone': player['phone'],
            'email': player['email'],
            'created_at': player['created_at']
        }

    def get_total_count(self) -> int:
        """총 선수 수"""
        return self.player_repo.get_total_count()

    def get_position_options(self) -> List[str]:
        """포지션 선택 옵션"""
        return ["GK", "DF", "MF", "FW"]

    def get_position_display_options(self) -> List[Dict[str, str]]:
        """포지션 표시 옵션 (코드와 표시명)"""
        positions = self.get_position_options()
        return [
            {
                'code': position,
                'display': format_position_display(position)
            }
            for position in positions
        ]

    def get_player_detailed_stats(self, player_id: int) -> Dict[str, Any]:
        """선수 상세 통계"""
        return self.player_repo.get_detailed_stats(player_id)

    def get_players_by_position(self, position: str) -> List[Dict[str, Any]]:
        """포지션별 선수 목록"""
        all_players = self.get_all_players()
        return [player for player in all_players if player['position'] == position]

    def get_leaderboard_data(self) -> Dict[str, List]:
        """순위표 데이터"""
        return self.player_stats_repo.get_leaderboard_data()

    def get_team_average_stats(self) -> Dict[str, float]:
        """팀 평균 통계"""
        return self.player_stats_repo.get_team_average_stats()

    def save_player_stats(self, player_id: int, match_id: int, goals: int, assists: int,
                         saves: int, yellow_cards: int, red_cards: int, mvp: bool) -> bool:
        """선수 통계 저장"""
        return self.player_stats_repo.save_stats(
            player_id, match_id, goals, assists, saves, yellow_cards, red_cards, mvp
        )

    def check_player_name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """선수명 중복 체크"""
        all_players = self.get_all_players()
        for player in all_players:
            if player['name'] == name and (exclude_id is None or player['id'] != exclude_id):
                return True
        return False

    def get_players_for_selection(self) -> List[Dict[str, str]]:
        """선택용 선수 목록 (ID와 이름)"""
        players = self.get_all_players()
        return [
            {
                'id': str(player['id']),
                'name': f"{player['name']} ({player['position_display']})"
            }
            for player in players
        ]

    def update_player(self, player_id: int, name: str, position: str, phone: str = "", email: str = "") -> bool:
        """선수 정보 수정"""
        # 데이터 검증
        validation_result = validate_player_data({
            'name': name,
            'position': position,
            'phone': phone,
            'email': email
        })

        if not validation_result.is_valid:
            raise ValueError(f"Invalid player data: {', '.join(validation_result.errors)}")

        # 전화번호 포맷팅
        formatted_phone = format_phone_number(phone) if phone else ""

        return self.player_repo.update(player_id, name, position, formatted_phone, email)

    def delete_player(self, player_id: int) -> bool:
        """선수 완전 삭제 (개인정보보호)"""
        return self.player_repo.delete(player_id)

# 서비스 인스턴스
player_service = PlayerService()