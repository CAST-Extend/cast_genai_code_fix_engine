# main.py
import asyncio
import time
import urllib3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import Config
from app_logger import AppLogger
from app_mongo import AppMongoDb
from app_llm import AppLLM
from app_imaging import AppImaging
from app_code_fixer import AppCodeFixer
from app_mq import AppMessageQueue

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config = Config()
mongo_db = AppMongoDb(config)
app_logger = AppLogger(mongo_db)
ai_model = AppLLM(app_logger, config)
imaging = AppImaging(app_logger, config)
code_fixer = AppCodeFixer(app_logger, mongo_db, ai_model, imaging)
mq = AppMessageQueue(app_logger, config).open()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async def worker():
        print("[WORKER] Background queue processor started.")
        while True:
            try:
                doc = await mq.get("status_queue", timeout=5)
                if doc:
                    request_id = doc["request_id"]
                    retry_count = doc.get("retry_count", 0)

                    print(f"[WORKER] Processing: {request_id}")
                    await mq.db["audit_log"].insert_one({
                        "request_id": request_id,
                        "event": "processing",
                        "timestamp": time.time()
                    })

                    result = await code_fixer.process_request_logic(request_id)
                    status = "Completed" if result.get("status") == "success" else "Failed"

                    await mq.publish("status_queue", {
                        "request_id": request_id,
                        "status": status.lower(),
                        "retry_count": retry_count,
                        "response": result
                    })

                    await mq.db["audit_log"].insert_one({
                        "request_id": request_id,
                        "event": status.lower(),
                        "timestamp": time.time()
                    })
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                print(f"[WORKER ERROR] {e}")
                await asyncio.sleep(2)

    asyncio.create_task(worker())
    yield

app = FastAPI(lifespan=lifespan)
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
        await mq.publish("status_queue", {
            "request_id": request_id,
            "status": "queued",
            "retry_count": 0
        })
        await mq.db["audit_log"].insert_one({
            "request_id": request_id,
            "event": "queued",
            "timestamp": time.time()
        })
        return {
            "Request_Id": request_id,
            "status": "queued",
            "message": "Request has been enqueued for processing.",
            "code": 202
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        return {"status": "error", "message": str(e), "code": 500}

@app.get("/api-python/v1/RequestStatus/{request_id}")
async def get_request_status(request_id: str):
    try:
        latest_doc = await mq.db["status_queue"].find_one(
            {"request_id": request_id},
            sort=[("timestamp", -1)]
        )
        if not latest_doc:
            return {
                "Request_Id": request_id,
                "status": "not_found",
                "message": "No status found for this request ID",
                "code": 404
            }
        return {
            "Request_Id": request_id,
            "status": latest_doc.get("status", "unknown"),
            "retry_count": latest_doc.get("retry_count", 0),
            "last_updated": latest_doc.get("timestamp"),
            "response": latest_doc.get("response", {}),
            "code": 200
        }
    except Exception as e:
        print(f"[ERROR] Failed to get status for {request_id}: {e}")
        return {"status": "error", "message": str(e), "code": 500}

@app.get("/api-python/v1/ListPendingRequests")
async def list_pending_requests():
    try:
        pending = mq.db["status_queue"].find({"status": "queued"})
        results = []
        async for doc in pending:
            results.append({
                "request_id": doc["request_id"],
                "status": doc["status"],
                "timestamp": doc["timestamp"]
            })
        return {"status": 200, "pending_requests": results}
    except Exception as e:
        print(f"[ERROR] Listing pending requests: {e}")
        return {"status": "error", "message": str(e), "code": 500}
