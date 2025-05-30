from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from fastapi.responses import JSONResponse
import shutil, os, uuid, boto3, requests
from ..utils.virusTotal import check_file_hash_with_virustotal
from azure.storage.blob import BlobServiceClient
from ..schemas import VirusTotalRequest
import json
from fastapi import Query
from typing import Literal


router = APIRouter(tags=["VALIDATE"])

# ENV config
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME")
LAMBDA_URL = os.getenv("LAMBDA_URL")
AZURE_FUNCTION_URL = os.getenv("AZURE_FUNCTION_URL")




AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING_2")  # should be securely stored
CONTAINER_NAME = "check-for-scan"
AZURE_FUNCTION_URL = os.getenv("AZURE_FUNCTION_URL")  # the URL of your Azure Function

blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)


# AWS S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)



def delete_from_s3(key: str):
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
        print(f"Deleted from S3: {key}")
    except Exception as e:
        print(f"[Warning] S3 deletion failed: {e}")

def delete_from_blob(blob_name: str):
    try:
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
        blob_client.delete_blob()
        print(f"Deleted from Azure Blob: {blob_name}")
    except Exception as e:
        print(f"[Warning] Blob deletion failed: {e}")

def save_and_upload(file: UploadFile, prefix="for_scan/") -> str:
    tmp_filename = f"/tmp/{uuid.uuid4()}_{file.filename}"
    with open(tmp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    s3_key = f"{prefix}{os.path.basename(tmp_filename)}"
    s3_client.upload_file(tmp_filename, S3_BUCKET, s3_key)
    os.remove(tmp_filename)
    return s3_key

@router.post("/validate/yara")
async def validate_yara(file: UploadFile = File(...)):
    try:
        s3_key = save_and_upload(file, prefix="yara/")
        payload = {"s3_key": s3_key, "bucket": S3_BUCKET}
        res = requests.post(LAMBDA_URL, json=payload, timeout=30)
        res.raise_for_status()
        result = res.json()  
        print(f"YARA scan result: {result}")


    
        matches = result.get("yara", [])
        print(f"YARA matches: {matches}")

        # Delete file from S3 after scan
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        except Exception as delete_err:
            print(f"[Warning] Failed to delete from S3: {delete_err}")
            # print("failed")


        if matches: 
            raise HTTPException(
                status_code=422,
                detail=f"YARA scan failed: malware detected. Matched rules: {matches}"
            )

        return JSONResponse(content={"status": "success", "source": "aws_yara", "result": matches})

    except requests.exceptions.RequestException as err:
        raise HTTPException(status_code=502, detail=f"AWS Lambda error: {err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/clamav")
async def validate_clamav(file: UploadFile = File(...)):
    try:
        blob_name = f"{uuid.uuid4()}_{file.filename}"
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
        blob_data = await file.read()
        blob_client.upload_blob(blob_data, overwrite=True)

        payload = {"blob_name": blob_name}
        res = requests.post(AZURE_FUNCTION_URL, json=payload, timeout=30)
        res.raise_for_status()
        result = res.json()  
        print(f"ClamAV scan result: {result}")

        # Delete blob after scan
        try:
            blob_client.delete_blob()
        except Exception as delete_err:
            print(f"[Warning] Failed to delete blob: {delete_err}")

        # === UTILIZE SCAN RESULT ===
        if result.get("status") == "infected":
            raise HTTPException(
                status_code=422,
                detail=f"ClamAV scan failed: malware detected. Message: {result.get('message')}"
            )
        elif result.get("status") == "error":
            raise HTTPException(
                status_code=500,
                detail=f"ClamAV scan error: {result.get('message')}"
            )

        return JSONResponse(content={
            "status": "success",
            "source": "azure_clamav",
            "result": result,
            "blob_name": blob_name
        })

    except requests.exceptions.RequestException as err:
        raise HTTPException(status_code=502, detail=f"Azure Function error: {err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.post("/validate/virustotal")
async def validate_virustotal(payload: VirusTotalRequest):
    try:
        fileHash = payload.fileHash
        if not fileHash:
            raise HTTPException(status_code=400, detail="fileHash is required")

        result = await check_file_hash_with_virustotal(fileHash)
        print(f"VirusTotal scan result for {fileHash}: {result}")
        if not result:
            raise HTTPException(status_code=404, detail="File hash not found in VirusTotal")

        positives = result.get("positives") or 0
        if positives and int(positives) > 0:
            raise HTTPException(
                status_code=422,
                detail=f"VirusTotal scan failed: malware detected. Details: {result}"
            )

        return JSONResponse(content={"status": "success", "source": "virustotal", "result": result})

    except requests.exceptions.RequestException as err:
        raise HTTPException(status_code=502, detail=f"VirusTotal error: {err}")
