# app_mq_mongodb_async.py
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import time
import json
from bson import ObjectId
from config import Config

class MongoDBMQ():
    def __init__(self, config: Config):
        self.config = config
        self.client = AsyncIOMotorClient(config.MONGODB_CONNECTION_STRING)
        self.db = self.client[config.MONGODB_NAME]

    async def publish(self, topic, message):

        request_id = message
        doc = {
            "status": "queued",
            "timestamp": time.time(),
            "request_id": request_id
        }
        await self.db[topic].insert_one(doc)
        return request_id

    async def get_latest_status(self, topic, request_id):
        doc = await self.db[topic].find_one({"request_id": request_id}, sort=[("timestamp", -1)])
        return doc["status"] if doc else None

    async def get(self, topic, timeout=5):
        deadline = time.time() + timeout
        while time.time() < deadline:
            doc = await self.db[topic].find_one_and_update(
                {"status": "queued"},
                {"$set": {
                    "status": "processing",
                    "processing_start": time.time()
                }},
                sort=[("timestamp", 1)]
            )
            if doc:
                return doc["message"]
            await asyncio.sleep(0.5)
        return None

    async def close(self):
        self.client.close()
