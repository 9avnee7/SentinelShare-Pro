from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from .. import models, database, auth, schemas
from typing import List
import logging
import os
from jose import JWTError, jwt
from ..utils.IpEncryption import AES256Encryptor
import base64
logging.basicConfig(level=logging.INFO)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "defaultsecret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
router = APIRouter(prefix="/admin", tags=["Admin"])


AES_256_KEY_B64 = os.getenv("AES_256_KEY_B64")
AES_256_KEY = base64.b64decode(AES_256_KEY_B64) 
encryptor = AES256Encryptor(AES_256_KEY)

# --- Dependencies ---
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    print(request.cookies)
    token = request.cookies.get("refresh_token")
    print(token)
    if not token:
        raise HTTPException(status_code=401, detail="Access token missing")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def superadmin_required(current_user: models.User = Depends(get_current_user)):
    logging.info(f"Current user role: {current_user.role}")
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Only superadmin can perform this action")
    return current_user
# --- Routes ---
@router.get("/users", response_model=List[schemas.UserOut])
def get_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(superadmin_required)):
    return db.query(models.User).all()



@router.patch("/update-role/{user_id}")
def update_user_role(user_id: int, role: str, db: Session = Depends(get_db), current_user: models.User = Depends(superadmin_required)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    user.role = role
    db.commit()
    return {"message": f"User {user.email}'s role updated to {role}"}



@router.get("/audit-logs")
async def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(superadmin_required)
):
    logs = db.query(models.AuditLog).all()
    if not logs:
        return []

    result = []
    for log in logs:
        try:
            print(f"Decrypting IP for log ID {log.id}")  # DEBUG
            decrypted_ip = encryptor.decrypt(log.ip)
        except Exception as e:
            print(f"Error decrypting IP for log ID {log.id}: {e}")
            decrypted_ip = "Decryption Failed"

        result.append({
            "id": log.id,
            "action": log.action,
            "user_id": log.user_id,
            "ip": decrypted_ip,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })

    return result
