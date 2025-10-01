"""인증 서비스"""
import bcrypt
from typing import Optional, Dict, Any
from database.repositories import admin_repo
from database.models import Admin


class AuthService:
    """관리자 인증 서비스"""

    def __init__(self):
        self.admin_repo = admin_repo

    def hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """관리자 로그인"""
        admin = self.admin_repo.get_by_username(username)
        if not admin:
            return None

        if not self.verify_password(password, admin['password_hash']):
            return None

        # 로그인 시간 업데이트
        self.admin_repo.update_last_login(admin['id'])

        # 비밀번호 해시 제거 후 반환
        admin_info = admin.copy()
        del admin_info['password_hash']
        return admin_info

    def create_admin(self, username: str, password: str, name: str, role: str = "admin") -> bool:
        """새 관리자 생성"""
        # 사용자명 중복 확인
        existing_admin = self.admin_repo.get_by_username(username)
        if existing_admin:
            return False

        password_hash = self.hash_password(password)
        admin = Admin(
            username=username,
            password_hash=password_hash,
            name=name,
            role=role
        )

        return self.admin_repo.create(admin)

    def change_password(self, admin_id: int, old_password: str, new_password: str) -> bool:
        """관리자 비밀번호 변경"""
        admin = self.admin_repo.get_by_id(admin_id)
        if not admin:
            return False

        # 기존 비밀번호 확인
        if not self.verify_password(old_password, admin['password_hash']):
            return False

        # 새 비밀번호 해시화 및 업데이트
        new_password_hash = self.hash_password(new_password)
        return self.admin_repo.update_password(admin_id, new_password_hash)

    def get_all_admins(self):
        """모든 활성 관리자 목록"""
        admins = self.admin_repo.get_all_active()
        # 비밀번호 해시 제거
        for admin in admins:
            if 'password_hash' in admin:
                del admin['password_hash']
        return admins

    def deactivate_admin(self, admin_id: int) -> bool:
        """관리자 비활성화"""
        return self.admin_repo.deactivate(admin_id)


# 서비스 인스턴스
auth_service = AuthService()