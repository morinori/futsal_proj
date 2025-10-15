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
    if match_time and not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', match_time):
        errors.append("올바른 시간 형식을 입력해주세요.")

    # 출석 마감 시간 검증
    attendance_lock_minutes = data.get('attendance_lock_minutes')
    if attendance_lock_minutes is not None:
        if not isinstance(attendance_lock_minutes, int):
            errors.append("출석 마감 시간은 정수여야 합니다.")
        elif attendance_lock_minutes < 0 or attendance_lock_minutes > 180:
            errors.append("출석 마감 시간은 0~180분 범위여야 합니다.")
        elif attendance_lock_minutes % 30 != 0:
            errors.append("출석 마감 시간은 30분 단위여야 합니다.")

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
    elif len(name) > 20:
        errors.append("이름은 20글자 이하여야 합니다.")

    # 포지션 검증
    position = data.get('position')
    valid_positions = ['GK', 'DF', 'MF', 'FW']
    if not position:
        errors.append("포지션을 선택해주세요.")
    elif position not in valid_positions:
        errors.append(f"유효한 포지션을 선택해주세요: {', '.join(valid_positions)}")

    # 전화번호 검증 (선택사항)
    phone = data.get('phone', '').strip()
    if phone and not re.match(r'^010-\d{4}-\d{4}$|^010\d{8}$', phone):
        errors.append("전화번호 형식이 올바르지 않습니다. (예: 010-1234-5678)")

    # 이메일 검증 (선택사항)
    email = data.get('email', '').strip()
    if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append("이메일 형식이 올바르지 않습니다.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)

def validate_field_data(data: Dict[str, Any]) -> ValidationResult:
    """구장 데이터 검증"""
    errors = []

    # 구장명 검증
    name = data.get('name', '').strip()
    if not name:
        errors.append("구장명을 입력해주세요.")
    elif len(name) < 2:
        errors.append("구장명은 2글자 이상이어야 합니다.")
    elif len(name) > 50:
        errors.append("구장명은 50글자 이하여야 합니다.")

    # 대관료 검증
    cost = data.get('cost')
    if cost is not None:
        if not isinstance(cost, (int, float)) or cost < 0:
            errors.append("대관료는 0 이상의 숫자여야 합니다.")
        elif cost > 1000000:
            errors.append("대관료는 100만원 이하여야 합니다.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)

def validate_finance_data(data: Dict[str, Any]) -> ValidationResult:
    """재정 데이터 검증"""
    errors = []

    # 설명 검증
    description = data.get('description', '').strip()
    if not description:
        errors.append("설명을 입력해주세요.")
    elif len(description) > 100:
        errors.append("설명은 100글자 이하여야 합니다.")

    # 금액 검증
    amount = data.get('amount')
    if not amount:
        errors.append("금액을 입력해주세요.")
    elif not isinstance(amount, (int, float)) or amount <= 0:
        errors.append("금액은 0보다 큰 숫자여야 합니다.")
    elif amount > 10000000:
        errors.append("금액은 1천만원 이하여야 합니다.")

    # 타입 검증
    transaction_type = data.get('type')
    if not transaction_type:
        errors.append("타입을 선택해주세요.")
    elif transaction_type not in ['income', 'expense']:
        errors.append("타입은 수입 또는 지출이어야 합니다.")

    # 카테고리 검증
    category = data.get('category')
    valid_categories = ['match', 'dues', 'equipment', 'event', 'other']
    if category and category not in valid_categories:
        errors.append(f"유효한 카테고리를 선택해주세요: {', '.join(valid_categories)}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)

def validate_news_data(data: Dict[str, Any]) -> ValidationResult:
    """소식 데이터 검증"""
    errors = []

    # 제목 검증
    title = data.get('title', '').strip()
    if not title:
        errors.append("제목을 입력해주세요.")
    elif len(title) > 100:
        errors.append("제목은 100글자 이하여야 합니다.")

    # 내용 검증
    content = data.get('content', '').strip()
    if not content:
        errors.append("내용을 입력해주세요.")
    elif len(content) > 5000:
        errors.append("내용은 5000글자 이하여야 합니다.")

    # 작성자 검증
    author = data.get('author', '').strip()
    if not author:
        errors.append("작성자를 입력해주세요.")
    elif len(author) > 20:
        errors.append("작성자는 20글자 이하여야 합니다.")

    # 카테고리 검증
    category = data.get('category')
    valid_categories = ['general', 'match', 'notice', 'event']
    if category and category not in valid_categories:
        errors.append(f"유효한 카테고리를 선택해주세요: {', '.join(valid_categories)}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)