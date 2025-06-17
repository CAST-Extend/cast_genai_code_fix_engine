import asyncio
import time
import json
import requests
import urllib3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from app_logger import AppLogger
from app_mongo import AppMongoDb
from app_llm import AppLLM
from app_imaging import AppImaging
from app_code_fixer import AppCodeFixer
from app_mq import AppMessageQueue

# Suppress the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = Config()
mongo_db = AppMongoDb(config)
app_logger = AppLogger(mongo_db)
ai_model = AppLLM(app_logger, config)
imaging = AppImaging(app_logger, config)
code_fixer = AppCodeFixer(app_logger, mongo_db, ai_model, imaging)
mq = AppMessageQueue(app_logger, config).open()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api-python/v1/")
async def home():
    return {"status": 200, "success": "Welcome to CAST Code Fix AI ENGINE."}

@app.get("/api-python/v1/CheckMongoDBConnection")
async def check_mongodb_connection():
    try:
        collections = await mongo_db.list_collections()
        return {"status": 200, "collections": collections}
    except Exception as e:
        return {"status": 500, "error": str(e)}

@app.get("/api-python/v1/ProcessRequest/{request_id}")
async def process_request(request_id: str):
    try:
        MAX_RETRIES = 3

        latest_doc = await mq.db["status_queue"].find_one(
            {"request_id": request_id},
            sort=[("timestamp", -1)]
        )
        latest_status = latest_doc["status"] if latest_doc else None
        retry_count = latest_doc.get("retry_count", 0) if latest_doc else 0

        if latest_status:
            status_lc = latest_status.lower()

            if status_lc in ["queued", "processing"]:
                return {
                    "Request_Id": request_id,
                    "status": status_lc,
                    "message": f"Request is already {latest_status}",
                    "code": 202
                }

            if status_lc == "completed":
                return {
                    "Request_Id": request_id,
                    "status": status_lc,
                    "message": "Request has already completed. No retry needed.",
                    "code": 200
                }

            if status_lc == "failed" and retry_count >= MAX_RETRIES:
                return {
                    "Request_Id": request_id,
                    "status": "failed",
                    "message": f"Retry limit reached ({retry_count}). Cannot retry further.",
                    "code": 429
                }

        # Retry allowed
        retry_count += 1
        print(f"[INFO] Retrying request_id: {request_id}, retry #{retry_count}")

        await mq.publish("request_queue", {"request_id": request_id, "retry_count": retry_count})
        await mq.publish("status_queue", {
            "request_id": request_id,
            "status": "queued",
            "retry_count": retry_count,
            "timestamp": time.time()
        })

        result = await code_fixer.process_request_logic(request_id)
        status = "Completed" if result.get("status") == "success" else "Failed"

        await mq.publish("status_queue", {
            "request_id": request_id,
            "status": status,
            "retry_count": retry_count,
            "response": result,
            "timestamp": time.time()
        })

        return result

    except Exception as e:
        print(f"[ERROR] {e}")
        return {"status": "error", "message": str(e), "code": 500}