import json
import time

from src.inference.base import InferenceProvider


class GeminiProvider(InferenceProvider):
    """Google Gemini inference provider (experimental)."""

    def __init__(self, client, model_name: str):
        self.client = client
        self.model_name = model_name

    def run_inference(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
        max_output_tokens: int = 16384,
    ) -> tuple[dict, dict]:
        # Gemini requires schema appended as text to the user prompt
        prompt_with_schema = (
            f"{user_prompt}\n\nFollow JSON schema."
            f"<JSONSchema>{json.dumps(json_schema)}</JSONSchema>"
        )

        timer_start = time.time()

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt_with_schema,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
            },
        )

        duration = time.time() - timer_start

        result = json.loads(response.text)

        usage = response.usage_metadata
        usage_dict = {
            "input_tokens": usage.prompt_token_count,
            "output_tokens": usage.candidates_token_count,
            "total_tokens": usage.total_token_count,
            "time_to_generate": f"{duration:.3f}",
        }

        return result, usage_dict
