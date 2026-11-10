"""Shared pytest set-up.

Environment variables are set *before* any ``app`` module is imported so the
tests never touch the real ``database.db`` and never print SQL logs.
"""
import os
import tempfile
from pathlib import Path

_TEST_DIR = Path(tempfile.mkdtemp(prefix="myadvisor-tests-"))

# Env vars take priority over .env in pydantic-settings.
os.environ["DATABASE_URI"] = f"sqlite:///{(_TEST_DIR / 'unused.db').as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"
os.environ["ENV"] = "pytest"  # not dev (no SQL echo), not production (non-secure cookies)
os.environ["CONFIG_PASSWORD"] = ""
