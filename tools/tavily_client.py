#!/usr/bin/env python3
"""
Tavily API 轮询查询工具
自动在多个 key 之间轮询，单个 key 失败自动切换下一个。

配置方法：
  在同目录下创建 tavily_keys.py，内容为：
  TAVILY_KEYS = ["tvly-YOUR_KEY_1", "tvly-YOUR_KEY_2", ...]

  获取 key: https://tavily.com/ （免费额度 1000次/月/key）
"""
import json
import os
import urllib.request

_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(_DIR, ".tavily_state.json")

# 加载 keys
try:
    from tavily_keys import TAVILY_KEYS
except ImportError:
    TAVILY_KEYS = []


def _check_keys():
    if not TAVILY_KEYS:
        raise RuntimeError(
            "Tavily API key 未配置。\n"
            "请在 tools/ 目录下创建 tavily_keys.py：\n"
            "  TAVILY_KEYS = [\"tvly-YOUR_KEY_HERE\"]\n"
            "获取 key: https://tavily.com/"
        )


def _load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"current_index": 0}


def _save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def tavily_search(query, search_depth="advanced", max_results=5, include_answer=True):
    """带轮询的 Tavily 搜索"""
    _check_keys()
    state = _load_state()
    start_index = state["current_index"]

    for attempt in range(len(TAVILY_KEYS)):
        idx = (start_index + attempt) % len(TAVILY_KEYS)
        key = TAVILY_KEYS[idx]
        try:
            data = json.dumps({
                "api_key": key,
                "query": query,
                "search_depth": search_depth,
                "include_answer": include_answer,
                "max_results": max_results,
            }).encode()
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            state["current_index"] = (idx + 1) % len(TAVILY_KEYS)
            _save_state(state)
            return result
        except urllib.error.HTTPError as e:
            if e.code in (429, 401):
                continue
            raise
        except Exception:
            continue

    raise RuntimeError("所有 Tavily API key 均已耗尽或不可用")


def tavily_extract(urls):
    """带轮询的 Tavily 内容提取"""
    _check_keys()
    state = _load_state()
    start_index = state["current_index"]

    for attempt in range(len(TAVILY_KEYS)):
        idx = (start_index + attempt) % len(TAVILY_KEYS)
        key = TAVILY_KEYS[idx]
        try:
            data = json.dumps({"api_key": key, "urls": urls}).encode()
            req = urllib.request.Request(
                "https://api.tavily.com/extract",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
            state["current_index"] = (idx + 1) % len(TAVILY_KEYS)
            _save_state(state)
            return result
        except urllib.error.HTTPError as e:
            if e.code in (429, 401):
                continue
            raise
        except Exception:
            continue

    raise RuntimeError("所有 Tavily API key 均已耗尽或不可用")
