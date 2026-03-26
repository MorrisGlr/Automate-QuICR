import json
import time

from src.inference.base import InferenceProvider


class OpenAIProvider(InferenceProvider):
    """OpenAI structured outputs inference provider."""

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
        timer_start = time.time()

        response = self.client.responses.create(
            model=self.model_name,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={"format": json_schema},
            max_output_tokens=max_output_tokens,
        )

        duration = time.time() - timer_start

        result = json.loads(response.output_text)

        usage = response.usage
        usage_dict = {
            "input_tokens": usage.input_tokens,
            "cached_input_tokens": usage.input_tokens_details.cached_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
            "time_to_generate": f"{duration:.3f}",
        }

        return result, usage_dict
