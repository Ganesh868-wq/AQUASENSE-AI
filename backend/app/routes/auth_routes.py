from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..database import SessionLocal
from ..models import User
from ..auth import hash_password, verify_password, create_access_token, token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    full_name = data.get("full_name", "").strip()
    phone = data.get("phone", "").strip()
    language = data.get("preferred_language", "en")

    if not email or "@" not in email:
        return jsonify({"error": "Valid email address is required"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400
    if not full_name:
        return jsonify({"error": "Full name is required"}), 400

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"error": "An account with this email already exists"}), 409

        hashed = hash_password(password)
        new_user = User(
            email=email,
            password_hash=hashed,
            full_name=full_name,
            phone=phone,
            preferred_language=language
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(new_user.id, new_user.email)
        return jsonify({
            "message": "User registered successfully",
            "token": token,
            "user": new_user.to_dict()
        }), 201
    finally:
        db.close()

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid email or password"}), 401

        token = create_access_token(user.id, user.email)
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": user.to_dict()
        }), 200
    finally:
        db.close()

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    new_password = data.get("new_password", "").strip()

    if not email or not new_password or len(new_password) < 6:
        return jsonify({"error": "Email and a new password (min 6 chars) are required"}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Prevent user enumeration in production; return standard confirmation
            return jsonify({"message": "If the email is registered, the password has been updated."}), 200

        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        return jsonify({"message": "Password reset successfully. You can now login with your new password."}), 200
    finally:
        db.close()

@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user_profile():
    return jsonify({"user": g.current_user.to_dict()}), 200

@auth_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    data = request.get_json() or {}
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == g.current_user.id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if "full_name" in data and data["full_name"].strip():
            user.full_name = data["full_name"].strip()
        if "phone" in data:
            user.phone = data["phone"].strip()
        if "preferred_language" in data and data["preferred_language"] in ("en", "te"):
            user.preferred_language = data["preferred_language"]

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200
    finally:
        db.close()
