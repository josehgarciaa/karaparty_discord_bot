import os
import json
import re
from pydantic import BaseModel
from openai import OpenAI
import instructor





class SmartBotService:
    def __init__(self, api_key: str):
        """
        Initializes the SmartBotService using OpenAI's instructor method and validates the API key.
        """
        if not api_key or not api_key.strip() or not api_key.startswith("sk-"):
            raise ValueError("API key is missing or does not correct.")
        os.environ["DEEPSEEK_API_KEY"] = api_key

        try:
            self.client = instructor.from_openai(
                OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
            )
            self.validate_login()
        except Exception as e:
            print(f"[ERROR] Failed to initialize SmartBotService: {str(e)}")
            raise

    def validate_login(self) -> None:
        """
        Validates that the client is properly authenticated.
        Raises an exception if the connection fails.
        """
        try:
            self.client.models.list()
        except Exception as e:
            raise ConnectionError(f"Failed to authenticate with DeepSeek API: {str(e)}")

    def validate_text(self, system_prompt: str, user_input: str, validation_format: BaseModel) -> dict:
        """
        Validates a text according to a system prompt and user input.
        Returns a structured response or an error message in case of failure.
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_model=validation_format
            )
            return response.model_dump()

        except Exception as e:
            print(f"[ERROR] Failed during text validation: {str(e)}")
            return {"error": str(e)}



