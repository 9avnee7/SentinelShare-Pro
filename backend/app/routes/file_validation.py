from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
import boto3
import requests

app = FastAPI()

print("Starting file validation service...")
# Load environment variables
print(os.getenv("AWS_ACCESS_KEY_ID"))
print(os.getenv("AWS_SECRET_ACCESS_KEY"))
print(os.getenv("AWS_REGION"))
print(os.getenv("AWS_S3_BUCKET_NAME"))
print(os.getenv("LAMBDA_URL"))
# Read config from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("AWS_S3_BUCKET_NAME")
LAMBDA_URL = os.getenv("LAMBDA_URL")  # API Gateway endpoint or Lambda URL
AZURE_FUNCTION_URL = os.getenv("AZURE_FUNCTION_URL")  # HTTP trigger URL

router = APIRouter(tags=["VALIDATE"])

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

@router.post("/validate")
async def validate_file(file: UploadFile = File(...)):
    print ("validate file endpoint hit") 
    tmp_filename = None
    try:
        # Step 1: Save the uploaded file temporarily
        tmp_filename = f"/tmp/{uuid.uuid4()}_{file.filename}"
        with open(tmp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Step 2: Upload to S3 with prefix 'for_scan/'
        s3_key = f"for_scan/{os.path.basename(tmp_filename)}"
        print(f"Uploading {tmp_filename} to S3 bucket {S3_BUCKET} with key {s3_key}")
        s3_client.upload_file(tmp_filename, S3_BUCKET, s3_key)
        print(f"File uploaded to S3: s3://{S3_BUCKET}/{s3_key}")

        # Step 3: Trigger AWS Lambda via HTTP POST
        print(f"Triggering AWS Lambda function at {LAMBDA_URL}")
        lambda_payload = {"s3_key": s3_key, "bucket": S3_BUCKET}
        print(f"Payload for Lambda: {lambda_payload}")
        lambda_res = requests.post(LAMBDA_URL, json=lambda_payload, timeout=30)
        print(f"Lambda response status code: {lambda_res}")
        lambda_res.raise_for_status()
        lambda_response = lambda_res.json()
        print(f"Lambda response: {lambda_response}")

        # # Step 4: Trigger Azure Function via HTTP POST
        # azure_payload = {"s3_key": s3_key, "bucket": S3_BUCKET}
        # azure_res = requests.post(AZURE_FUNCTION_URL, json=azure_payload, timeout=30)
        # azure_res.raise_for_status()
        # azure_response = azure_res.json()

        # Step 5: Return combined result
        result = {
            "lambda_result": lambda_response,
            # "azure_result": azure_response
        }

        return JSONResponse(content=result)

    except requests.exceptions.RequestException as req_err:
        raise HTTPException(status_code=502, detail=f"Error calling cloud functions: {req_err}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temp file if exists
        if tmp_filename and os.path.exists(tmp_filename):
            os.remove(tmp_filename)
        print(f"Temporary file {tmp_filename} removed.")
