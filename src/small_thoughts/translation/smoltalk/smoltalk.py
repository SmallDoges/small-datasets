import os

from datasets import Dataset, load_dataset

from ...utils.translate import translate


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

    # load and process the dataset
    ds = load_dataset(
        "HuggingFaceTB/smoltalk",
        split="train",
        cache_dir=cache_dir,
    )

    # if try_run, only take 2 samples
    if try_run:
        ds = ds.take(2)

    # split dataset into user and assistant messages
    user_messages = []
    assistant_messages = []

    for sample in ds:
        messages = sample["messages"]
        if len(messages) >= 2:
            user_msg = next((msg for msg in messages if msg["role"] == "user"), None)
            assistant_msg = next((msg for msg in messages if msg["role"] == "assistant"), None)
            if user_msg and assistant_msg:
                user_messages.append({"content": user_msg["content"]})
                assistant_messages.append({"content": assistant_msg["content"]})

    # create a new dataset with user and assistant messages
    user_ds = Dataset.from_dict({"content": [msg["content"] for msg in user_messages]})
    assistant_ds = Dataset.from_dict({"content": [msg["content"] for msg in assistant_messages]})

    # translate user messages
    user_translated_ds = translate(
        dataset=user_ds,
        base_url=base_url,
        model_name=model_name,
        temperture=temperture,
        max_tokens=max_tokens,
        system_prompt_type=system_prompt_type,
        max_requests_per_minute=max_requests_per_minute,
        max_tokens_per_minute=max_tokens_per_minute,
    )
    
    # translate assistant messages
    assistant_translated_ds = translate(
        dataset=assistant_ds,
        base_url=base_url,
        model_name=model_name,
        temperture=temperture,
        max_tokens=max_tokens,
        system_prompt_type=system_prompt_type,
        max_requests_per_minute=max_requests_per_minute,
        max_tokens_per_minute=max_tokens_per_minute,
    )

    # create a new dataset with translated messages
    result_data = {"messages": []}
    for i in range(len(user_translated_ds)):
        message_pair = [
            {"content": user_translated_ds[i]["content"], "role": "user"},
            {"content": assistant_translated_ds[i]["content"], "role": "assistant"}
        ]
        result_data["messages"].append(message_pair)
    
    ds = Dataset.from_dict(result_data)

    # push to hub
    ds.push_to_hub(f"{os.environ.get('HF_ORG')}/smoltalk{'-try-run' if try_run else ''}")
