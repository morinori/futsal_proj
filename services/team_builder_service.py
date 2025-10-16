"""팀 구성 관련 비즈니스 로직"""
from typing import List, Dict, Any, Optional, Literal
import random
from dataclasses import dataclass, asdict
from database.repositories import team_distribution_repo


@dataclass
class LayoutResult:
    """팀 레이아웃 계산 결과"""
    team_count: int
    team_size: int
    total_assigned: int
    remainder: int
    is_valid: bool
    message: str


@dataclass
class PlayerInfo:
    """선수 정보"""
    player_id: int
    player_name: str


@dataclass
class TeamDistribution:
    """팀 분배 결과"""
    teams: List[List[PlayerInfo]]
    bench: List[PlayerInfo]
    team_names: List[str]


class TeamBuilderService:
    """팀 구성 관련 서비스"""

    def calculate_layout(
        self,
        total_present: int,
        team_count: Optional[int] = None,
        team_size: Optional[int] = None
    ) -> LayoutResult:
        """
        팀 레이아웃 계산 및 검증

        Args:
            total_present: 참석 선수 총 인원
            team_count: 팀 개수 (None이면 team_size로 계산)
            team_size: 팀당 인원 (None이면 team_count로 계산)

        Returns:
            LayoutResult: 계산된 레이아웃 정보
        """
        # 입력 검증
        if total_present <= 0:
            return LayoutResult(
                team_count=0,
                team_size=0,
                total_assigned=0,
                remainder=0,
                is_valid=False,
                message="참석 인원이 없습니다."
            )

        # 둘 다 None인 경우
        if team_count is None and team_size is None:
            return LayoutResult(
                team_count=0,
                team_size=0,
                total_assigned=0,
                remainder=0,
                is_valid=False,
                message="팀 개수 또는 팀당 인원을 입력해주세요."
            )

        # 둘 다 입력된 경우 - 검증
        if team_count is not None and team_size is not None:
            if team_count < 1 or team_size < 1:
                return LayoutResult(
                    team_count=team_count or 0,
                    team_size=team_size or 0,
                    total_assigned=0,
                    remainder=0,
                    is_valid=False,
                    message="팀 개수와 팀당 인원은 1 이상이어야 합니다."
                )

            total_assigned = team_count * team_size
            remainder = total_present - total_assigned

            if total_assigned > total_present:
                return LayoutResult(
                    team_count=team_count,
                    team_size=team_size,
                    total_assigned=total_assigned,
                    remainder=remainder,
                    is_valid=False,
                    message=f"필요 인원({total_assigned}명)이 참석 인원({total_present}명)보다 많습니다."
                )

            return LayoutResult(
                team_count=team_count,
                team_size=team_size,
                total_assigned=total_assigned,
                remainder=remainder,
                is_valid=True,
                message=f"{team_count}팀 × {team_size}명 + 벤치 {remainder}명"
            )

        # 팀 개수만 입력된 경우
        if team_count is not None:
            if team_count < 1:
                return LayoutResult(
                    team_count=0,
                    team_size=0,
                    total_assigned=0,
                    remainder=0,
                    is_valid=False,
                    message="팀 개수는 1 이상이어야 합니다."
                )

            team_size_calc = total_present // team_count
            if team_size_calc < 1:
                return LayoutResult(
                    team_count=team_count,
                    team_size=team_size_calc,
                    total_assigned=0,
                    remainder=total_present,
                    is_valid=False,
                    message=f"참석 인원이 부족하여 {team_count}팀을 구성할 수 없습니다."
                )

            total_assigned = team_count * team_size_calc
            remainder = total_present - total_assigned

            return LayoutResult(
                team_count=team_count,
                team_size=team_size_calc,
                total_assigned=total_assigned,
                remainder=remainder,
                is_valid=True,
                message=f"{team_count}팀 × {team_size_calc}명 + 벤치 {remainder}명"
            )

        # 팀당 인원만 입력된 경우
        if team_size is not None:
            if team_size < 1:
                return LayoutResult(
                    team_count=0,
                    team_size=0,
                    total_assigned=0,
                    remainder=0,
                    is_valid=False,
                    message="팀당 인원은 1 이상이어야 합니다."
                )

            team_count_calc = total_present // team_size
            if team_count_calc < 1:
                return LayoutResult(
                    team_count=team_count_calc,
                    team_size=team_size,
                    total_assigned=0,
                    remainder=total_present,
                    is_valid=False,
                    message=f"참석 인원이 부족하여 팀당 {team_size}명으로 팀을 구성할 수 없습니다."
                )

            total_assigned = team_count_calc * team_size
            remainder = total_present - total_assigned

            return LayoutResult(
                team_count=team_count_calc,
                team_size=team_size,
                total_assigned=total_assigned,
                remainder=remainder,
                is_valid=True,
                message=f"{team_count_calc}팀 × {team_size}명 + 벤치 {remainder}명"
            )

        # 이론적으로 도달 불가
        return LayoutResult(
            team_count=0,
            team_size=0,
            total_assigned=0,
            remainder=0,
            is_valid=False,
            message="알 수 없는 오류가 발생했습니다."
        )

    def distribute_players(
        self,
        players: List[Dict[str, Any]],
        team_count: int,
        team_size: int,
        strategy: Literal["balanced_random"] = "balanced_random"
    ) -> TeamDistribution:
        """
        선수들을 팀에 분배

        Args:
            players: 선수 리스트 (player_id, player_name 포함)
            team_count: 팀 개수
            team_size: 팀당 인원
            strategy: 분배 전략 (현재는 balanced_random만 지원)

        Returns:
            TeamDistribution: 분배 결과
        """
        if not players:
            return TeamDistribution(
                teams=[[] for _ in range(team_count)],
                bench=[],
                team_names=[f"Team {chr(65+i)}" for i in range(team_count)]
            )

        # 선수 정보 변환
        player_infos = [
            PlayerInfo(player_id=p['player_id'], player_name=p['player_name'])
            for p in players
        ]

        # 전략에 따른 분배
        if strategy == "balanced_random":
            return self._distribute_balanced_random(player_infos, team_count, team_size)

        # 기본값
        return self._distribute_balanced_random(player_infos, team_count, team_size)

    def _distribute_balanced_random(
        self,
        players: List[PlayerInfo],
        team_count: int,
        team_size: int
    ) -> TeamDistribution:
        """균등 랜덤 분배 (셔플 후 라운드로빈)"""
        # 선수 셔플
        shuffled = players.copy()
        random.shuffle(shuffled)

        # 팀 초기화
        teams: List[List[PlayerInfo]] = [[] for _ in range(team_count)]

        # 라운드로빈 방식으로 분배
        total_to_assign = team_count * team_size
        for i in range(min(total_to_assign, len(shuffled))):
            team_idx = i % team_count
            if len(teams[team_idx]) < team_size:
                teams[team_idx].append(shuffled[i])

        # 벤치 인원
        bench = shuffled[total_to_assign:] if len(shuffled) > total_to_assign else []

        # 팀 이름 생성
        team_names = [f"Team {chr(65+i)}" for i in range(team_count)]

        return TeamDistribution(
            teams=teams,
            bench=bench,
            team_names=team_names
        )

    def rebalance_with_remainder(
        self,
        teams: List[List[PlayerInfo]],
        bench: List[PlayerInfo],
        mode: Literal["bench", "spread"] = "bench"
    ) -> TeamDistribution:
        """
        잔여 인원 재분배

        Args:
            teams: 현재 팀 구성
            bench: 벤치 인원
            mode: 재분배 모드 ("bench": 벤치 유지, "spread": 팀에 분산)

        Returns:
            TeamDistribution: 재분배 결과
        """
        if mode == "bench" or not bench:
            return TeamDistribution(
                teams=teams,
                bench=bench,
                team_names=[f"Team {chr(65+i)}" for i in range(len(teams))]
            )

        # "spread" 모드: 벤치 인원을 팀에 균등 분산
        new_teams = [team.copy() for team in teams]
        new_bench = bench.copy()

        team_idx = 0
        while new_bench:
            new_teams[team_idx].append(new_bench.pop(0))
            team_idx = (team_idx + 1) % len(new_teams)

        return TeamDistribution(
            teams=new_teams,
            bench=[],
            team_names=[f"Team {chr(65+i)}" for i in range(len(new_teams))]
        )

    def move_player_to_team(
        self,
        teams: List[List[PlayerInfo]],
        bench: List[PlayerInfo],
        player_id: int,
        from_location: str,  # "team_0", "team_1", ..., "bench"
        to_location: str     # "team_0", "team_1", ..., "bench"
    ) -> tuple[List[List[PlayerInfo]], List[PlayerInfo], bool, str]:
        """
        선수를 다른 팀이나 벤치로 이동

        Returns:
            (teams, bench, success, message)
        """
        # 선수 찾기 및 제거
        player_to_move: Optional[PlayerInfo] = None

        if from_location == "bench":
            for player in bench:
                if player.player_id == player_id:
                    player_to_move = player
                    bench.remove(player)
                    break
        elif from_location.startswith("team_"):
            try:
                team_idx = int(from_location.split("_")[1])
                if 0 <= team_idx < len(teams):
                    for player in teams[team_idx]:
                        if player.player_id == player_id:
                            player_to_move = player
                            teams[team_idx].remove(player)
                            break
            except (ValueError, IndexError):
                return teams, bench, False, "잘못된 출발 위치입니다."

        if not player_to_move:
            return teams, bench, False, "선수를 찾을 수 없습니다."

        # 목적지에 추가
        if to_location == "bench":
            bench.append(player_to_move)
        elif to_location.startswith("team_"):
            try:
                team_idx = int(to_location.split("_")[1])
                if 0 <= team_idx < len(teams):
                    teams[team_idx].append(player_to_move)
                else:
                    # 복구
                    if from_location == "bench":
                        bench.append(player_to_move)
                    else:
                        from_team_idx = int(from_location.split("_")[1])
                        teams[from_team_idx].append(player_to_move)
                    return teams, bench, False, "잘못된 목적지 위치입니다."
            except (ValueError, IndexError):
                # 복구
                if from_location == "bench":
                    bench.append(player_to_move)
                else:
                    from_team_idx = int(from_location.split("_")[1])
                    teams[from_team_idx].append(player_to_move)
                return teams, bench, False, "잘못된 목적지 위치입니다."

        return teams, bench, True, "선수가 이동되었습니다."

    def validate_distribution(
        self,
        teams: List[List[PlayerInfo]],
        bench: List[PlayerInfo],
        total_players: int
    ) -> tuple[bool, str]:
        """
        팀 분배 검증 (중복 선수 확인, 인원 수 확인)

        Returns:
            (is_valid, message)
        """
        # 모든 선수 ID 수집
        all_player_ids = []
        for team in teams:
            all_player_ids.extend([p.player_id for p in team])
        all_player_ids.extend([p.player_id for p in bench])

        # 중복 확인
        if len(all_player_ids) != len(set(all_player_ids)):
            return False, "중복된 선수가 있습니다."

        # 총 인원 확인
        if len(all_player_ids) != total_players:
            return False, f"총 인원이 일치하지 않습니다. (예상: {total_players}, 실제: {len(all_player_ids)})"

        return True, "검증 통과"

    def save_distribution(
        self,
        match_id: int,
        teams: List[List[PlayerInfo]],
        bench: List[PlayerInfo],
        team_names: List[str],
        config: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> bool:
        """
        팀 구성을 데이터베이스에 저장

        Args:
            match_id: 경기 ID
            teams: 팀별 선수 리스트
            bench: 벤치 선수 리스트
            team_names: 팀 이름 리스트
            config: 팀 설정 정보
            created_by: 생성한 관리자 ID

        Returns:
            성공 여부
        """
        # PlayerInfo 객체를 dict로 변환
        teams_dict = [
            [asdict(player) for player in team]
            for team in teams
        ]
        bench_dict = [asdict(player) for player in bench]

        team_data = {
            'teams': teams_dict,
            'bench': bench_dict,
            'team_names': team_names,
            'config': config
        }

        return team_distribution_repo.save(match_id, team_data, created_by)

    def get_distribution(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        경기별 저장된 팀 구성 조회

        Args:
            match_id: 경기 ID

        Returns:
            팀 구성 데이터 (teams, bench, team_names, config 포함)
        """
        distribution = team_distribution_repo.get_by_match_id(match_id)
        if distribution and distribution.get('team_data'):
            return distribution['team_data']
        return None

    def delete_distribution(self, match_id: int) -> bool:
        """
        팀 구성 삭제

        Args:
            match_id: 경기 ID

        Returns:
            성공 여부
        """
        return team_distribution_repo.delete(match_id)


# 싱글톤 인스턴스
team_builder_service = TeamBuilderService()
