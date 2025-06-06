import os

from datasets import load_dataset

from ...utils.decontaminate import decontaminate
from ...utils.deduplicate import deduplicate
from ...utils.reason import reason


def filter_problems(example):
    for keyword in ["figure", "diagram", "jpeg", "png", "jpg", "svg", "answer:"]:
        if keyword in example["problem"].lower():
            return False
    if example["problem"].lower().startswith("a)") and "b)" in example["problem"].lower():  # These are multipart questions
        return False
    if example["solution"] is None:
        return False
    if example["solution"] == "":
        return False
    if len(example["solution"]) > 2048:
        return False
    if "\\boxed{}" in example["solution"].lower():  # This is QED, so these are proofs
        return False
    if "\\boxed{" not in example["solution"].lower():
        return False
    return True

def add_prompt_to_question(example):
    question = f"Return your final response within \\boxed{{}}. {example['question']}"
    return {"question": question}

def main(
    try_run: bool = False,
    base_url: str = "https://api.deepseek.com",
    model_name: str = "deepseek-reasoner",
    temperature: float = 0.0,
    max_tokens: int = 8192,
    system_prompt_type: str = "english",
    max_requests_per_minute: int = 1_000,
    max_tokens_per_minute: int = 1_000_000_000,
    cache_dir: str = "./cache",
    num_proc: int = 4,
    **kwargs,
):
    
    # load and process the math dataset
    ds = load_dataset("AI-MO/NuminaMath-CoT", split="train", cache_dir=cache_dir)
    ds = ds.filter(lambda x: x["source"] in ["amc_aime", "olympiads", "aops_forum", "math"])
    ds = ds.filter(filter_problems)

    # rename columns for reason
    ds = ds.rename_column("source", "source_subset")
    ds = ds.rename_column("problem", "question")
    ds = ds.rename_column("solution", "answer")
    ds = ds.add_column("domain", ["math"] * len(ds))
    ds = ds.add_column("source", ["numina_math"] * len(ds))

    # if try_run, only take 2 samples
    if try_run:
        ds = ds.take(2)

    # clean the dataset
    ds = deduplicate(ds, num_proc=num_proc)
    ds = decontaminate(ds, cache_dir=cache_dir, num_proc=num_proc)

    # generate reasoning
    ds = reason(
        dataset=ds.map(add_prompt_to_question),
        base_url=base_url,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt_type=system_prompt_type,
        max_requests_per_minute=max_requests_per_minute,
        max_tokens_per_minute=max_tokens_per_minute,
    )

    if try_run:
        print("======== MATH REASONING DATASET CREATED ========")
        print(ds)
        print(ds[0])
        print("===================================================")

    # push to hub
    ds.push_to_hub(f"{os.environ.get('HF_ORG')}/small-thoughts-math{'-try-run' if try_run else ''}")
