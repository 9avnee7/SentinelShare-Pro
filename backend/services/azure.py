from azure.storage.blob import BlobServiceClient
import os
from io import BytesIO



connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "files"
blob_service_client = BlobServiceClient.from_connection_string(connect_str)




def upload_chunk_to_blob(file_id, chunk_index, chunk_data):
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"{file_id}/chunk_{chunk_index}")
    blob_client.upload_blob(chunk_data, overwrite=True)
    return f"azure://{CONTAINER_NAME}/{file_id}/chunk_{chunk_index}"


def download_chunks_azure(file_id, chunk_count):
    chunks = []
    for i in range(chunk_count):
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"{file_id}/chunk_{i}")
        try:
            blob_data = blob_client.download_blob().readall()
            chunks.append(blob_data)
            print("Downloaded chunk", i)
        except Exception as e:
            print(f"Error downloading chunk {i}: {e}")
            break  # Stop if no more chunks are found
    return chunks

def delete_chunks_azure(file_id, chunk_count):
    print(f"Deleting chunks for file ID: {file_id}")
    for i in range(chunk_count):  # Assuming a maximum of 100 chunks
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f"{file_id}/chunk_{i}")
        try:
            blob_client.delete_blob()
            print(f"Deleted chunk {i} from Azure")
        except Exception as e:
            print(f"Error deleting chunk {i}: {e}")
            break  # Stop if no more chunks are found
    print("Finished deleting chunks from Azure")
