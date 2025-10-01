"""파일 보안 검증 유틸리티"""
import os
import re
import hashlib
import mimetypes
from typing import Optional, Dict, Any, List
from config.settings import app_config


class FileSecurityValidator:
    """파일 보안 검증 클래스"""

    @staticmethod
    def validate_file_upload(file_data: bytes, filename: str) -> Dict[str, Any]:
        """파일 업로드 종합 보안 검증

        Args:
            file_data: 파일 데이터 (바이트)
            filename: 원본 파일명

        Returns:
            Dict: {
                'is_valid': bool,
                'error_message': str,
                'safe_filename': str,
                'file_extension': str
            }
        """
        result = {
            'is_valid': False,
            'error_message': '',
            'safe_filename': '',
            'file_extension': ''
        }

        # 1. 파일 크기 검증
        size_check = FileSecurityValidator._validate_file_size(file_data)
        if not size_check['is_valid']:
            result['error_message'] = size_check['error_message']
            return result

        # 2. 파일명 검증
        filename_check = FileSecurityValidator._validate_filename(filename)
        if not filename_check['is_valid']:
            result['error_message'] = filename_check['error_message']
            return result

        # 3. 확장자 검증
        extension_check = FileSecurityValidator._validate_file_extension(filename)
        if not extension_check['is_valid']:
            result['error_message'] = extension_check['error_message']
            return result

        # 4. 파일 내용 검증 (매직 바이트)
        content_check = FileSecurityValidator._validate_file_content(
            file_data, extension_check['file_extension']
        )
        if not content_check['is_valid']:
            result['error_message'] = content_check['error_message']
            return result

        # 5. 안전한 파일명 생성
        safe_filename = FileSecurityValidator._generate_safe_filename(
            file_data, extension_check['file_extension']
        )

        result.update({
            'is_valid': True,
            'safe_filename': safe_filename,
            'file_extension': extension_check['file_extension']
        })

        return result

    @staticmethod
    def _validate_file_size(file_data: bytes) -> Dict[str, Any]:
        """파일 크기 검증"""
        file_size = len(file_data)
        max_size = app_config.MAX_FILE_SIZE

        if file_size > max_size:
            max_mb = max_size // (1024 * 1024)
            current_mb = file_size / (1024 * 1024)
            return {
                'is_valid': False,
                'error_message': f'파일 크기가 너무 큽니다. 최대 {max_mb}MB까지 가능합니다. (현재: {current_mb:.1f}MB)'
            }

        if file_size == 0:
            return {
                'is_valid': False,
                'error_message': '빈 파일은 업로드할 수 없습니다.'
            }

        return {'is_valid': True}

    @staticmethod
    def _validate_filename(filename: str) -> Dict[str, Any]:
        """파일명 보안 검증"""
        if not filename:
            return {
                'is_valid': False,
                'error_message': '파일명이 없습니다.'
            }

        # 파일명 길이 제한
        if len(filename) > app_config.MAX_FILENAME_LENGTH:
            return {
                'is_valid': False,
                'error_message': f'파일명이 너무 깁니다. 최대 {app_config.MAX_FILENAME_LENGTH}자까지 가능합니다.'
            }

        # 위험한 문자 검사
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*', '\x00']
        for char in dangerous_chars:
            if char in filename:
                return {
                    'is_valid': False,
                    'error_message': f'파일명에 허용되지 않는 문자가 포함되어 있습니다: {char}'
                }

        # 위험한 파일명 패턴 검사
        dangerous_patterns = [
            r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows 예약어
            r'^\.',  # 숨김 파일
            r'.*\.(bat|cmd|exe|scr|vbs|js|jar|com|pif)$',  # 실행 파일
        ]

        for pattern in dangerous_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return {
                    'is_valid': False,
                    'error_message': '위험한 파일명 패턴이 감지되었습니다.'
                }

        return {'is_valid': True}

    @staticmethod
    def _validate_file_extension(filename: str) -> Dict[str, Any]:
        """파일 확장자 검증"""
        if '.' not in filename:
            return {
                'is_valid': False,
                'error_message': '파일 확장자가 없습니다.'
            }

        # 마지막 점 이후를 확장자로 인식 (다중 확장자 공격 방지)
        file_extension = filename.split('.')[-1].lower()

        if not file_extension:
            return {
                'is_valid': False,
                'error_message': '파일 확장자가 비어있습니다.'
            }

        if file_extension not in app_config.ALLOWED_EXTENSIONS:
            allowed = ', '.join(app_config.ALLOWED_EXTENSIONS)
            return {
                'is_valid': False,
                'error_message': f'허용되지 않는 파일 형식입니다. 허용 형식: {allowed}'
            }

        return {
            'is_valid': True,
            'file_extension': file_extension
        }

    @staticmethod
    def _validate_file_content(file_data: bytes, file_extension: str) -> Dict[str, Any]:
        """파일 내용 검증 (매직 바이트)"""
        if not app_config.SCAN_FILE_CONTENT:
            return {'is_valid': True}

        if file_extension not in app_config.ALLOWED_MIME_TYPES:
            return {
                'is_valid': False,
                'error_message': '지원되지 않는 파일 형식입니다.'
            }

        mime_config = app_config.ALLOWED_MIME_TYPES[file_extension]
        magic_bytes_list = mime_config['magic_bytes']

        # 매직 바이트 검증
        file_header = file_data[:32]  # 처음 32바이트 검사

        for magic_bytes in magic_bytes_list:
            if file_header.startswith(magic_bytes):
                return {'is_valid': True}

        return {
            'is_valid': False,
            'error_message': f'파일 내용이 {file_extension.upper()} 형식과 일치하지 않습니다.'
        }

    @staticmethod
    def _generate_safe_filename(file_data: bytes, file_extension: str) -> str:
        """안전한 파일명 생성"""
        # 파일 내용의 해시값으로 고유한 파일명 생성
        file_hash = hashlib.sha256(file_data).hexdigest()[:16]
        return f"{file_hash}.{file_extension}"

    @staticmethod
    def validate_file_path(file_path: str, base_dir: str) -> bool:
        """파일 경로 검증 (경로 조작 공격 방지)"""
        try:
            # 경로 정규화
            normalized_path = os.path.normpath(file_path)
            normalized_base = os.path.normpath(base_dir)

            # 절대 경로로 변환
            abs_path = os.path.abspath(normalized_path)
            abs_base = os.path.abspath(normalized_base)

            # 기본 디렉토리 내부에 있는지 확인
            return abs_path.startswith(abs_base + os.sep) or abs_path == abs_base

        except (ValueError, OSError):
            return False

    @staticmethod
    def sanitize_text_input(text: str) -> str:
        """텍스트 입력 XSS 방지 처리"""
        if not text:
            return ""

        # HTML 태그 제거
        text = re.sub(r'<[^>]*>', '', text)

        # 특수 문자 이스케이프
        dangerous_chars = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;',
            '/': '&#x2F;'
        }

        for char, escape in dangerous_chars.items():
            text = text.replace(char, escape)

        # 스크립트 관련 키워드 제거
        script_patterns = [
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'onmouseover=',
        ]

        for pattern in script_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        return text.strip()


# 편의 함수들
def validate_upload_file(file_data: bytes, filename: str) -> Dict[str, Any]:
    """파일 업로드 검증 (편의 함수)"""
    return FileSecurityValidator.validate_file_upload(file_data, filename)


def sanitize_input(text: str) -> str:
    """입력 텍스트 정화 (편의 함수)"""
    return FileSecurityValidator.sanitize_text_input(text)


def is_safe_path(file_path: str, base_dir: str = None) -> bool:
    """안전한 경로인지 검증 (편의 함수)"""
    if base_dir is None:
        base_dir = app_config.UPLOAD_DIR
    return FileSecurityValidator.validate_file_path(file_path, base_dir)