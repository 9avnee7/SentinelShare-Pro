from fastapi import APIRouter, UploadFile, Form, File, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .. import models, database
from services.aws import upload_chunk_to_s3,delete_chunks_from_s3
from services.azure import upload_chunk_to_blob,delete_chunks_azure
from fastapi import Query
from jose import JWTError, jwt
import os
import json

from fastapi.responses import JSONResponse

router = APIRouter(tags=["Upload"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "defaultsecret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_chunk(
    request: Request,
    chunk: UploadFile = File(...),
    chunkIndex: int = Form(...),
    fileName: str = Form(...),
    iv: str = Form(...),
    fileHash: str = Form(...),
    totalChunks: int = Form(...),
    key: str = Form(...),
    db: Session = Depends(get_db),
):
    # Check malware status only for first chunk
    

    # Authenticate user
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Token missing")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=403, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Read file chunk as bytes (prevent file pointer issue)
    chunk_bytes = await chunk.read()

    # Upload encrypted chunk to Azure and AWS
    azure_url = upload_chunk_to_blob(fileHash, chunkIndex, chunk_bytes)
    aws_url = upload_chunk_to_s3(fileHash, chunkIndex, chunk_bytes)

    # Log upload attempt
    if chunkIndex == 0:
        client_ip = request.client.host
        print(f"Upload request from IP: {client_ip}, user: {user_email}")
        audit_log = models.AuditLog(
            action="upload",
            user_id=user.id,
            ip=client_ip
        )
        db.add(audit_log)
        db.commit()
        print("Audit log entry committed")

    # Parse IV from frontend
    try:
        iv_parsed = json.loads(iv)
        if not isinstance(iv_parsed, list):
            raise ValueError("Invalid IV format")
    except Exception:
        raise HTTPException(status_code=400, detail="IV must be a JSON array of bytes (12 elements)")

    # File record logic
    existing_file = db.query(models.FileUpload).filter_by(file_hash=fileHash, owner_id=user.id).first()

    if chunkIndex == 0:
        if existing_file:
            raise HTTPException(status_code=400, detail="File already uploaded")

        new_file = models.FileUpload(
            file_name=fileName,
            file_hash=fileHash,
            azure_url=azure_url,
            aws_url=aws_url,
            owner_id=user.id,
            chunk_count=totalChunks,
            ivs=json.dumps([iv_parsed]),
            encrypted_key=key,
        )
        db.add(new_file)

    else:
        if not existing_file:
            raise HTTPException(status_code=404, detail="File record not found")

        try:
            iv_list = json.loads(existing_file.ivs)
        except:
            iv_list = []

        iv_list.append(iv_parsed)
        existing_file.ivs = json.dumps(iv_list)
        db.add(existing_file)

        if chunkIndex == totalChunks - 1:
            if len(iv_list) != totalChunks:
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"IV count mismatch. Expected {totalChunks}, got {len(iv_list)}"
                )

    db.commit()
    return {"status": "chunk uploaded", "chunkIndex": chunkIndex}




@router.delete("/delete-file")
async def delete_file(
    request: Request,
    file_hash: str = Query(...),
    db: Session = Depends(get_db)
):
    # Decode user from JWT
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Token missing")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=403, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Find file owned by user
    file_record = db.query(models.FileUpload).filter_by(file_hash=file_hash).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete chunks from S3 and azure
    try:
        delete_chunks_from_s3(file_hash, file_record.chunk_count)
        delete_chunks_azure(file_hash, file_record.chunk_count)
         # Log download attempt
        client_ip = request.client.host
        print(f"delete request from IP: {client_ip}, user: {user_email}")
        audit_log = models.AuditLog(
            action="deleted",
            user_id=user.id,
            ip=client_ip
        )
        db.add(audit_log)
        db.commit()
        print("Audit log entry committed")  # DEBUG

    except Exception as e:
        print("Error deleting chunks from S3:", e)
        return JSONResponse(status_code=500, content={"error": "Failed to delete file chunks from S3 or Azure"})

    # Delete DB record
    db.delete(file_record)
    db.commit()

    return {"message": "File deleted successfully"}