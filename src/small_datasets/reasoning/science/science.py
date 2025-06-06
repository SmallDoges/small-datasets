import os

from datasets import Dataset, load_dataset, concatenate_datasets
import pandas as pd

from ...utils.decontaminate import decontaminate
from ...utils.deduplicate import deduplicate
from ...utils.reason import reason


def subsample(dataset, num_samples_per_subtopic):
    df = dataset.to_pandas()

    sampled_dfs = []
    for subtopic in df["sub_topic"].unique():
        subtopic_sample = df[df["sub_topic"] == subtopic].sample(n=num_samples_per_subtopic, random_state=42)
        sampled_dfs.append(subtopic_sample)
    result_df = pd.concat(sampled_dfs)

    return Dataset.from_pandas(result_df)

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

    # load and process the three science datasets
    domains = {
        "biology": None,
        "chemistry": None,
        "physics": None,
    }
    for domain in domains:
        ds = load_dataset(f"mlfoundations-dev/camel-ai-{domain}", split="train", cache_dir=cache_dir)
        ds = subsample(ds, 2)
        ds = ds.add_column("domain", [domain] * len(ds))
        domains[domain] = ds
    ds: Dataset = concatenate_datasets(domains.values())

    # rename columns for reason
    ds = ds.rename_column("message_1", "question")
    ds = ds.rename_column("message_2", "answer")
    ds = ds.rename_column("topic;", "topic")
    ds = ds.select_columns(["question", "answer", "domain", "topic", "sub_topic"])
    ds = ds.add_column("source", ["camel"] * len(ds))

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
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt_type=system_prompt_type,
        max_requests_per_minute=max_requests_per_minute,
        max_tokens_per_minute=max_tokens_per_minute,
    )

    if try_run:
        print("======== SCIENCE REASONING DATASET CREATED ========")
        print(ds)
        print(ds[0])
        print("===================================================")

    # push to hub
    ds.push_to_hub(f"{os.environ.get('HF_ORG')}/small-thoughts-science{'-try-run' if try_run else ''}")
