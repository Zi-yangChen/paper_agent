# 🤖 Paper Agent: AI-Powered Preprint Researcher

**Paper Agent** is a Python automation tool designed to help researchers stay on top of the latest developments in their field. It automatically scrapes the latest papers from **arXiv** and **bioRxiv**, filters them by keywords, and uses **Large Language Models** to analyze, score, and summarize them.

It generates a clean **CSV** database and a formatted **Markdown** report daily, making it easy to spot high-value papers without scrolling through hundreds of titles.

## ✨ Features

*   **Multi-Source Support**: Fetch papers from **arXiv** (CS, Physics, Math, etc.) or **bioRxiv** (Biology).
*   **AI Analysis**: Uses LLMs (e.g., Qwen, GPT, DeepSeek) to score papers and extract domain keywords.
*   **Smart Filtering**:
    *   Filter by **Categories** (e.g., `cs.CV`, `Neuroscience`).
    *   Filter by **Keywords** in Title/Abstract (e.g., "Diffusion", "Transformer").
    *   Filter by **Date** range.
*   **Dual Output**:
    *   📄 **CSV**: For data analysis and archiving.
    *   📝 **Markdown**: A beautiful summary report ready for Notion, Obsidian, or Slack.
*   **Multi-Language**: Supports generating summaries in **English** or **Chinese**.


## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Zi-yangChen/paper_agent.git
git clone 
cd paper_agent
```

### 2. Install Dependencies
Make sure you have Python 3.8+ installed.
```bash
pip install requests pandas openai arxiv
```

## ⚙️ Configuration

Open the script (e.g., `paper_agent.py`) in your text editor. You need to configure your LLM provider in the **Configuration Section** at the top of the file.

The script supports any **OpenAI-compatible API** (e.g., OpenAI, SiliconFlow, Alibaba DashScope, DeepSeek).

```python
API_KEY = "" 
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1" # I use aliyun here
MODEL_NAME = "qwen3-max"
```

## 🚀 Usage

Run the script from the command line. You must choose either `--arxiv` or `--biorxiv`.

```bash
python paper_agent.py [SOURCE] [OPTIONS]
```

### Parameters

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--arxiv` | Fetch papers from arXiv. | (Exclusive) |
| `--biorxiv` | Fetch papers from bioRxiv. | (Exclusive) |
| `--cats` | List of categories to search (e.g., `cs.CV`). | None |
| `--kw` | List of keywords to filter by (in Title/Abstract). | None (All) |
| `--limit` | Maximum number of papers to analyze. | 10 |
| `--days` | Number of past days to search. | 1 |
| `--lang` | Output language (`cn` for Chinese, `en` for English). | `cn` |
| `--prefix` | Custom prefix for the output filenames. | None |

## 💡 Examples

### 1. The "Deep Learning Daily"
Get the top 10 latest AI papers from arXiv (Computer Vision & Machine Learning) and summarize them in Chinese.
```bash
python paper_agent.py --arxiv --cats cs.CV cs.LG --limit 10
```

### 2. Specific Research Topic (Data Augmentation)
Find papers specifically about "Data Augmentation" within Computer Vision.
```bash
python paper_agent.py --arxiv --cats cs.CV --kw "data augmentation" --limit 5 --prefix Augmentation_Daily
```

### 3. Biology Research (English Report)
Search bioRxiv for "Neuroscience" papers mentioning "Transformer" from the last 3 days, with an English summary.
```bash
python paper_agent.py --biorxiv --cats Neuroscience --kw transformer --days 3 --lang en --limit 20
```

### 4. Generative AI Tracking
Track latest advancements in Diffusion Models.
```bash
python paper_agent.py --arxiv --cats cs.CV cs.AI --kw "diffusion model" "generative" --limit 15 --prefix GenAI_News
```

## 📂 Output

After running the script, two files will be generated in the current directory:

1.  **`[Prefix]_YYYY-MM-DD.csv`**: Contains raw data (Title, Abstract, Score, Keywords, Link, Summary).
2.  **`[Prefix]_YYYY-MM-DD.md`**: A formatted report highlighting the "Top Picks" (Highest scored papers).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

---
*Happy Researching!* 🎓
