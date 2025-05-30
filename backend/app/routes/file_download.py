from fastapi import APIRouter, Depends, HTTPException, Response, Query, Request
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from .. import models, database
from services.aws import download_chunks_from_s3
from services.azure import download_chunks_azure
import os
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ..utils.IpEncryption import AES256Encryptor
router = APIRouter(tags=["Download"])
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")


AES_256_KEY_B64 = os.getenv("AES_256_KEY_B64")
AES_256_KEY = base64.b64decode(AES_256_KEY_B64) 
encryptor = AES256Encryptor(AES_256_KEY)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/download")
async def download_file(
    request: Request,
    file_hash: str = Query(...),
    db: Session = Depends(get_db),
):
    print(f"\n=== Starting download for file_hash: {file_hash} ===")
    
    # TODO: Replace hardcoded token with real auth from cookies or headers
    token = request.cookies.get("access_token")

    try:
        print("Decoding JWT token...")  # DEBUG
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded payload: {payload}")  # DEBUG
        user_email = payload.get("sub")
        print(f"Extracted email from token: {user_email}")  # DEBUG

        user = db.query(models.User).filter(models.User.email == user_email).first()
        if not user:
            print("User not found in database")  # DEBUG
            raise HTTPException(status_code=403, detail="User not found")
        else:
            print(f"User found: {user.email} (ID: {user.id})")  # DEBUG

    except JWTError as e:
        print(f"JWT decoding failed: {e}")  # DEBUG
        raise HTTPException(status_code=403, detail="Invalid token")
    
    # Log download attempt
    client_ip = request.client.host
    encrypted_ip = encryptor.encrypt(client_ip)
    print(f"Download request from IP: {client_ip}, user: {user_email}")
    audit_log = models.AuditLog(
        action="download",
        user_id=user.id,
        ip=encrypted_ip
    )
    db.add(audit_log)
    db.commit()
    print("Audit log entry committed")  # DEBUG

    # Retrieve file metadata
    print(f"Fetching file metadata for hash: {file_hash}")  # DEBUG
    file = db.query(models.FileUpload).filter(models.FileUpload.file_hash == file_hash).first()
    if not file:
        print("File not found in DB")  # DEBUG
        raise HTTPException(status_code=404, detail="File not found")

    print(f"File found: {file.file_name}, chunk count: {file.chunk_count}")  # DEBUG
    print(f"IVs stored: {file.ivs} (type: {type(file.ivs)})")  # DEBUG

    # Download encrypted chunks with AWS primary, Azure fallback
    print("Attempting to download chunks from AWS S3...")  # DEBUG
    try:
        print(f"Downloaded {len(chunks)} chunks from S3")  # DEBUG
        chunks = download_chunks_from_s3(file_hash, file.chunk_count)
        print("chunk size:", len(chunks[0]))  # DEBUG
    except Exception as aws_error:
        print(f"AWS S3 download failed: {aws_error}")  # DEBUG
        print("Falling back to Azure Blob Storage...")  # DEBUG
        try:
            chunks = download_chunks_azure(file_hash, file.chunk_count)
            print(f"Downloaded {len(chunks)} chunks from Azure Blob Storage")  # DEBUG
            
        except Exception as azure_error:
            print(f"Azure fallback failed: {azure_error}")  # DEBUG
            raise HTTPException(status_code=500, detail="Failed to download file from both AWS and Azure")


    # Prepare decryption
    decrypted_data = bytearray()
    key_b64 = file.encrypted_key
    print(f"Encrypted key (base64): {key_b64}")  # DEBUG

    key_bytes = base64.b64decode(key_b64)
    print(f"Decoded key bytes length: {len(key_bytes)}")  # DEBUG

    ivs = file.ivs
    if isinstance(ivs, str):
        print("IVs is a string; attempting JSON parse")  # DEBUG
        try:
            ivs = json.loads(ivs)
            print(f"Parsed IVs: {ivs[:2]}... (total: {len(ivs)})")  # DEBUG
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed for IVs: {e}")  # DEBUG
            raise HTTPException(status_code=500, detail="Invalid IV format in database")
    
    if len(ivs) != file.chunk_count:
        print(f"IV count ({len(ivs)}) != chunk count ({file.chunk_count})")  # DEBUG
        raise HTTPException(status_code=500, detail="Mismatch between IV count and chunk count")

    aesgcm = AESGCM(key_bytes)
    print("AES-GCM initialized with key")  # DEBUG

    for i, encrypted_chunk in enumerate(chunks):
        print(f"\n--- Decrypting chunk {i} ---")
        print(f"Encrypted size: {len(encrypted_chunk)} bytes")  # DEBUG
        iv_array = ivs[i]

        if isinstance(iv_array, str):
            try:
                iv_array = json.loads(iv_array)
                print(f"Parsed IV[{i}] from JSON string")  # DEBUG
            except Exception:
                print(f"ERROR: IV[{i}] is not valid JSON: {iv_array}")  # DEBUG
                raise HTTPException(status_code=500, detail=f"IV at chunk {i} is not valid JSON")

        print(f"Final IV[{i}]: {iv_array} (type: {type(iv_array)})")  # DEBUG
        if not isinstance(iv_array, list) or len(iv_array) != 12:
            print(f"ERROR: IV[{i}] format incorrect: {iv_array}")  # DEBUG
            raise HTTPException(status_code=500, detail=f"Invalid IV format or length at chunk {i}")

        try:
            iv = bytes(iv_array)
            print(f"IV bytes: {iv.hex()}")  # DEBUG
            decrypted_chunk = aesgcm.decrypt(iv, encrypted_chunk, None)
            print(f"Decrypted chunk size: {len(decrypted_chunk)} bytes")  # DEBUG
            decrypted_data.extend(decrypted_chunk)
        except Exception as e:
            print(f"Decryption failed at chunk {i}: {e}")  # DEBUG
            raise HTTPException(status_code=500, detail=f"Decryption failed at chunk {i}")

    print("\n=== Download and decryption successful ===")
    print(f"Total decrypted file size: {len(decrypted_data)} bytes")

    return Response(
        content=bytes(decrypted_data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file.file_name}"}
    )




@router.get("/my-files")
async def get_user_files(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=403, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Role-based access
    if user.role in ("admin", "superadmin"):
        files = db.query(models.FileUpload).all()
    else:
        files = db.query(models.FileUpload).filter(models.FileUpload.owner_id == user.id).all()

    return [
        {
            "file_name": f.file_name,
            "file_hash": f.file_hash,
            "uploaded_at": f.created_at,
            "chunk_count": f.chunk_count
        } for f in files
    ]





@router.get("/audit-logs")
async def get_audit_logs(
    db: Session = Depends(get_db)
):
    logs = db.query(models.AuditLog).all()
    if not logs:
        return []

    result = []
    for log in logs:
        try:
            print(f"Decrypting IP for log ID {log.ip}")  # DEBUG
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
