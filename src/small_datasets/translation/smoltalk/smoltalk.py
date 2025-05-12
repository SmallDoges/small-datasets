import os
import concurrent.futures
from functools import partial

from datasets import Dataset, load_dataset

from ...utils.translate import translate


def extract_dataset_by_role(dataset):
    # messages list
    user_messages = []
    assistant_messages = []
    system_messages = []

    # message indices list
    user_message_indices = []
    assistant_message_indices = []
    system_message_indices = []

    # sample indices list
    user_sample_indices = []
    assistant_sample_indices = []
    system_sample_indices = []
    
    for i, sample in enumerate(dataset):
        messages = sample["messages"]
        for j, message in enumerate(messages):
            if message["role"] == "user":
                user_messages.append(message["content"])
                user_sample_indices.append(i)
                user_message_indices.append(j)
            elif message["role"] == "assistant":
                assistant_messages.append(message["content"])
                assistant_sample_indices.append(i)
                assistant_message_indices.append(j)
            elif message["role"] == "system":
                system_messages.append(message["content"])
                system_sample_indices.append(i)
                system_message_indices.append(j)
    
    if len(user_messages) > 0:
        user_dataset = Dataset.from_dict({
            "content": user_messages,
            "sample_indices": user_sample_indices,
            "message_indices": user_message_indices,
        })
    else:
        user_dataset = Dataset.from_dict({
            "content": [],
            "sample_indices": [],
            "message_indices": [],
        })
    
    if len(assistant_messages) > 0:
        assistant_dataset = Dataset.from_dict({
            "content": assistant_messages,
            "sample_indices": assistant_sample_indices,
            "message_indices": assistant_message_indices,
        })
    else:
        assistant_dataset = Dataset.from_dict({
            "content": [],
            "sample_indices": [],
            "message_indices": [],
        })
    
    if len(system_messages) > 0:
        system_dataset = Dataset.from_dict({
            "content": system_messages,
            "sample_indices": system_sample_indices,
            "message_indices": system_message_indices,
        })
    else:
        system_dataset = Dataset.from_dict({
            "content": [],
            "sample_indices": [],
            "message_indices": [],
        })

    return user_dataset, assistant_dataset, system_dataset


def combine_translated_datasets(user_ds, assistant_ds, system_ds, original_dataset, num_proc=32):
    # create a function to prepare the translation keys
    def prepare_translation_keys(example, idx):
        return {
            "key": (example["sample_indices"], example["message_indices"]),
            "translation": example.get("translated_content", None)
        }
    
    # process the dataset for each role
    def process_role_dataset(ds, role_name):
        if "translated_content" not in ds.column_names or len(ds) == 0:
            print(f"{role_name} messages: 0/{len(ds)} successfully translated")
            return {}
        
        # extract the keys and values in parallel
        keyed_ds = ds.map(
            prepare_translation_keys,
            with_indices=True,
            num_proc=num_proc
        )
        
        # convert to a dictionary
        translations = {}
        valid_count = 0
        for item in keyed_ds:
            if item["translation"] is not None:
                translations[(item["key"][0], item["key"][1])] = item["translation"]
                valid_count += 1
        
        print(f"{role_name} messages: {valid_count}/{len(ds)} successfully translated")
        return translations
    
    # process each role dataset
    user_translations = process_role_dataset(user_ds, "User")
    assistant_translations = process_role_dataset(assistant_ds, "Assistant")
    system_translations = process_role_dataset(system_ds, "System")
    
    # merge all translations
    translations = {**user_translations, **assistant_translations, **system_translations}
    
    # process the original dataset with the translations
    def process_batch(batch, indices):
        new_messages_list = []
        valid_flags = []
        
        for i, sample_idx in enumerate(indices):
            messages = batch["messages"][i]
            all_translated = True
            new_messages = []
            
            for msg_idx, msg in enumerate(messages):
                if (sample_idx, msg_idx) in translations:
                    new_messages.append({
                        "role": msg["role"],
                        "content": translations[(sample_idx, msg_idx)]
                    })
                else:
                    all_translated = False
                    break
            
            if all_translated and new_messages:
                new_messages_list.append(new_messages)
                valid_flags.append(True)
            else:
                new_messages_list.append(messages)
                valid_flags.append(False)
        
        return {
            "messages": new_messages_list,
            "valid": valid_flags
        }

    # process the original dataset in parallel
    processed_ds = original_dataset.map(
        process_batch,
        with_indices=True,
        batched=True,
        batch_size=100,
        num_proc=num_proc
    )

    # filter out the valid samples
    filtered_ds = processed_ds.filter(lambda x: x["valid"], num_proc=num_proc)
    filtered_ds = filtered_ds.remove_columns(["valid"])
    
    print(f"Final dataset: {len(filtered_ds)}/{len(original_dataset)} samples included after translation")
    
    return filtered_ds


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
    # ['all', 'smol-magpie-ultra', 'smol-constraints', 'smol-rewrite', 'smol-summarize', 'apigen-80k', 'everyday-conversations', 'explore-instruct-rewriting', 'longalign', 'metamathqa-50k', 'numina-cot-100k', 'openhermes-100k', 'self-oss-instruct', 'systemchats-30k']
    ds = load_dataset(
        "HuggingFaceTB/smoltalk",
        "all",
        split="train",
        cache_dir=cache_dir,
    )

    # if try_run, only take 2 samples
    if try_run:
        ds = ds.take(2)

    # split dataset into user and assistant messages with indices
    user_ds, assistant_ds, system_ds = extract_dataset_by_role(ds)

    # translate user and assistant messages while tracking indices
    results = {}
    translate_func = partial(
        translate,
        base_url=base_url,
        model_name=model_name,
        temperture=temperture,
        max_tokens=max_tokens,
        system_prompt_type=system_prompt_type,
        max_requests_per_minute=max_requests_per_minute,
        max_tokens_per_minute=max_tokens_per_minute,
    )
    translation_tasks = [
        ('user', user_ds),
        ('assistant', assistant_ds)
    ]
    if len(system_ds["content"]) > 0:
        translation_tasks.append(('system', system_ds))
    else:
        results['system'] = system_ds

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_role = {
            executor.submit(translate_func, dataset=ds): role 
            for role, ds in translation_tasks
        }
        for future in concurrent.futures.as_completed(future_to_role):
            role = future_to_role[future]
            results[role] = future.result()
            print(f"Completed translation for {role} messages")
    
    user_translated_ds = results['user']
    assistant_translated_ds = results['assistant']
    system_translated_ds = results['system']

    # create a new dataset with translated messages and their indices
    ds = combine_translated_datasets(
        user_translated_ds, 
        assistant_translated_ds, 
        system_translated_ds,
        ds,
        num_proc=num_proc
    ).select_columns(["messages"])

    # push to hub
    ds.push_to_hub(
        f"{os.environ.get('HF_ORG')}/smoltalk{'-try-run' if try_run else ''}"
        "all",
        split="train",
    )