from bespokelabs import curator

from ..utils.prompt import REASONING_PROMPT


class Reasoner(curator.LLM):
    return_completions_object = True

    def __init__(self, model_name, generation_params, backend_params, system_prompt=None):
        super().__init__(model_name=model_name, generation_params=generation_params, backend_params=backend_params, backend="openai")
        self.system_prompt = system_prompt

    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""
        question = input["question"]
        answer = input["answer"]
        prompt = f"{question}\nBelow is the correct answer to the above question:\n{answer}\nYou need to provide the correct reasoning and solution based on the question and answer."
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        return {
            "question": input["question"],
            "reasoning": response["choices"][0]["message"]["reasoning_content"],
            "deepseek_solution": response["choices"][0]["message"]["content"],
            "domain": input["domain"],
        }


def reason(dataset, base_url, model_name, temperature=0.0, max_tokens=8192, system_prompt_type="english", max_requests_per_minute=1_000, max_tokens_per_minute=1_000_000_000):
    reasoner = Reasoner(
        model_name=model_name,
        generation_params={"temp": temperature, "max_tokens": max_tokens},
        backend_params={"base_url": base_url, "max_requests_per_minute": max_requests_per_minute, "max_tokens_per_minute": max_tokens_per_minute, "max_retries": 1, "require_all_responses": False},
        system_prompt=REASONING_PROMPT[system_prompt_type],
    )
    return reasoner(dataset)
