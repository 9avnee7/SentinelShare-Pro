# utils/s3.py
import boto3
import os

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
print("AWS S3 client initialized")
print("access key", os.getenv("AWS_ACCESS_KEY_ID"))
print("secret key", os.getenv("AWS_SECRET_ACCESS_KEY"))
print("region", os.getenv("AWS_REGION"))
print("bucket name", os.getenv("AWS_S3_BUCKET_NAME"))

BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
import io

def upload_chunk_to_s3(file_hash: str, chunk_index: int, chunk_data: bytes) -> str:
    key = f"{file_hash}/chunk_{chunk_index}"
    s3_client.upload_fileobj(io.BytesIO(chunk_data), BUCKET_NAME, key)
    s3_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
    return s3_url

def download_chunks_from_s3(file_id, chunk_count):
    chunks = []
    for i in range(chunk_count):
        key = f"{file_id}/chunk_{i}"
        chunk_data = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
        chunks.append(chunk_data)
        print("Downloaded chunk", i)

    return chunks


def delete_chunks_from_s3(file_id,chunk_count):
    print(f"Deleting chunks for file ID: {file_id}")
    for i in range(chunk_count):  # Assuming a maximum of 100 chunks
        key = f"{file_id}/chunk_{i}"
        try:
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
            print(f"Deleted chunk {i} from S3")
        except Exception as e:
            print(f"Error deleting chunk {i}: {e}")
            break  # Stop if no more chunks are found
    print("Finished deleting chunks from S3")