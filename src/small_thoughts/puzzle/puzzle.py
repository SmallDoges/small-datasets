import os

from datasets import load_dataset

from ..utils.decontaminate import decontaminate
from ..utils.deduplicate import deduplicate
from ..utils.reason import reason


def riddle_sense_map(x):
    question = x["question"]
    choices = x["choices"]
    full_question = question
    labels = choices["label"]
    texts = choices["text"]
    for label, text in zip(labels, texts):
        full_question += f"\n{label}: {text}"
    return {"question": full_question, "answer": x["answerKey"]}

def main(
    try_run: bool = False,
    base_url: str = "https://api.deepseek.com",
    model_name: str = "deepseek-reasoner",
    temperture: float = 0.0,
    max_tokens: int = 8192,
    system_prompt_type: str = "english",
    max_requests_per_minute: int = 1_000,
    max_tokens_per_minute: int = 1_000_000_000,
    cache_dir: str = "./cache",
    num_proc: int = 4,
    **kwargs,
):

    # load and process the riddle_sense dataset
    ds = load_dataset("INK-USC/riddle_sense", split="train", trust_remote_code=True, cache_dir=cache_dir)
    ds = ds.map(riddle_sense_map)
    ds = ds.shuffle(seed=42).take(2_000) 

    # rename columns for reason
    ds = ds.remove_columns(["answerKey", "choices"])
    ds = ds.add_column("domain", ["puzzle"] * len(ds))
    ds = ds.add_column("source", ["riddle_sense"] * len(ds))

    # if try_run, only take 2 samples
    if try_run:
        ds = ds.take(2)

    # clean the dataset
    ds = deduplicate(ds, num_proc=num_proc)
    ds = decontaminate(ds, cache_dir=cache_dir, num_proc=num_proc)

    # generate reasoning
    ds = reason(
        dataset=ds,
        base_url=base_url,
        model_name=model_name,
        temperture=temperture,
        max_tokens=max_tokens,
        system_prompt_type=system_prompt_type,
        max_requests_per_minute=max_requests_per_minute,
        max_tokens_per_minute=max_tokens_per_minute,
    )

    if try_run:
        print("======== PUZZLE REASONING DATASET CREATED ========")
        print(ds)
        print(ds[0])
        ("===================================================")

    # push to hub
    ds.push_to_hub(f"{os.environ.get('HF_ORG')}/small-thoughts-puzzle{'-try-run' if try_run else ''}")
