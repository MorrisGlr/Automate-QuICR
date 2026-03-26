from abc import ABC, abstractmethod


class InferenceProvider(ABC):
    """Abstract base class for LLM inference providers."""

    @abstractmethod
    def run_inference(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict,
        max_output_tokens: int = 16384,
    ) -> tuple[dict, dict]:
        """Run a single inference call and return structured output with usage metadata.

        Args:
            system_prompt: The system prompt text.
            user_prompt: The user prompt text.
            json_schema: The JSON schema for structured output.
            max_output_tokens: Maximum output tokens.

        Returns:
            Tuple of (parsed_json_output, usage_dict) where usage_dict has keys:
            input_tokens, output_tokens, total_tokens, cached_input_tokens (optional),
            time_to_generate.
        """
        ...
