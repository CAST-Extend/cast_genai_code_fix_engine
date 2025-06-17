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
        latest_status = await mq.get_latest_status("status_queue", request_id)
        if latest_status:
            if latest_status in ["Queued", "Processing"]:
                return {
                    "Request_Id": request_id,
                    "status": latest_status.lower(),
                    "message": f"Request is already {latest_status}",
                    "code": 202
                }

        await mq.publish("request_queue", request_id)
        await mq.publish("status_queue", request_id)

        # Run the processing logic immediately (no background worker)
        result = await code_fixer.process_request_logic(request_id)
        status = "Completed" if result.get("status") == "success" else "Failed"

        await mq.publish("status_queue", {
            "request_id": request_id,
            "status": status,
            "response": result,
            "timestamp": time.time()
        })

        return result

    except Exception as e:
        print(e)
        return {"status": "error", "message": str(e), "code": 500}
