# app_mongo_async.py
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

class AppMongoDb:
    def __init__(self, config:Config):
        self.connection_string = config.MONGODB_CONNECTION_STRING
        self.mongodb_name = config.MONGODB_NAME
        self.client = AsyncIOMotorClient(self.connection_string)

    def get_collection(self, collection_name):
        db = self.client[self.mongodb_name]
        return db[collection_name]

    async def list_collections(self):
        db = self.client[self.mongodb_name]
        return await db.list_collection_names()
