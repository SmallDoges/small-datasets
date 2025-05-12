import os
import hashlib
import json

from ..code.constants import COLUMNS 
from ..code.filters import filter_problem, filter_tests
from ...utils.decontaminate import decontaminate
from ...utils.deduplicate import deduplicate
from ...utils.reason import reason

from datasets import Dataset, load_dataset


def compute_problem_id(description: str) -> str:
    return hashlib.md5(description.encode()).hexdigest()

def cps_groupby_problem_id(dataset: Dataset) -> Dataset:
    df = dataset.to_pandas()
    df = (
        df.groupby("problem_id")
        .agg(
            {
                "test_cases": list,
                "code": list,
                "name": "first",
                "description": "first",
            }
        )
        .reset_index()
    )

    return Dataset.from_pandas(df)

def rename_cps(dataset: Dataset) -> Dataset:
    df = dataset.to_pandas()
    df = df.rename(
        columns={
            "description": "problem",
            "tests": "test_cases",
            "difficulty": "difficulty",
            "source": "source",
            "problem_id": "problem_id",
            "name": "name",
        }
    )

    return Dataset.from_pandas(df)

def cps_process(dataset: Dataset, num_proc: int = 1) -> Dataset:
    dataset = dataset.filter(lambda x: x["verdict"] == "OK", num_proc=num_proc)

    dataset = dataset.map(
        lambda x: {
            "sample-tests": f"Sample Input\n{''.join(x['demo-input'])}\nSample Output\n{''.join(x['demo-output'])}",
        },
        num_proc=num_proc,
    )

    dataset = dataset.map(
        lambda x: {
            "description": x["problem-description"] + "\n" + x["input-specification"] + "\n" + x["output-specification"] + "\n" + x["sample-tests"],
            "problem_id": compute_problem_id(
                x["problem-description"] + "\n" + x["input-specification"] + "\n" + x["output-specification"] + "\n" + x["sample-tests"]
            ),
        },
        num_proc=num_proc,
    )

    dataset = cps_groupby_problem_id(dataset)

    dataset = dataset.filter(lambda x: filter_problem(x["description"]), num_proc=num_proc)

    dataset = dataset.map(
        lambda x: {
            "source": "CODEFORCES",
            "difficulty": "UNKNOWN",
            "test_cases": {
                "inputs": [i["input"] for i in x["test_cases"][0]],
                "outputs": [i["output"] for i in x["test_cases"][0]],
            },
            "language": "PYTHON3",
        },
        num_proc=num_proc,
    )

    dataset = dataset.filter(lambda x: filter_tests(x["test_cases"]), num_proc=num_proc)

    dataset = rename_cps(dataset)

    dataset = dataset.map(
        lambda x: {
            "solutions": x["code"],
            "num_solutions": len(x["code"]),
            "starter_code": "",
        },
        num_proc=num_proc,
    )

    dataset = dataset.select_columns(COLUMNS)

    # dump tests
    dataset = dataset.map(
        lambda x: {"test_cases": json.dumps(x["test_cases"])},
        num_proc=num_proc,
    )

    return dataset

def format_code_prompt(example):
    formatted_prompt = ""

    data = json.loads(example["test_cases"])
    if not data.get("fn_name"):
        formatted_prompt += "Generate an executable Python function generated from the given prompt. The function should take stdin as input and print the output. Simply call the function after the definition."  # noqa
    else:
        formatted_prompt += (
            "Generate an executable Python function generated from the given prompt. Return the function body without invoking it at the final solution."  # noqa
        )

    formatted_prompt += example["question"]
    if example["starter_code"] is not None:
        data = example["starter_code"]
        data = "\n" + data
        formatted_prompt += data
    return {"question": formatted_prompt}

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
    
    # load and process the code datasets
    ds = load_dataset("MatrixStudio/Codeforces-Python-Submissions", split="train", cache_dir=cache_dir)
    ds = cps_process(ds, num_proc=num_proc)

    # rename columns for reason
    ds = ds.map(lambda x: {"language": [x["language"]] if isinstance(x["language"], str) else x["language"]})
    ds = ds.rename_column("problem", "question")
    ds = ds.map(lambda x: {"answer": x["solutions"][0]})
    ds = ds.add_column("domain", ["code"] * len(ds))

    # if try_run, only take 2 samples
    if try_run:
        ds = ds.take(2)

    # clean the dataset
    ds = deduplicate(ds, num_proc=num_proc)
    ds = decontaminate(ds, cache_dir=cache_dir, num_proc=num_proc)

    # generate reasoning
    ds = reason(
        dataset=ds.map(format_code_prompt),
        base_url=base_url,
        model_name=model_name,
        temperture=temperture,
        max_tokens=max_tokens,
        system_prompt_type=system_prompt_type,
        max_requests_per_minute=max_requests_per_minute,
        max_tokens_per_minute=max_tokens_per_minute,
    )

    if try_run:
        print("======== CODE REASONING DATASET CREATED ========")
        print(ds)
        print(ds[0])
        print("===================================================")

    # push to hub
    ds.push_to_hub(f"{os.environ.get('HF_ORG')}/small-thoughts-code{'-try-run' if try_run else ''}")
