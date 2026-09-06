"""
auth/auth_service.py
─────────────────────
Core auth service — passwords, JWT, sessions, rate limiting, account lockout

Security design:
  - Passwords: bcrypt with cost factor 12
  - Access token: JWT HS256, 15-minute TTL, signed with SECRET_KEY
  - Refresh token: JWT HS256, 7-day TTL, stored hash in DB
  - Account lockout: 5 failed attempts → 15-minute lockout (exponential backoff)
  - Token rotation: every refresh issues a new refresh token (old revoked)
  - All events written to audit_logs table
"""
from __future__ import annotations

import hashlib
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt

# ── Config ─────────────────────────────────────────────────────────────────────
import os
SECRET_KEY         = os.environ.get("SECRET_KEY", "changeme-secret-key-in-production")
ALGORITHM          = "HS256"
ACCESS_TTL_MIN     = 15        # access token lifetime (minutes)
REFRESH_TTL_DAYS   = 7         # refresh token lifetime (days)
MAX_FAILED_LOGINS  = 5         # before lockout
LOCKOUT_MINUTES    = 15        # initial lockout duration
MIN_PASSWORD_LEN   = 8

# ── Password hashing ────────────────────────────────────────────────────────────
_pwd_ctx = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)

def validate_password_strength(password: str) -> list[str]:
    """Return list of violations. Empty = strong enough."""
    errors = []
    if len(password) < MIN_PASSWORD_LEN:
        errors.append(f"ต้องมีอย่างน้อย {MIN_PASSWORD_LEN} ตัวอักษร")
    if not any(c.isupper() for c in password):
        errors.append("ต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว")
    if not any(c.islower() for c in password):
        errors.append("ต้องมีตัวพิมพ์เล็กอย่างน้อย 1 ตัว")
    if not any(c.isdigit() for c in password):
        errors.append("ต้องมีตัวเลขอย่างน้อย 1 ตัว")
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        errors.append("ต้องมีอักขระพิเศษอย่างน้อย 1 ตัว (!@#$%^&*...)")
    return errors

# ── JWT ─────────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub":   user_id,
        "email": email,
        "role":  role,
        "type":  "access",
        "iat":   now,
        "exp":   now + timedelta(minutes=ACCESS_TTL_MIN),
        "jti":   secrets.token_hex(16),  # unique ID (allows revocation)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str, session_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub":        user_id,
        "session_id": session_id,
        "type":       "refresh",
        "iat":        now,
        "exp":        now + timedelta(days=REFRESH_TTL_DAYS),
        "jti":        secrets.token_hex(16),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return payload

def decode_refresh_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "refresh":
        raise JWTError("Not a refresh token")
    return payload

def hash_token(token: str) -> str:
    """SHA-256 hash of token for DB storage (never store raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()

# ── In-memory store (SQLite file for persistence without PostgreSQL) ────────────
# Uses SQLite as a drop-in when PostgreSQL is unavailable.
# All critical data is stored in quant_auth.db next to the project root.
_DB_PATH = Path(__file__).parent.parent / "quant_auth.db"

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def _init_sqlite():
    """Create tables if they don't exist (SQLite version)."""
    conn = _get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id               TEXT PRIMARY KEY,
        email            TEXT UNIQUE NOT NULL COLLATE NOCASE,
        username         TEXT UNIQUE NOT NULL COLLATE NOCASE,
        display_name     TEXT,
        hashed_password  TEXT NOT NULL,
        role             TEXT NOT NULL DEFAULT 'viewer',
        is_active        INTEGER NOT NULL DEFAULT 1,
        is_verified      INTEGER NOT NULL DEFAULT 0,
        failed_logins    INTEGER NOT NULL DEFAULT 0,
        locked_until     TEXT,
        last_login_at    TEXT,
        last_login_ip    TEXT,
        password_changed_at TEXT DEFAULT (datetime('now')),
        created_at       TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS user_sessions (
        id              TEXT PRIMARY KEY,
        user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        refresh_token   TEXT UNIQUE NOT NULL,
        device_info     TEXT,
        ip_address      TEXT,
        is_revoked      INTEGER NOT NULL DEFAULT 0,
        expires_at      TEXT NOT NULL,
        created_at      TEXT NOT NULL DEFAULT (datetime('now')),
        last_used_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS ix_sessions_token ON user_sessions(refresh_token);

    CREATE TABLE IF NOT EXISTS audit_logs (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    TEXT,
        event      TEXT NOT NULL,
        ip_address TEXT,
        user_agent TEXT,
        details    TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS ix_audit_user ON audit_logs(user_id);
    """)
    conn.commit()
    conn.close()

_init_sqlite()

# ── User CRUD ──────────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[dict]:
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_username(username: str) -> Optional[dict]:
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: str) -> Optional[dict]:
    conn = _get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(email: str, username: str, password: str,
                display_name: Optional[str] = None, role: str = "viewer") -> dict:
    uid = str(uuid.uuid4())
    conn = _get_db()
    conn.execute("""
        INSERT INTO users (id, email, username, display_name, hashed_password, role)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (uid, email.strip().lower(), username.strip().lower(),
          display_name or username, hash_password(password), role))
    conn.commit()
    user = dict(conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone())
    conn.close()
    return user

def update_last_login(user_id: str, ip: str):
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_db()
    conn.execute("""
        UPDATE users SET last_login_at = ?, last_login_ip = ?,
            failed_logins = 0, locked_until = NULL, updated_at = ?
        WHERE id = ?
    """, (now, ip, now, user_id))
    conn.commit()
    conn.close()

def increment_failed_login(user_id: str):
    conn = _get_db()
    row = conn.execute("SELECT failed_logins FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        conn.close()
        return
    fails = row["failed_logins"] + 1
    locked_until = None
    if fails >= MAX_FAILED_LOGINS:
        # Exponential: 15min * 2^(fails-5) but cap at 24h
        multiplier = 2 ** max(0, fails - MAX_FAILED_LOGINS)
        minutes    = min(LOCKOUT_MINUTES * multiplier, 1440)
        locked_until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    conn.execute(
        "UPDATE users SET failed_logins = ?, locked_until = ?, updated_at = ? WHERE id = ?",
        (fails, locked_until, datetime.now(timezone.utc).isoformat(), user_id)
    )
    conn.commit()
    conn.close()

def is_locked_out(user: dict) -> bool:
    if not user.get("locked_until"):
        return False
    try:
        locked_until = datetime.fromisoformat(user["locked_until"])
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < locked_until
    except Exception:
        return False

def change_password(user_id: str, new_password: str):
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_db()
    conn.execute("""
        UPDATE users SET hashed_password = ?, password_changed_at = ?,
            failed_logins = 0, locked_until = NULL, updated_at = ?
        WHERE id = ?
    """, (hash_password(new_password), now, now, user_id))
    # Revoke all sessions (force re-login after password change)
    conn.execute("UPDATE user_sessions SET is_revoked = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ── Sessions ───────────────────────────────────────────────────────────────────

def create_session(user_id: str, ip: str, device: str) -> tuple[str, str]:
    """Create session → return (access_token, refresh_token)."""
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")

    session_id  = str(uuid.uuid4())
    refresh_tok = create_refresh_token(user_id, session_id)
    tok_hash    = hash_token(refresh_tok)
    expires_at  = (datetime.now(timezone.utc) + timedelta(days=REFRESH_TTL_DAYS)).isoformat()

    conn = _get_db()
    conn.execute("""
        INSERT INTO user_sessions (id, user_id, refresh_token, device_info, ip_address, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, user_id, tok_hash, device[:200], ip, expires_at))
    conn.commit()
    conn.close()

    access_tok = create_access_token(user_id, user["email"], user["role"])
    return access_tok, refresh_tok

def rotate_session(old_refresh_token: str, ip: str, device: str) -> tuple[str, str]:
    """Exchange old refresh token for a new pair. Old session is revoked."""
    tok_hash = hash_token(old_refresh_token)
    conn     = _get_db()
    row      = conn.execute(
        "SELECT * FROM user_sessions WHERE refresh_token = ? AND is_revoked = 0",
        (tok_hash,)
    ).fetchone()

    if not row:
        conn.close()
        raise ValueError("Invalid or revoked refresh token")

    session = dict(row)
    # Check expiry
    try:
        exp = datetime.fromisoformat(session["expires_at"])
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            conn.execute("UPDATE user_sessions SET is_revoked = 1 WHERE id = ?", (session["id"],))
            conn.commit()
            conn.close()
            raise ValueError("Refresh token expired")
    except ValueError:
        raise

    # Revoke old session
    conn.execute("UPDATE user_sessions SET is_revoked = 1 WHERE id = ?", (session["id"],))
    conn.commit()
    conn.close()

    return create_session(session["user_id"], ip, device)

def revoke_session(refresh_token: str):
    tok_hash = hash_token(refresh_token)
    conn = _get_db()
    conn.execute("UPDATE user_sessions SET is_revoked = 1 WHERE refresh_token = ?", (tok_hash,))
    conn.commit()
    conn.close()

def revoke_all_sessions(user_id: str):
    conn = _get_db()
    conn.execute("UPDATE user_sessions SET is_revoked = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def list_sessions(user_id: str) -> list[dict]:
    conn = _get_db()
    rows = conn.execute("""
        SELECT id, device_info, ip_address, is_revoked, expires_at, created_at, last_used_at
        FROM user_sessions WHERE user_id = ? AND is_revoked = 0
        ORDER BY last_used_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Audit ──────────────────────────────────────────────────────────────────────

def audit(event: str, user_id: Optional[str] = None, ip: str = "",
          user_agent: str = "", details: Optional[dict] = None):
    import json
    conn = _get_db()
    conn.execute("""
        INSERT INTO audit_logs (user_id, event, ip_address, user_agent, details)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, event, ip, user_agent[:500],
          json.dumps(details or {}, ensure_ascii=False)))
    conn.commit()
    conn.close()

def get_audit_logs(user_id: Optional[str] = None, limit: int = 50) -> list[dict]:
    import json
    conn = _get_db()
    if user_id:
        rows = conn.execute("""
            SELECT * FROM audit_logs WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["details"] = json.loads(d["details"])
        except Exception:
            pass
        result.append(d)
    return result
