from bespokelabs import curator

from ..utils.prompt import TRANSLATION_PROMPT


class Translator(curator.LLM):
    return_completions_object = True

    def __init__(self, model_name, generation_params, backend_params, system_prompt=None):
        super().__init__(model_name=model_name, generation_params=generation_params, backend_params=backend_params, backend="openai")
        self.system_prompt = system_prompt

    def prompt(self, input):
        """Create a prompt for the LLM to translate about the content."""
        content = input["content"]
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": content},
        ]

    def parse(self, input, response):
        """Parse the LLM response to extract translated content."""
        return {
            "content": input["content"],
            "translated_content": response["choices"][0]["message"]["content"],
            "sample_indices": input["sample_indices"],
            "message_indices": input["message_indices"],
        }


def translate(dataset, base_url, model_name, temperature=0.0, max_tokens=8192, system_prompt_type="english", max_requests_per_minute=1_000, max_tokens_per_minute=1_000_000_000):
    reasoner = Translator(
        model_name=model_name,
        generation_params={"temp": temperature, "max_tokens": max_tokens},
        backend_params={"base_url": base_url, "max_requests_per_minute": max_requests_per_minute, "max_tokens_per_minute": max_tokens_per_minute, "max_retries": 10, "require_all_responses": False},
        system_prompt=TRANSLATION_PROMPT[system_prompt_type],
    )
    return reasoner(dataset)
