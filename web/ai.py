"""
Hermes Roleplay Engine - AI 调用模块
"""

import json
import urllib.request
import urllib.error

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, HAS_TAVILY

# 延迟导入 Tavily（仅在需要时）
_tavily_search = None
if HAS_TAVILY:
    try:
        from tavily_client import tavily_search as _tavily_search
    except ImportError:
        pass

def _tavily_context(query: str, max_results: int = 3) -> str:
    """用 Tavily 搜索上下文，失败返回空字符串"""
    if not _tavily_search:
        return ""
    try:
        import re as _re
        result = _tavily_search(query, max_results=max_results, include_answer=True)
        if not result:
            return ""
        answer = result.get("answer", "")
        results = result.get("results", [])
        if not answer and not results:
            return ""
        parts = []
        if answer:
            parts.append(f"[Tavily搜索摘要] {answer}")
        if results:
            snippets = []
            for r in results[:max_results]:
                title = _re.sub(r"\s+", " ", r.get("title", ""))[:50]
                snippet = _re.sub(r"\s+", " ", r.get("content", ""))[:150]
                if title or snippet:
                    snippets.append(f"- {title}: {snippet}")
            if snippets:
                parts.append("\n".join(snippets))
        return "\n".join(parts)
    except Exception as e:
        print(f"[Tavily 搜索失败] {e}")
        return ""

def call_deepseek_stream(system_prompt: str, messages: list):
    """流式调用 DeepSeek API"""
    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    
    # 将角色消息转换为 DeepSeek 支持的格式
    # DeepSeek 不支持 'character' 角色，需要转换为 'assistant'
    converted_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        # 将 character 转换为 assistant
        if role == "character":
            role = "assistant"
        converted_messages.append({"role": role, "content": msg.get("content", "")})
    
    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + converted_messages,
        "stream": True,
        "temperature": 0.8,
        "max_tokens": 2048,
    })
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    req = urllib.request.Request(url, data=payload.encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            buffer = b""
            for chunk in iter(lambda: resp.read(1024), b""):
                buffer += chunk
                while b"\n\n" in buffer:
                    line, buffer = buffer.split(b"\n\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith(b"data: "):
                        line = line[6:]
                        if line == b"[DONE]":
                            return
                        try:
                            data = json.loads(line.decode("utf-8"))
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
    except urllib.error.HTTPError as e:
        yield f"[API错误] HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
    except urllib.error.URLError as e:
        yield f"[连接错误] {e.reason}"
    except Exception as e:
        yield f"[未知错误] {e}"

def call_deepseek(system_prompt: str, messages: list) -> str:
    """同步调用 DeepSeek API"""
    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    
    # 将角色消息转换为 DeepSeek 支持的格式
    # DeepSeek 不支持 'character' 角色，需要转换为 'assistant'
    converted_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        # 将 character 转换为 assistant
        if role == "character":
            role = "assistant"
        converted_messages.append({"role": role, "content": msg.get("content", "")})
    
    payload = json.dumps({
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + converted_messages,
        "stream": False,
        "temperature": 0.8,
        "max_tokens": 2048,
    })
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    req = urllib.request.Request(url, data=payload.encode("utf-8"), headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except urllib.error.HTTPError as e:
        return f"[API错误] HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
    except urllib.error.URLError as e:
        return f"[连接错误] {e.reason}"
    except Exception as e:
        return f"[未知错误] {e}"
