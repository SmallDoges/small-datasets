import re

from datasets import Dataset, concatenate_datasets, load_dataset

from ..utils.prompt import MIX_PROMPT


def process_map(example, system_prompt_type="english"):
    problem = re.sub(r'^(.*?)"(.*)"(.*?)$', r'\1\2\3', example["question"], 1, re.DOTALL)

    deepseek_solution = example["deepseek_solution"].replace("  \n", "\n").replace("  \n\n", "\n\n")
    solution_pattern = r"<\|begin_of_solution\|>(.*?)<\|end_of_solution\|>"
    solution = re.search(solution_pattern, deepseek_solution, re.DOTALL).group(1)

    messages = [
        {"role": "user", "content": problem},
        {"role": "assistant", "content": deepseek_solution},
    ]
    return {
        "system_prompt": MIX_PROMPT[system_prompt_type],
        "problem": problem,
        "solution": solution.replace("\n**Solution:**", "**Solution:**"),
        "messages": messages,
    }

def mix_subsets(org, subsets, try_run=False, num_proc=4, system_prompt_type="english", **kwargs):
    mix_ds = []
    for subset in subsets:
        ds = load_dataset(f"{org}/small-thoughts-{subset}{'-try-run' if try_run else ''}", split="train")
        colunm_names = ds.column_names
        ds = ds.map(process_map, num_proc=num_proc, remove_columns=colunm_names, fn_kwargs={"system_prompt_type": system_prompt_type})
        mix_ds.append(ds)
    ds: Dataset = concatenate_datasets(mix_ds)

    # push to hub
    ds.push_to_hub(f"{org}/small-thoughts-mix{'-try-run' if try_run else ''}")
