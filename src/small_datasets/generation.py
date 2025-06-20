import os
import sys
import logging
import subprocess

from argparse import ArgumentParser

from small_datasets.reasoning.science import science_main
from small_datasets.reasoning.puzzle import puzzle_main
from small_datasets.reasoning.maths import math_main
from small_datasets.reasoning.code import code_main
from small_datasets.utils.mix import mix_subsets

from small_datasets.translation.smoltalk import smoltalk_main

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()
    parser.add_argument("--task", type=str, default="reasoning", choices=["reasoning", "translation"])
    parser.add_argument("--try_run", action="store_true", default=True)
    parser.add_argument("--base_url", type=str, default="https://api.deepseek.com")
    parser.add_argument("--model_name", type=str, default="deepseek-reasoner")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max_tokens", type=int, default=8192)
    parser.add_argument("--system_prompt_type", type=str, default="english")
    parser.add_argument("--max_requests_per_minute", type=int, default=1_000)
    parser.add_argument("--max_tokens_per_minute", type=int, default=1_000_000_000)
    parser.add_argument("--cache_dir", type=str, default="./cache")
    parser.add_argument("--num_proc", type=int, default=4)
    args = vars(parser.parse_args())

    # set logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # check if huggingface-cli is logged in
    is_logged_in = subprocess.run(["huggingface-cli", "whoami"], stdout=subprocess.PIPE).stdout.decode().strip()
    if is_logged_in == "Not logged in":
        subprocess.run(["huggingface-cli", "login"])

    # check if HF_ORG is set
    if "HF_ORG" not in os.environ:
        os.environ["HF_ORG"] = input("Please enter your Hugging Face organization id: ")

    # check if API_KEY is set
    if args["model_name"] in ["deepseek-reasoner", "deepseek-chat"]:
        if "DEEPSEEK_API_KEY" not in os.environ:
            os.environ["DEEPSEEK_API_KEY"] = input("Please enter your DeepSeek API Key: ")

    if args["task"] == "reasoning":
        # generate reasoning datasets
        science_main(**args)
        puzzle_main(**args)
        math_main(**args)
        code_main(**args)

        # mix reasoning datasets
        mix_subsets(os.environ["HF_ORG"], ["science", "puzzle", "math", "code"], **args)
    elif args["task"] == "translation":
        # generate translation datasets
        smoltalk_main(**args)



if __name__ == "__main__":
    main()