"""
Hermes Roleplay Engine - 工具函数模块
"""

import json
from pathlib import Path
from flask import Response

from .config import CHARACTERS_DIR, SOUL_PATH, MODULES_LOADED

def json_resp(data, status=200):
    """统一 JSON 响应（确保中文不转义 + charset=utf-8）"""
    body = json.dumps(data, ensure_ascii=False, indent=None)
    return Response(body, status=status, mimetype="application/json; charset=utf-8")

def parse_character_card(path: Path) -> dict:
    """解析角色卡（YAML/JSON）"""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data:
            return data
    except Exception:
        pass
    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def list_characters() -> list:
    """列出所有角色"""
    chars = []
    if not CHARACTERS_DIR.exists():
        return chars
    for f in CHARACTERS_DIR.iterdir():
        if f.suffix.lower() in (".yaml", ".yml", ".json") and not f.name.startswith("_"):
            data = parse_character_card(f)
            chars.append({
                "file": f.name,
                "name": data.get("name", f.stem),
                "age": data.get("age", ""),
                "description": (data.get("description", "") or "")[:100],
                "tags": data.get("tags", []),
                "creator": data.get("creator", ""),
            })
    return chars

def get_character_detail(name: str) -> dict:
    """获取角色详情"""
    for f in CHARACTERS_DIR.iterdir():
        if f.suffix.lower() in (".yaml", ".yml", ".json") and not f.name.startswith("_"):
            data = parse_character_card(f)
            card_name = data.get("name", "")
            if card_name == name or f.stem == name:
                return {"success": True, "data": data, "file": f.name}
    return {"success": False, "error": f"角色 '{name}' 未找到"}

def build_soul_from_engine(char_name: str) -> str:
    """从角色引擎构建 SOUL.md 内容"""
    if SOUL_PATH.exists():
        with open(SOUL_PATH, "r", encoding="utf-8") as f:
            return f.read()
    
    result = get_character_detail(char_name)
    if result["success"]:
        data = result["data"]
        parts = [f"你是{data.get('name', '角色')}。沉浸式角色扮演模式。"]
        for key in ["personality", "behavior", "speech", "backstory", "scenario", "system_prompt"]:
            if data.get(key):
                parts.append(f"\n{key}: {data[key]}")
        if data.get("first_mes"):
            parts.append(f"\n文风锚定: {data['first_mes']}")
        return "\n".join(parts)
    return ""

def force_utf8(response):
    """强制响应为 UTF-8 编码"""
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response
