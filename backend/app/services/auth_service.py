"""Password hashing, JWT creation/verification, and the FastAPI
authentication dependencies every protected route depends on. See Phase 14
notes in docs/architecture.md.

Kept intentionally simple: one algorithm (HS256), one secret, access
tokens only (no refresh tokens), a boolean is_admin instead of a role
system. This is a real, secure implementation — just not an elaborate one.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET_KEY
from app.database import get_db
from app.models.user import User

# LOCAL DEVELOPMENT ONLY — a known, documented seed admin account (see
# README.md). Never use a hardcoded credential like this in anything other
# than a local, single-developer dev database.
# Note: the domain must NOT be one of the IANA/RFC 2606 reserved
# special-use TLDs (.local, .test, .example, .invalid, .localhost) —
# email-validator (used by Pydantic's EmailStr) rejects those outright,
# which would make this account permanently unable to log in.
DEV_ADMIN_EMAIL = "admin@dailytechlearn.dev"
DEV_ADMIN_PASSWORD = "devpassword123"

# FastAPI's standard way of documenting "this API expects a Bearer token"
# in its auto-generated docs (/docs) and extracting it from the
# Authorization header for us. tokenUrl just tells the docs UI where to
# get a token from — it doesn't affect how tokens are actually verified.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthError(Exception):
    """Raised for any authentication/registration failure. Carries the
    HTTP status code the router should respond with."""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def register_user(db: Session, email: str, password: str, username: str | None = None) -> User:
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email is not None:
        raise AuthError("An account with this email already exists", status_code=409)

    if username is not None:
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username is not None:
            raise AuthError("This username is already taken", status_code=409)

    user = User(email=email, username=username, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User:
    """identifier may be either the account's email or its username (Phase
    18.1) — resolved against both columns here so the router/frontend only
    ever deal with one generic field. Deliberately returns the SAME error
    for 'no such account', 'wrong password', and 'account disabled' —
    telling them apart would leak which emails/usernames are registered
    versus merely deactivated."""
    generic_error = AuthError("Incorrect email/username or password", status_code=401)

    user = (
        db.query(User)
        .filter((User.email == identifier) | (User.username == identifier))
        .first()
    )
    if user is None:
        raise generic_error
    if not verify_password(password, user.password_hash):
        raise generic_error
    if not user.is_active:
        raise generic_error

    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """The reusable dependency every protected route uses: reads the
    Authorization header (handled by oauth2_scheme), verifies the JWT's
    signature and expiry, loads the user it names, and rejects anything
    that doesn't check out. A route that depends on this NEVER trusts a
    user id supplied by the caller — only what the verified token says."""
    invalid_token_error = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise invalid_token_error

    user_id = payload.get("sub")
    if user_id is None:
        raise invalid_token_error

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise invalid_token_error

    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Same as get_current_user, plus requires is_admin — for the content
    pipeline's management endpoints. A logged-in normal user still fails
    this with a clear 403, not a confusing 401 (they ARE authenticated;
    they're just not allowed to do this particular thing — see Phase 14
    notes on authentication vs. authorization)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
