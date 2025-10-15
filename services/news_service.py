"""소식 관련 비즈니스 로직"""
from typing import List, Dict, Any
from database.repositories import news_repo
from database.models import News
from utils.validators import validate_news_data
from utils.formatters import format_news_category, truncate_text

class NewsService:
    """소식 관련 서비스"""

    def __init__(self):
        self.news_repo = news_repo

    def create_news(self, title: str, content: str, author: str,
                   pinned: bool = False, category: str = "general") -> bool:
        """소식 생성"""
        # 데이터 검증
        validation_result = validate_news_data({
            'title': title,
            'content': content,
            'author': author,
            'category': category
        })

        if not validation_result.is_valid:
            raise ValueError(f"Invalid news data: {', '.join(validation_result.errors)}")

        return self.news_repo.create(title, content, author, pinned, category)

    def get_all_news(self) -> List[Dict[str, Any]]:
        """모든 소식 목록 (고정글 우선)"""
        news_list = self.news_repo.get_all()

        return [
            {
                'id': news['id'],
                'title': news['title'],
                'content': news['content'],
                'content_preview': truncate_text(news['content'], 100),
                'author': news['author'],
                'pinned': bool(news['pinned']),
                'category': news['category'],
                'category_display': format_news_category(news['category']),
                'created_at': news['created_at'],
                'created_date': news['created_at'][:10] if news['created_at'] else ""
            }
            for news in news_list
        ]

    def get_recent_news(self, limit: int = 3) -> List[Dict[str, Any]]:
        """최근 소식"""
        recent_news = self.news_repo.get_recent(limit)

        return [
            {
                'id': news['id'],
                'title': news['title'],
                'content': news['content'],
                'content_preview': truncate_text(news['content'], 100),
                'author': news['author'],
                'pinned': bool(news['pinned']),
                'category': news['category'],
                'category_display': format_news_category(news['category']),
                'created_at': news['created_at'],
                'created_date': news['created_at'][:10] if news['created_at'] else ""
            }
            for news in recent_news
        ]

    def get_pinned_news(self) -> List[Dict[str, Any]]:
        """고정된 소식"""
        all_news = self.get_all_news()
        return [news for news in all_news if news['pinned']]

    def get_news_by_category(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 소식"""
        all_news = self.get_all_news()
        return [news for news in all_news if news['category'] == category]

    def get_category_options(self) -> List[Dict[str, str]]:
        """카테고리 옵션"""
        categories = ['general', 'match', 'notice', 'event']
        return [
            {'code': category, 'display': format_news_category(category)}
            for category in categories
        ]

    def search_news(self, search_term: str) -> List[Dict[str, Any]]:
        """소식 검색 (제목, 내용, 작성자)"""
        all_news = self.get_all_news()
        search_term = search_term.lower().strip()

        if not search_term:
            return all_news

        return [
            news for news in all_news
            if (search_term in news['title'].lower() or
                search_term in news['content'].lower() or
                search_term in news['author'].lower())
        ]

    def get_news_statistics(self) -> Dict[str, Any]:
        """소식 통계"""
        all_news = self.get_all_news()

        category_counts = {}
        for news in all_news:
            category = news['category']
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            'total_news': len(all_news),
            'pinned_count': len([news for news in all_news if news['pinned']]),
            'category_counts': category_counts,
            'recent_authors': list(set([news['author'] for news in all_news[:10]]))
        }

    def get_news_by_author(self, author: str) -> List[Dict[str, Any]]:
        """작성자별 소식"""
        all_news = self.get_all_news()
        return [news for news in all_news if news['author'] == author]

    def validate_news_title_unique(self, title: str, exclude_id: int = None) -> bool:
        """소식 제목 중복 체크"""
        all_news = self.get_all_news()
        for news in all_news:
            if (news['title'] == title and
                (exclude_id is None or news['id'] != exclude_id)):
                return False
        return True

    def delete_news(self, news_id: int) -> bool:
        """소식 삭제"""
        return self.news_repo.delete(news_id)

    def toggle_pinned(self, news_id: int) -> bool:
        """소식 고정 상태 토글"""
        return self.news_repo.toggle_pinned(news_id)

    def get_news_by_id(self, news_id: int) -> Dict[str, Any]:
        """ID로 소식 조회"""
        news = self.news_repo.get_by_id(news_id)
        if news:
            return {
                'id': news['id'],
                'title': news['title'],
                'content': news['content'],
                'content_preview': truncate_text(news['content'], 100),
                'author': news['author'],
                'pinned': bool(news['pinned']),
                'category': news['category'],
                'category_display': format_news_category(news['category']),
                'created_at': news['created_at'],
                'created_date': news['created_at'][:10] if news['created_at'] else ""
            }
        return None

    def update_news(self, news_id: int, title: str, content: str, author: str,
                   pinned: bool = False, category: str = "general") -> bool:
        """소식 수정"""
        # 데이터 검증
        validation_result = validate_news_data({
            'title': title,
            'content': content,
            'author': author,
            'category': category
        })

        if not validation_result.is_valid:
            raise ValueError(f"Invalid news data: {', '.join(validation_result.errors)}")

        return self.news_repo.update(news_id, title, content, author, pinned, category)

# 서비스 인스턴스
news_service = NewsService()