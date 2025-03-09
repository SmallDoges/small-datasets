import os
import sys
import logging
import subprocess

from argparse import ArgumentParser

from small_thoughts.science import science_main
from small_thoughts.puzzle import puzzle_main
from small_thoughts.maths import math_main
from small_thoughts.code import code_main
from small_thoughts.utils.mix import mix_subsets

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()
    parser.add_argument("--try_run", action="store_true", default=True)
    parser.add_argument("--base_url", type=str, default="https://api.deepseek.com")
    parser.add_argument("--model_name", type=str, default="deepseek-reasoner")
    parser.add_argument("--temperture", type=float, default=0.0)
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

    # generate datasets
    science_main(**args)
    puzzle_main(**args)
    math_main(**args)
    code_main(**args)

    # mix datasets
    mix_subsets(os.environ["HF_ORG"], ["science", "puzzle", "math", "code"], **args)


if __name__ == "__main__":
    main()