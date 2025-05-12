<div align="center">

[![Discord](https://img.shields.io/badge/Discord-Small%20Doges-7289da?logo=discord&logoColor=white&color=7289da)](https://discord.gg/P2yYH95N)
[![huggingface](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Datasets-FFD21E)](https://huggingface.co/datasets/SmallDoge/SmallThoughts)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

*小数据, 大进步!*

---

*我们的目标是构建一个数据处理流水线来为语言模型训练的所有阶段提供高质量的数据集*

<h4>

简体中文 | [English](./README.md)

</h4>

</div>


# 新闻

* **[2025-5-12]** 🎉发布了 [SmallTalks](https://huggingface.co/datasets/SmallDoge/SmallTalks) 数据集.
* **[2025-3-8]** 🎉发布了 [SmallThoughts](https://huggingface.co/datasets/SmallDoge/SmallThoughts) 数据集.


# 关于

本项目旨在构建一个全面的**数据集处理流水线**，为语言模型训练的各个阶段提供高质量的数据集。这包括用于以下目的的数据集：

*   **预训练:** 大规模、多样化的文本语料库。
*   **指令微调:** 例如 `SmallTalks` 这样的数据集，用于使模型与用户指令对齐。
*   **推理微调:** 例如 `SmallThoughts` 这样的数据集，用于增强模型的推理能力。
*   **强化学习:** 用于通过奖励机制进一步优化模型行为的数据集。

我们的目标是通过为每个关键训练阶段提供精心策划的数据来支持开发功能更强大、更稳健的语言模型。


# 要求

- Python >= 3.10
- Linux 操作系统
- DeepSeek API Key
- Hugging Face API Key

> [!TIP]
> 如果您是 Windows 用户, 可以使用 WSL2 创建一个 Ubuntu 子系统, 以便在 Windows 上运行 Linux 命令.


# 安装

```bash
git clone https://github.com/SmallDoges/small-datasets.git
cd small-datasets
pip install .
```


# 使用

```bash
python src/small_datasets/generation.py \
--task reasoning \
--try_run \
--base_url https://api.deepseek.com \
--model_name deepseek-reasoner \
--temperture 0.0 \
--max_tokens 8192 \
--system_prompt_type chinese \
--max_requests_per_minute 1000 \
--max_tokens_per_minute 1000000000 \
--cache_dir ./cache \
--num_proc 4
```

然后跟随终端中的指引操作即可.

使用 `--try_run` 参数运行, 您可以在您的huggingface仓库下面得到以下数据集.

![example](./assets/example.png)

如果您需要完整的蒸馏数据集, 请移除 `--try_run` 参数.


# 相关项目

- [Openthoughts](https://github.com/open-thoughts/open-thoughts)
- [DeepSeek R1](https://huggingface.co/deepseek-ai/DeepSeek-R1)
- [Curator](https://github.com/bespokelabsai/curator)


# 引用

如果您使用此代码库, 或者认为我们的工作有价值, 请引用我们的仓库:

```bibtex
@misc{small-thoughts,
  author = {Jingze, Shi and Yifan, Wu and Bingheng, Wu and Yuyu, Luo},
  title = {Small Thoughts},
  year = {2025},
  month = {march},
  url = {https://github.com/SmallDoges/small-thoughts}
}
```
