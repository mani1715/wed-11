from fastapi import APIRouter, HTTPException, status, Request, Depends
from models import AdminCreate, AdminLogin, AdminResponse, Admin, AdminRole
from auth_utils import get_password_hash, verify_password, create_access_token
from datetime import timedelta
import os

router = APIRouter()

@router.post("/register", response_model=dict)
async def register_admin(admin_data: AdminCreate, request: Request):
    db = request.app.state.db
    
    # Check if email already exists
    existing_admin = await db.admins.find_one({"email": admin_data.email})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin
    new_admin = Admin(
        email=admin_data.email,
        hashed_password=get_password_hash(admin_data.password),
        full_name=admin_data.full_name,
        role=admin_data.role
    )
    
    await db.admins.insert_one(new_admin.dict())
    
    # Create access token
    access_token = create_access_token(
        data={"sub": new_admin.id, "email": new_admin.email, "role": new_admin.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": AdminResponse(**new_admin.dict())
    }

@router.post("/login", response_model=dict)
async def login_admin(credentials: AdminLogin, request: Request):
    db = request.app.state.db
    
    # Find admin by email
    admin = await db.admins.find_one({"email": credentials.email})
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, admin["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": admin["id"], "email": admin["email"], "role": admin["role"]}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": AdminResponse(**admin)
    }

@router.get("/me", response_model=AdminResponse)
async def get_current_admin_info(request: Request):
    from dependencies import get_current_admin
    admin = await get_current_admin(request)
    return AdminResponse(**admin)