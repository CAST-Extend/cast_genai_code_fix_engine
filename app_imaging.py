# app_imaging.py
import requests
from app_logger import AppLogger
from config import Config

class AppImaging:
    def __init__(self, app_logger: AppLogger, config: Config):
        self.base_url = f"{config.IMAGING_URL}rest/tenants"
        self.params = {"api-key": config.IMAGING_API_KEY}
        self.app_logger = app_logger

    async def get_source_locations(self, tenant, application, object_id):
        object_url = f"{self.base_url}/{tenant}/applications/{application}/objects/{object_id}?select=source-locations"
        return requests.get(object_url, params=self.params, verify=False), object_url

    async def get_source(self, object_type, tenant, application, object_id, start_line, end_line):
        object_code_url = f"{self.base_url}/{tenant}/applications/{application}/files/{object_id}?start-line={start_line}&end-line={end_line}"
        response = requests.get(object_code_url, params=self.params, verify=False)
        if response.status_code == 200:
            return response.text
        else:
            self.app_logger.log_error("get_source", f"Failed to fetch {object_type} code from {object_code_url}. Status code: {response.status_code}")
            return ""

    async def get_file(self, object_type, tenant, application, file_id):
        object_code_url = f"{self.base_url}/{tenant}/applications/{application}/files/{file_id}"
        response = requests.get(object_code_url, params=self.params, verify=False)
        if response.status_code == 200:
            return response.text
        else:
            self.app_logger.log_error("get_file", f"Failed to fetch {object_type} file from {object_code_url}. Status code: {response.status_code}")
            return ""

    async def get_callees(self, tenant, application, object_id):
        url = f"{self.base_url}/{tenant}/applications/{application}/objects/{object_id}/callees"
        return requests.get(url, params=self.params, verify=False), url

    async def get_callers(self, tenant, application, object_id):
        url = f"{self.base_url}/{tenant}/applications/{application}/objects/{object_id}/callers?select=bookmarks"
        return requests.get(url, params=self.params, verify=False), url
