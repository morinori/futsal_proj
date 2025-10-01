"""재정 관련 비즈니스 로직"""
from typing import List, Dict, Any, Optional
from datetime import date
from database.repositories import finance_repo
from database.models import FinanceRecord
from utils.validators import validate_finance_data
from utils.formatters import format_currency, format_finance_type, format_finance_category

class FinanceService:
    """재정 관련 서비스"""

    def __init__(self):
        self.finance_repo = finance_repo

    def create_record(self, date_str: str, description: str, amount: int,
                     transaction_type: str, category: str = "match") -> bool:
        """재정 기록 생성"""
        # 데이터 검증
        validation_result = validate_finance_data({
            'description': description,
            'amount': amount,
            'type': transaction_type,
            'category': category
        })

        if not validation_result.is_valid:
            raise ValueError(f"Invalid finance data: {', '.join(validation_result.errors)}")

        return self.finance_repo.create(date_str, description, amount, transaction_type, category)

    def get_financial_summary(self) -> Dict[str, Any]:
        """재정 요약"""
        summary = self.finance_repo.get_summary()

        total_income = summary.get('total_income', 0)
        total_expense = summary.get('total_expense', 0)
        balance = total_income - total_expense

        return {
            'total_income': total_income,
            'total_income_display': format_currency(total_income),
            'total_expense': total_expense,
            'total_expense_display': format_currency(total_expense),
            'balance': balance,
            'balance_display': format_currency(balance),
            'is_positive': balance >= 0
        }

    def get_monthly_data(self) -> List[Dict[str, Any]]:
        """월별 재정 데이터"""
        monthly_data = self.finance_repo.get_monthly_data()

        return [
            {
                'month': data['month'],
                'income': data['income'],
                'income_display': format_currency(data['income']),
                'expense': data['expense'],
                'expense_display': format_currency(data['expense']),
                'balance': data['income'] - data['expense'],
                'balance_display': format_currency(data['income'] - data['expense'])
            }
            for data in monthly_data
        ]

    def get_expense_by_category(self) -> List[Dict[str, Any]]:
        """카테고리별 지출"""
        category_data = self.finance_repo.get_expense_by_category()

        return [
            {
                'category': data['category'],
                'category_display': format_finance_category(data['category']),
                'amount': data['amount'],
                'amount_display': format_currency(data['amount'])
            }
            for data in category_data
        ]

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """모든 거래 내역"""
        transactions = self.finance_repo.get_all_transactions()

        return [
            {
                'id': trans['id'],
                'date': trans['date'],
                'description': trans['description'],
                'amount': trans['amount'],
                'amount_display': format_currency(trans['amount']),
                'type': trans['type'],
                'type_display': format_finance_type(trans['type']),
                'category': trans['category'],
                'category_display': format_finance_category(trans['category']),
                'created_at': trans['created_at'],
                'amount_with_sign': f"+{format_currency(trans['amount'])}" if trans['type'] == 'income' else f"-{format_currency(trans['amount'])}"
            }
            for trans in transactions
        ]

    def get_team_balance(self) -> int:
        """팀 잔고"""
        return self.finance_repo.get_team_balance()

    def get_transaction_type_options(self) -> List[Dict[str, str]]:
        """거래 타입 옵션"""
        return [
            {'code': 'income', 'display': format_finance_type('income')},
            {'code': 'expense', 'display': format_finance_type('expense')}
        ]

    def get_category_options(self) -> List[Dict[str, str]]:
        """카테고리 옵션"""
        categories = ['match', 'dues', 'equipment', 'event', 'other']
        return [
            {'code': category, 'display': format_finance_category(category)}
            for category in categories
        ]

    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 거래 내역"""
        all_transactions = self.get_all_transactions()
        return all_transactions[:limit]

    def get_transactions_by_type(self, transaction_type: str) -> List[Dict[str, Any]]:
        """타입별 거래 내역"""
        all_transactions = self.get_all_transactions()
        return [trans for trans in all_transactions if trans['type'] == transaction_type]

    def get_transactions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 거래 내역"""
        all_transactions = self.get_all_transactions()
        return [trans for trans in all_transactions if trans['category'] == category]

    def calculate_monthly_stats(self, year: int, month: int) -> Dict[str, Any]:
        """특정 월 통계"""
        monthly_data = self.get_monthly_data()
        target_month = f"{year}-{month:02d}"

        for data in monthly_data:
            if data['month'] == target_month:
                return data

        # 해당 월 데이터가 없으면 기본값 반환
        return {
            'month': target_month,
            'income': 0,
            'income_display': format_currency(0),
            'expense': 0,
            'expense_display': format_currency(0),
            'balance': 0,
            'balance_display': format_currency(0)
        }

    def delete_transaction(self, finance_id: int) -> bool:
        """재정 기록 삭제"""
        # 삭제 전 기록 존재 확인
        record = self.finance_repo.get_by_id(finance_id)
        if not record:
            raise ValueError(f"Finance record with id {finance_id} not found")

        return self.finance_repo.delete(finance_id)

    def get_transaction_by_id(self, finance_id: int) -> Optional[Dict[str, Any]]:
        """특정 거래 내역 조회"""
        record = self.finance_repo.get_by_id(finance_id)

        if not record:
            return None

        return {
            'id': record['id'],
            'date': record['date'],
            'description': record['description'],
            'amount': record['amount'],
            'amount_display': format_currency(record['amount']),
            'type': record['type'],
            'type_display': format_finance_type(record['type']),
            'category': record['category'],
            'category_display': format_finance_category(record['category']),
            'created_at': record['created_at'],
            'amount_with_sign': f"+{format_currency(record['amount'])}" if record['type'] == 'income' else f"-{format_currency(record['amount'])}"
        }

# 서비스 인스턴스
finance_service = FinanceService()