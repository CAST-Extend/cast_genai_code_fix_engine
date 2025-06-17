# app_logger_async.py
import traceback
from utils import get_timestamp

class AppLogger:
    def __init__(self, mongo_db):
        self.mongo_db = mongo_db

    async def log_error(self, function_name, exception):
        collection = self.mongo_db.get_collection("ExceptionLog")
        error_data = {
            "function": function_name,
            "error": str(exception),
            "trace": traceback.format_exc(),
            "timestamp": get_timestamp(),
        }
        await collection.insert_one(error_data)
        print(f"Error logged to MongoDB: {error_data}\n")
