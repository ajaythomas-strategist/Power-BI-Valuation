"""
Session and Temporary File Cleanup Service.
Guarantees ephemeral storage: temporary folders created during evaluation
are cleaned up immediately when the session ends or on error.
"""
import os
import shutil
import tempfile
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class CleanupService:
    """Manages temporary disk workspaces per evaluation session."""

    _active_sessions: Dict[str, Path] = {}

    @classmethod
    def create_session_workspace(cls, session_id: Optional[str] = None) -> Tuple[str, Path]:
        sid = session_id or str(uuid.uuid4())
        base_temp = Path(tempfile.gettempdir()) / "powerbi_evaluator"
        base_temp.mkdir(parents=True, exist_ok=True)

        session_path = base_temp / sid
        session_path.mkdir(parents=True, exist_ok=True)

        cls._active_sessions[sid] = session_path
        logger.info(f"Created temporary evaluation workspace: {session_path}")
        return sid, session_path

    @classmethod
    def get_session_workspace(cls, session_id: str) -> Optional[Path]:
        path = cls._active_sessions.get(session_id)
        if path and path.exists():
            return path
        # Fallback check temp dir
        candidate = Path(tempfile.gettempdir()) / "powerbi_evaluator" / session_id
        if candidate.exists():
            return candidate
        return None

    @classmethod
    def cleanup_session(cls, session_id: str) -> bool:
        """Deletes all files in the session directory."""
        path = cls._active_sessions.pop(session_id, None)
        if not path:
            path = Path(tempfile.gettempdir()) / "powerbi_evaluator" / session_id

        if path and path.exists():
            try:
                shutil.rmtree(path, ignore_errors=True)
                logger.info(f"Cleaned up session temporary workspace: {path}")
                return True
            except Exception as e:
                logger.error(f"Error cleaning up session workspace {path}: {e}")
                return False
        return False

    @classmethod
    def cleanup_all(cls):
        """Emergency cleanup of all temporary workspaces."""
        base_temp = Path(tempfile.gettempdir()) / "powerbi_evaluator"
        if base_temp.exists():
            shutil.rmtree(base_temp, ignore_errors=True)
            logger.info("All temporary evaluator workspaces cleaned up.")
