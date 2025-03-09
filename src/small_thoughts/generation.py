import sys
import logging

from argparse import ArgumentParser

from small_thoughts.science import science_main
from small_thoughts.puzzle import puzzle_main

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()
    parser.add_argument("--try_run", action="store_true", default=False)
    parser.add_argument("--base_url", type=str, default="https://api.deepseek.com/v1")
    parser.add_argument("--model_name", type=str, default="deepseek-reasoner")
    parser.add_argument("--temperture", type=float, default=0.0)
    parser.add_argument("--max_tokens", type=int, default=8192)
    parser.add_argument("--max_requests_per_minute", type=int, default=1_000)
    parser.add_argument("--max_tokens_per_minute", type=int, default=1_000_000_000)
    parser.add_argument("--cache_dir", type=str, default="./cache")
    parser.add_argument("--num_proc", type=int, default=2)


    # set logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    args = vars(parser.parse_args())
    # science_main(**args)
    puzzle_main(**args)

if __name__ == "__main__":
    main()