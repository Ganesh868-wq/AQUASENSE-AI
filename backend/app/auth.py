import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from .config import Config
from .database import SessionLocal
from .models import User

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str) -> str:
    """Generate a signed JWT token."""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])

def token_required(f):
    """Decorator to enforce authentication on API endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header missing", "code": "UNAUTHORIZED"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format. Expected 'Bearer <token>'", "code": "INVALID_TOKEN_FORMAT"}), 401

        token = parts[1]
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                return jsonify({"error": "Invalid token subject", "code": "INVALID_TOKEN"}), 401
            
            # Fetch user from db
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    return jsonify({"error": "User no longer exists", "code": "USER_NOT_FOUND"}), 401
                # Attach to Flask's global context
                g.current_user = user
                g.db = db
                return f(*args, **kwargs)
            finally:
                db.close()
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again.", "code": "TOKEN_EXPIRED"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid or tampered token.", "code": "INVALID_TOKEN"}), 401
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}", "code": "AUTH_ERROR"}), 401

    return decorated
