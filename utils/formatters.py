"""데이터 포맷팅 함수들"""
from typing import List, Tuple
from datetime import date
from config.settings import ui_config

def format_currency(amount: int) -> str:
    """통화 포맷팅"""
    return f"{amount:,}원"

def format_date_korean(date_obj: date) -> str:
    """한국어 날짜 포맷팅"""
    weekdays = ['월', '화', '수', '목', '금', '토', '일']
    weekday = weekdays[date_obj.weekday()]
    return f"{date_obj.year}년 {date_obj.month}월 {date_obj.day}일 ({weekday})"

def format_time_display(time_str: str) -> str:
    """시간 표시 포맷팅"""
    try:
        hour = int(time_str.split(':')[0])
        if hour < 12:
            return f"오전 {hour}시" if hour != 0 else "오전 12시"
        else:
            display_hour = hour - 12 if hour != 12 else 12
            return f"오후 {display_hour}시"
    except:
        return time_str

def format_time_options() -> List[Tuple[str, str]]:
    """시간 선택 옵션 생성"""
    time_options = []

    for hour in range(ui_config.CALENDAR_START_HOUR, ui_config.CALENDAR_END_HOUR + 1):
        time_str = f"{hour:02d}:00"
        display_time = format_time_display(time_str)
        time_options.append((time_str, display_time))

    return time_options

def format_phone_number(phone: str) -> str:
    """전화번호 포맷팅"""
    # 숫자만 추출
    digits = ''.join(filter(str.isdigit, phone))

    if len(digits) == 11 and digits.startswith('010'):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"

    return phone

def format_position_display(position: str) -> str:
    """포지션 표시 포맷팅"""
    position_names = {
        'GK': '골키퍼',
        'DF': '수비수',
        'MF': '미드필더',
        'FW': '공격수'
    }
    return position_names.get(position, position)

def format_match_result(result: str) -> str:
    """경기 결과 포맷팅"""
    if not result:
        return "결과 미입력"
    return result

def format_attendance_status(status: str) -> str:
    """출석 상태 포맷팅"""
    status_names = {
        'present': '출석',
        'absent': '결석',
        'late': '지각'
    }
    return status_names.get(status, status)

def format_news_category(category: str) -> str:
    """소식 카테고리 포맷팅"""
    category_names = {
        'general': '일반',
        'match': '경기',
        'notice': '공지',
        'event': '이벤트'
    }
    return category_names.get(category, category)

def format_finance_type(finance_type: str) -> str:
    """재정 타입 포맷팅"""
    type_names = {
        'income': '수입',
        'expense': '지출'
    }
    return type_names.get(finance_type, finance_type)

def format_finance_category(category: str) -> str:
    """재정 카테고리 포맷팅"""
    category_names = {
        'match': '경기',
        'dues': '회비',
        'equipment': '장비',
        'event': '이벤트',
        'other': '기타'
    }
    return category_names.get(category, category)

def truncate_text(text: str, max_length: int = 100) -> str:
    """텍스트 길이 제한"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_field_display_name(name: str, address: str) -> str:
    """구장 표시명 포맷팅"""
    return f"{name} - {address}" if address else name