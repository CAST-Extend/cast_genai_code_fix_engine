import json
import asyncio
import tiktoken
import httpx
from app_logger import AppLogger
from config import Config

class AppLLM:
    def __init__(self, app_logger: AppLogger, config: Config):
        self.model_name = config.MODEL_NAME
        self.model_version = config.MODEL_VERSION  # Unused
        self.model_url = config.MODEL_URL
        self.model_max_input_tokens = config.MODEL_MAX_INPUT_TOKENS
        self.model_max_output_tokens = config.MODEL_MAX_OUTPUT_TOKENS
        self.model_invocation_delay = config.MODEL_INVOCATION_DELAY_IN_SECONDS
        self.headers = {
            "Authorization": f"Bearer {config.MODEL_API_KEY}",
            "Content-Type": "application/json"
        }
        self.app_logger = app_logger
        self.first_prompt = True

        try:
            self.encoding = tiktoken.encoding_for_model(self.model_name)
            print(f"Using encoding for {self.model_name}")
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")
            print("Using fallback encoding 'cl100k_base'")

    async def count_tokens(self, prompt: str) -> int:
        try:
            return len(self.encoding.encode(prompt))
        except Exception as e:
            print(f"Error counting tokens: {e}")
            asyncio.create_task(self.app_logger.log_error("count_tokens", e))
            return 0

    async def ask_ai_model(self, prompt_content: str, json_resp: str, max_tokens: int, ObjectID=None):
        if self.first_prompt:
            self.first_prompt = False
        else:
            await asyncio.sleep(self.model_invocation_delay)

        MAX_RETRIES = 3
        tokens = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        messages = [{"role": "user", "content": prompt_content}]
        payload = {"model": self.model_name, "messages": messages, "temperature": 0}

        async with httpx.AsyncClient(timeout=3000.0) as client:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = await client.post(self.model_url, headers=self.headers, json=payload)
                    response.raise_for_status()

                    response_data = response.json()
                    ai_content = response_data["choices"][0]["message"]["content"]

                    try:
                        ai_response = json.loads(ai_content)

                        tokens = {
                            "prompt_tokens": response_data["usage"]["prompt_tokens"],
                            "completion_tokens": response_data["usage"]["completion_tokens"],
                            "total_tokens": response_data["usage"]["total_tokens"]
                        }

                        print(f"Processed ObjectID - {ObjectID}")
                        return ai_response, "success", tokens

                    except json.JSONDecodeError as e:
                        print(f"[Attempt {attempt}] Failed to decode AI response JSON: {e}")
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(self.model_invocation_delay)
                            prompt_content = (
                                f"The following text is not a valid JSON string:\n```{ai_content}```\n"
                                f"Error when parsing with json.loads():\n```{e}```\n"
                                f"It should match this format:\n```{json_resp}```\n"
                                f"Make sure your response is a valid JSON string. Respond only with the JSON."
                            )
                            messages = [{"role": "user", "content": prompt_content}]
                            payload = {"model": self.model_name, "messages": messages, "temperature": 0}
                        else:
                            return None, "Max retries reached! Failed to obtain valid JSON from AI.", tokens

                except httpx.HTTPError as e:
                    print(f"[Attempt {attempt}] HTTP error for ObjectID-{ObjectID}: {e}")
                    # await self.app_logger.log_error("ask_ai_model", e)
                    return None, f"HTTP Error: {e}. Please retry.", tokens
                except Exception as e:
                    print(f"[Attempt {attempt}] Unexpected error for ObjectID-{ObjectID}: {e}")
                    # await self.app_logger.log_error("ask_ai_model", e)
                    return None, f"Unexpected Error: {e}. Please retry.", tokens

        return None, "AI Model failed to fix the code. Please Resend the request...", tokens
