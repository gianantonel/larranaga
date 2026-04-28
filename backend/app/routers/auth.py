from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..security import verify_password, create_access_token, decode_token, get_password_hash
from ..utils.resend import notify_admin_of_new_user
import os

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    user = db.query(models.User).filter(models.User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role not in [models.UserRole.super_admin, models.UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requieren permisos de administrador")
    return current_user


def require_super_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != models.UserRole.super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requieren permisos de Super-Admin")
    return current_user


@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login con email + password. Devuelve JWT."""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    user_out = schemas.UserOut.model_validate(user)
    return schemas.Token(access_token=access_token, token_type="bearer", user=user_out)


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Devuelve el usuario actualmente autenticado."""
    return current_user


@router.post("/register", response_model=schemas.Token)
def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user (public endpoint)."""
    # Check if user already exists
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )
    
    # Generate avatar initials
    initials = ((user_data.name or " ")[0] + (user_data.last_name or " ")[0]).strip().upper() or "??"
    
    # Create new user with pending status and colaborador role by default
    new_user = models.User(
        name=user_data.name,
        last_name=user_data.last_name,
        cuit=user_data.cuit,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=models.UserRole.colaborador,  # Default role for public registration
        status=models.UserStatus.pending,  # Pending approval
        is_active=True,
        avatar_initials=initials[:3],
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Notify super admins about new user registration
    try:
        # Get super admin emails from database
        super_admins = db.query(models.User).filter(
            models.User.role == models.UserRole.super_admin,
            models.User.is_active == True
        ).all()
        admin_emails = [admin.email for admin in super_admins]
        
        # Fallback to default super-admin emails if none found in DB
        if not admin_emails:
            admin_emails = [
                "optimizar.ai@gmail.com",
                "gianantonel@gmail.com", 
                "rodriguezfederico765@gmail.com",
                "gerogambuli2002@gmail.com"
            ]
        
        notify_admin_of_new_user(
            user_data={
                "name": new_user.name,
                "last_name": new_user.last_name,
                "cuit": new_user.cuit,
                "email": new_user.email
            },
            admin_emails=admin_emails
        )
    except Exception as e:
        # Log error but don't fail the user creation
        print(f"Failed to send admin notification: {e}")
    
    # Create access token for the newly registered user (optional)
    # But since they are pending, maybe we don't want to log them in yet
    # For now, we'll return a token but the frontend should check status
    access_token = create_access_token({"sub": str(new_user.id), "role": new_user.role})
    user_out = schemas.UserOut.model_validate(new_user)
    return schemas.Token(access_token=access_token, token_type="bearer", user=user_out)