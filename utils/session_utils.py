"""세션 지속성 유틸리티"""
import streamlit as st
import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


SESSION_DIR = "/tmp/futsal_sessions"
SESSION_TIMEOUT_HOURS = 1  # 1시간으로 단축


def _get_session_file_path(session_id: str) -> str:
    """세션 파일 경로 반환"""
    os.makedirs(SESSION_DIR, exist_ok=True)
    return os.path.join(SESSION_DIR, f"session_{session_id}.json")


def _generate_session_id() -> str:
    """세션 ID 생성 (브라우저 정보 기반)"""
    try:
        # Method 1: Try to get session info from runtime
        try:
            session_info = st.runtime.get_instance().session_info
            browser_info = f"{session_info.session_id}_{session_info.user_ip}"
            return hashlib.md5(browser_info.encode()).hexdigest()
        except:
            pass

        # Method 2: Try to get from script run context
        try:
            ctx = st.runtime.scriptrunner.get_script_run_ctx()
            if hasattr(ctx, 'session_id'):
                return hashlib.md5(ctx.session_id.encode()).hexdigest()
        except:
            pass

        # Method 3: Try to access session state hash
        try:
            session_hash = str(hash(str(st.session_state)))
            return hashlib.md5(session_hash.encode()).hexdigest()
        except:
            pass

    except Exception:
        pass

    # Final fallback: generate time-based consistent ID within session
    # This should only happen in development/testing
    import uuid
    fallback_id = str(uuid.uuid4())[:8] + "_fallback"
    return hashlib.md5(fallback_id.encode()).hexdigest()


def _is_session_expired(session_data: dict) -> bool:
    """세션 만료 여부 확인"""
    try:
        expire_time = datetime.fromisoformat(session_data.get('expire_time', ''))
        return datetime.now() > expire_time
    except (ValueError, TypeError):
        return True


def save_admin_session(admin_data: dict):
    """관리자 세션을 파일에 저장"""
    try:
        session_id = _generate_session_id()
        expire_time = (datetime.now() + timedelta(hours=SESSION_TIMEOUT_HOURS)).isoformat()

        session_data = {
            'admin_id': admin_data['id'],
            'admin_username': admin_data['username'],
            'admin_name': admin_data['name'],
            'admin_role': admin_data.get('role', 'admin'),
            'expire_time': expire_time,
            'created_at': datetime.now().isoformat()
        }

        session_file = _get_session_file_path(session_id)
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        # 세션 ID를 Streamlit 세션에 저장
        st.session_state['_session_id'] = session_id

    except Exception as e:
        st.error(f"세션 저장 실패: {e}")


def load_admin_session() -> Optional[Dict[str, Any]]:
    """파일에서 관리자 세션 로드"""
    try:
        session_id = st.session_state.get('_session_id')
        if not session_id:
            # Try to find existing session files first
            if os.path.exists(SESSION_DIR):
                for filename in os.listdir(SESSION_DIR):
                    if filename.startswith('session_') and filename.endswith('.json'):
                        file_path = os.path.join(SESSION_DIR, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                session_data = json.load(f)
                            if not _is_session_expired(session_data):
                                # Found valid session, extract ID from filename
                                session_id = filename.replace('session_', '').replace('.json', '')
                                st.session_state['_session_id'] = session_id
                                break
                        except (json.JSONDecodeError, FileNotFoundError):
                            continue

            # If no valid session found, return None (don't create new ID here)
            if not session_id:
                return None

        session_file = _get_session_file_path(session_id)

        if not os.path.exists(session_file):
            return None

        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        # 세션 만료 체크
        if _is_session_expired(session_data):
            os.remove(session_file)
            return None

        return session_data

    except Exception as e:
        # 에러 발생 시 조용히 None 반환 (로그인 상태로 돌아감)
        return None


def clear_admin_session():
    """관리자 세션 파일 삭제"""
    try:
        session_id = st.session_state.get('_session_id')
        if session_id:
            session_file = _get_session_file_path(session_id)
            if os.path.exists(session_file):
                os.remove(session_file)

        # Streamlit 세션 상태 정리
        admin_keys = [
            'is_admin',
            'admin_id',
            'admin_username',
            'admin_name',
            'admin_role',
            'admin_menu_expanded',
            '_session_id',
            'last_activity'
        ]

        for key in admin_keys:
            if key in st.session_state:
                del st.session_state[key]

    except Exception as e:
        # 에러가 발생해도 세션 상태는 정리
        pass


def restore_admin_session():
    """관리자 세션 복원 - 더 짧은 만료 시간 적용"""
    if st.session_state.get('is_admin', False):
        # 기존 세션이 있어도 만료 시간 체크
        last_activity = st.session_state.get('last_activity')
        if last_activity:
            try:
                last_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_time > timedelta(minutes=30):  # 30분 비활성 시 만료
                    clear_admin_session()
                    return False
            except:
                pass
        # 마지막 활동 시간 업데이트
        st.session_state['last_activity'] = datetime.now().isoformat()
        return True

    # 파일에서 세션 데이터 로드
    session_data = load_admin_session()

    if session_data and all(key in session_data for key in ['admin_id', 'admin_username', 'admin_name']):
        # 세션 상태 복원
        st.session_state['is_admin'] = True
        st.session_state['admin_id'] = session_data['admin_id']
        st.session_state['admin_username'] = session_data['admin_username']
        st.session_state['admin_name'] = session_data['admin_name']
        st.session_state['admin_role'] = session_data.get('admin_role', 'admin')
        st.session_state['admin_menu_expanded'] = False
        st.session_state['last_activity'] = datetime.now().isoformat()

        # Log successful session restoration
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Session restored for admin: {session_data['admin_username']}")
        except:
            pass

        return True

    return False


def cleanup_expired_sessions():
    """만료된 세션 파일들 정리"""
    try:
        if not os.path.exists(SESSION_DIR):
            return

        current_time = datetime.now()
        for filename in os.listdir(SESSION_DIR):
            if filename.startswith('session_') and filename.endswith('.json'):
                file_path = os.path.join(SESSION_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)

                    if _is_session_expired(session_data):
                        os.remove(file_path)

                except (json.JSONDecodeError, FileNotFoundError):
                    # 손상된 파일 삭제
                    try:
                        os.remove(file_path)
                    except:
                        pass

    except Exception:
        # 정리 작업 실패 시 조용히 넘어감
        pass