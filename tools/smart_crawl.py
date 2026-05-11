#!/usr/bin/env python3
"""
统一爬虫入口 — Tavily 首选 + Playwright fallback

用法:
  python3 smart_crawl.py <url>                    # 自动选择
  python3 smart_crawl.py <url> --force-playwright # 强制 Playwright
  python3 smart_crawl.py search "关键词"           # Tavily 搜索

依赖:
  - tavily_client.py（同目录，需配置 key）
  - Node.js + Playwright（可选，用于 fallback）
"""
import sys
import os
import subprocess
import json

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

try:
    from tavily_client import tavily_search, tavily_extract
    HAS_TAVILY = True
except (ImportError, RuntimeError):
    HAS_TAVILY = False

CRAWL_SCRIPT = os.path.join(_DIR, "crawl.mjs")
HAS_PLAYWRIGHT = os.path.isfile(CRAWL_SCRIPT)


def try_tavily(url):
    if not HAS_TAVILY:
        return None
    try:
        result = tavily_extract([url])
        results = result.get("results", [])
        if results and len(results[0].get("raw_content", "")) > 100:
            return results[0]["raw_content"]
    except Exception as e:
        print(f"[Tavily 失败: {e}]", file=sys.stderr)
    return None


def try_playwright(url):
    if not HAS_PLAYWRIGHT:
        return None
    try:
        r = subprocess.run(
            ["node", CRAWL_SCRIPT, url, "--extract", "body", "--timeout", "20000"],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode == 0 and len(r.stdout.strip()) > 50:
            return r.stdout.strip()
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"[Playwright 失败: {e}]", file=sys.stderr)
    return None


def crawl(url, force_playwright=False):
    if not force_playwright:
        content = try_tavily(url)
        if content:
            return content

    content = try_playwright(url)
    if content:
        return content

    if not HAS_TAVILY and not HAS_PLAYWRIGHT:
        print("错误：无可用爬取工具。请配置 Tavily key 或安装 Playwright。", file=sys.stderr)
    return ""


def search(query):
    if not HAS_TAVILY:
        print("错误：搜索需要 Tavily API。请配置 tavily_keys.py。", file=sys.stderr)
        return {"results": []}
    try:
        return tavily_search(query, max_results=5)
    except Exception as e:
        print(f"[搜索失败: {e}]", file=sys.stderr)
        return {"results": []}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    force_pw = "--force-playwright" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args[0] == "search" and len(args) > 1:
        result = search(" ".join(args[1:]))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        url = args[0]
        content = crawl(url, force_playwright=force_pw)
        if content:
            print(content)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
