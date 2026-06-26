"""
Auth API — registration, login, and user profile endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from database.db import get_db
from services.auth_service import hash_password, verify_password, create_access_token
from services.auth_middleware import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(req: RegisterRequest):
    """Register a new user account."""
    if not req.name or len(req.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    if not req.password or len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    import re
    if not re.search(r"[A-Za-z]", req.password) or not re.search(r"[0-9]", req.password) or not re.search(r"[^A-Za-z0-9]", req.password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one letter, one number, and one special character"
        )

    db = get_db()

    # Check if email already exists
    existing = await db.users.find_one({"email": req.email.lower().strip()})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create user
    user_doc = {
        "name": req.name.strip(),
        "email": req.email.lower().strip(),
        "password_hash": hash_password(req.password),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Generate token
    token = create_access_token({"sub": user_id})

    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": user_doc["name"],
            "email": user_doc["email"],
        },
    }


@router.post("/login")
async def login(req: LoginRequest):
    """Authenticate and return a JWT token."""
    db = get_db()
    user = await db.users.find_one({"email": req.email.lower().strip()})

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token({"sub": user_id})

    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
        },
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return current_user
