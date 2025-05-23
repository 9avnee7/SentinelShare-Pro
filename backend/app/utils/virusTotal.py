import httpx
import os

VT_API_KEY = os.getenv("VT_API_KEY", "")  # Store in .env

async def check_file_hash_with_virustotal(file_hash: str) -> dict:
    url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
    headers = {
        "x-apikey": VT_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        result = response.json()
        malicious_votes = result["data"]["attributes"]["last_analysis_stats"]["malicious"]
        return {
            "found": True,
            "malicious_votes": malicious_votes,
            "raw": result
        }
    elif response.status_code == 404:
        return { "found": False }
    else:
        return { "error": response.text }
