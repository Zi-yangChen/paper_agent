import argparse
import requests
import arxiv
import pandas as pd
from openai import OpenAI
import datetime
import json
import time
import sys
import os

API_KEY = "" 
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1" # I use aliyun here
MODEL_NAME = "qwen3-max"
HARD_LIMIT_MAX = 100
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ================= PROMPT TEMPLATES =================
PROMPTS = {
    "cn": {
        "system": "你是一个专业的科研助手。请分析论文标题和摘要，输出纯JSON格式。",
        "user": """
        请分析以下论文：
        标题: {title}
        摘要: {abstract}

        请输出且仅输出一个合法的 JSON 对象，包含以下字段：
        1. "keywords": [list of strings], 5-10个关键领域标签，粒度从粗到细。
        2. "score": int, 1-10分，评价其学术价值或创新性，请像评审专家一样严谨分析每篇论文的质量，避免分数虚高，掩盖真正有价值的成果。
        3. "summary": string, 中文一句话概括核心贡献，50字左右。
        4. "reason": string, 中文简短解释打分理由，100字左右。

        JSON 示例:
        {{
            "keywords": ["Deep Learning", "Genome"],
            "score": 9,
            "summary": "提出一个新的基因组语言模型EVO2，在多个任务上超越现有模型，并能够从头生成真核生物基因组。",
            "reason": "基于StripedHyena 2 架构开发基因组语言模型EVO2，在9.3TB 基因组数据训练，最大参数量达到40B。在多个任务中表现超越现有模型，同时拥有强大的生成能力。"
        }}
        """
    },
    "en": {
        "system": "You are a professional research assistant. Analyze the paper and output strictly in JSON format.",
        "user": """
        Please analyze the following paper:
        Title: {title}
        Abstract: {abstract}

        Output ONLY a valid JSON object with the following fields:
        1. "keywords": [list of strings], 3-5 domain tags.
        2. "score": int, 1-10, rating academic value or innovation.
        3. "summary": string, one-sentence summary in English.
        4. "reason": string, short explanation for the score in English.

        JSON Example:
        {{
            "keywords": ["Deep Learning", "NLP"],
            "score": 8,
            "summary": "Proposes a novel attention mechanism.",
            "reason": "Solves long-sequence dependency effectively."
        }}
        """
    }
}

def check_keywords(text, keywords):
    """ Check if any of the keywords exist in the text (case-insensitive). """
    if not keywords:
        return True 
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False

def get_arxiv_papers(categories, max_results, days_back, keywords=None):
    """ Fetch papers from Arxiv based on categories, date, and keywords. """
    print(f"[Arxiv] Searching {categories} | Keywords: {keywords} | Target Limit: {max_results}...")
    
    query_str = " OR ".join([f"cat:{cat}" for cat in categories]) if categories else "cat:cs.AI"
    search_limit = max_results * 10 if keywords else max_results * 2
    
    search = arxiv.Search(
        query=query_str,
        max_results=search_limit, 
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    results = []
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_back)
    
    count = 0
    for result in search.results():
        if result.published < cutoff_date:
            continue
            
        text_content = f"{result.title} {result.summary}"
        if not check_keywords(text_content, keywords):
            continue

        results.append({
            "source": "arXiv",
            "title": result.title,
            "abstract": result.summary.replace("\n", " "),
            "url": result.entry_id,
            "date": result.published.strftime("%Y-%m-%d"),
            "authors": ", ".join([a.name for a in result.authors[:3]])
        })
        count += 1
        if count >= max_results:
            break
            
    return results

def get_biorxiv_papers(categories, max_results, days_back, keywords=None):
    """ Fetch papers from BioRxiv with filtering. """
    print(f"[BioRxiv] Fetching recent {days_back} days | Keywords: {keywords}...")
    
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days_back)
    
    url = f"https://api.biorxiv.org/details/biorxiv/{start_date}/{end_date}/0/json"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        papers = []
        if 'collection' in data:
            for item in data['collection']:
                if categories:
                    if item['category'].lower() not in [c.lower() for c in categories]:
                        continue
                
                text_content = f"{item['title']} {item['abstract']}"
                if not check_keywords(text_content, keywords):
                    continue

                papers.append({
                    "source": "bioRxiv",
                    "title": item['title'],
                    "abstract": item['abstract'],
                    "url": f"https://www.biorxiv.org/content/{item['doi']}",
                    "date": item['date'],
                    "authors": item['authors'],
                    "category": item['category']
                })
                
                if len(papers) >= max_results:
                    break
        return papers
    except Exception as e:
        print(f"Error fetching BioRxiv: {e}")
        return []

def analyze_paper(paper, lang='cn'):
    """ Call LLM to analyze paper """
    template = PROMPTS[lang]
    prompt_content = template["user"].format(
        title=paper['title'], 
        abstract=paper['abstract']
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": template["system"]},
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.2,
        )
        content = completion.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:]
        if content.endswith("```"): content = content[:-3]
        return json.loads(content)
    except Exception as e:
        print(f"  [AI Error] {e}")
        return {}

def generate_markdown_report(df, filename):
    """ Generate Markdown Summary """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Daily Paper Summary ({datetime.date.today()})\n\n")
        
        f.write("## Top Picks\n")
        top_papers = df.head(3)
        for _, row in top_papers.iterrows():
            f.write(f"### [{row['Score']}] {row['Title']}\n")
            f.write(f"- **Summary**: {row['Summary']}\n")
            f.write(f"- **Reason**: {row['Reason']}\n")
            f.write(f"- **Link**: [Read Paper]({row['Link']})\n\n")
            
        f.write("---\n## All Papers\n")
        f.write("| Score | Title | Keywords | Link |\n")
        f.write("|---|---|---|---|\n")
        for _, row in df.iterrows():
            f.write(f"| {row['Score']} | {row['Title']} | {row['Keywords']} | [Link]({row['Link']}) |\n")
    print(f"Markdown report generated: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Daily Preprint Paper Agent")
    
    # Source
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--arxiv', action='store_true', help="Fetch from Arxiv")
    group.add_argument('--biorxiv', action='store_true', help="Fetch from BioRxiv")
    
    # Settings
    parser.add_argument('--limit', type=int, default=10, help="Max number of papers")
    parser.add_argument('--days', type=int, default=1, help="Look back days")
    parser.add_argument('--lang', type=str, choices=['cn', 'en'], default='cn', help="Language")
    
    # Filters
    parser.add_argument('--cats', nargs='+', help="Categories (e.g. cs.CV)")
    parser.add_argument('--keywords', '--kw', nargs='+', help="Keywords to filter")
    
    # Output Control (NEW)
    parser.add_argument('--prefix', type=str, default=None, help="Output filename prefix (e.g. 'deep_learning')")
    
    args = parser.parse_args()

    if args.limit > HARD_LIMIT_MAX:
        print(f"Warning: Limit {args.limit} exceeds hard limit. Set to {HARD_LIMIT_MAX}.")
        args.limit = HARD_LIMIT_MAX

    # === Fetching ===
    papers = []
    start_time = time.time()
    
    if args.arxiv:
        cats = args.cats if args.cats else ["cs.AI", "cs.LG"]
        papers = get_arxiv_papers(cats, args.limit, args.days, args.keywords)
        
    elif args.biorxiv:
        papers = get_biorxiv_papers(args.cats, args.limit, args.days, args.keywords)

    if not papers:
        print("No papers found matching your criteria.")
        return

    print(f"Found {len(papers)} matching papers. Starting AI analysis...")

    # === Analysis ===
    analyzed_data = []
    for i, paper in enumerate(papers):
        print(f"[{i+1}/{len(papers)}] Analyzing: {paper['title'][:40]}...")
        res = analyze_paper(paper, lang=args.lang)
        
        analyzed_data.append({
            "Date": paper['date'],
            "Source": paper['source'],
            "Score": res.get("score", 0),
            "Title": paper['title'],
            "Summary": res.get("summary", "N/A"),
            "Keywords": ", ".join(res.get("keywords", [])),
            "Reason": res.get("reason", "N/A"),
            "Link": paper['url'],
            "Abstract": paper['abstract']
        })
        time.sleep(1)

    # === Export ===
    if analyzed_data:
        df = pd.DataFrame(analyzed_data)
        df = df.sort_values(by="Score", ascending=False)
        
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        # === Output Filename Logic ===
        if args.prefix:
            # Custom prefix: "my_topic_2023-xx-xx"
            base_name = f"{args.prefix}_{today_str}"
        else:
            # Default: "papers_cn_2023-xx-xx"
            base_name = f"papers_{args.lang}_{today_str}"
            
        csv_filename = f"{base_name}.csv"
        md_filename = f"{base_name}.md"
        
        df.to_csv(csv_filename, index=False, encoding='utf_8_sig')
        generate_markdown_report(df, md_filename)
        
        print(f"\n[Done] Time: {time.time() - start_time:.2f}s")
        print(f"Files saved: {csv_filename}, {md_filename}")

if __name__ == "__main__":
    main()