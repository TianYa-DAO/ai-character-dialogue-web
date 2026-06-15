"""
Hermes Roleplay Engine - 蒸馏功能模块
"""

import json
import os
import time
import threading
from flask import request

from .config import CHARACTERS_DIR, MODULES_LOADED, run_research, save_research
from .utils import json_resp, parse_character_card, get_character_detail
from .ai import call_deepseek

# ── 蒸馏状态 ──
distill_status = {
    "running": False,
    "progress": "",
    "result": None,
    "error": None,
    "start_time": None,
    "end_time": None,
}

def register_distill_routes(app):
    """注册蒸馏相关路由"""
    
    @app.route("/api/distill", methods=["POST"])
    def api_start_distill():
        """开始蒸馏角色"""
        if not MODULES_LOADED:
            return json_resp({"error": "蒸馏模块未加载"}, 503)
        
        if distill_status["running"]:
            return json_resp({"error": "正在蒸馏中，请稍后"}, 400)
        
        data = request.json or {}
        char_name = data.get("char_name")
        work_name = data.get("work_name")
        media_type = data.get("media_type", "game")
        lang = data.get("lang", "zh")
        
        if not char_name or not work_name:
            return json_resp({"error": "缺少角色名或作品名"}, 400)
        
        # 启动蒸馏线程
        distill_status["running"] = True
        distill_status["progress"] = "开始调研..."
        distill_status["result"] = None
        distill_status["error"] = None
        distill_status["start_time"] = time.time()
        
        thread = threading.Thread(
            target=distill_worker,
            args=(char_name, work_name, lang, media_type),
            daemon=True
        )
        thread.start()
        
        return json_resp({"success": True, "message": "蒸馏已开始"})
    
    @app.route("/api/distill/status", methods=["GET"])
    def api_distill_status():
        """获取蒸馏状态"""
        return json_resp({
            "running": distill_status["running"],
            "progress": distill_status["progress"],
            "result": distill_status["result"],
            "error": distill_status["error"],
        })
    
    @app.route("/api/distill/generate-card", methods=["POST"])
    def api_generate_card():
        """生成角色卡"""
        data = request.json or {}
        char_name = data.get("char_name") or data.get("name")
        
        if not char_name:
            return json_resp({"error": "缺少角色名"}, 400)
        
        result = generate_character_card(char_name)
        return json_resp(result)
    
    @app.route("/api/research/list", methods=["GET"])
    def api_research_list():
        """列出调研目录"""
        research_dir = CHARACTERS_DIR / "_research"
        if not research_dir.exists():
            return json_resp([])
        
        research_list = []
        for item in research_dir.iterdir():
            if item.is_dir():
                char_name = item.name
                meta_path = item / "meta.json"
                if meta_path.exists():
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                    except:
                        meta = {}
                else:
                    meta = {}
                
                research_list.append({
                    "name": char_name,
                    "work": meta.get("work_name", ""),
                    "media_type": meta.get("media_type", ""),
                    "lang": meta.get("lang", ""),
                    "created_at": meta.get("created_at", ""),
                    "info_count": meta.get("info_count", 0),
                })
        
        return json_resp(research_list)

def distill_worker(char_name, work_name, lang, media_type):
    """蒸馏工作线程"""
    try:
        distill_status["progress"] = "正在调研..."
        research = run_research(char_name, work_name, lang=lang, media_type=media_type)
        
        distill_status["progress"] = "正在保存调研结果..."
        save_research(char_name, work_name, research, media_type)
        
        distill_status["progress"] = "正在生成角色卡..."
        card_result = generate_character_card(char_name)
        
        if card_result.get("success"):
            distill_status["result"] = {"char_name": char_name, "character": char_name, "work": work_name, "card_generated": True, "card_path": card_result.get("path"), "card_size": len(card_result.get("path", ""))}
            distill_status["progress"] = "蒸馏完成"
        else:
            distill_status["result"] = {"char_name": char_name, "character": char_name, "work": work_name, "card_error": card_result.get("error", "未知错误")}
            distill_status["progress"] = "蒸馏完成（角色卡生成失败）"
        
    except Exception as e:
        distill_status["error"] = str(e)
        distill_status["progress"] = f"蒸馏失败: {e}"
    
    distill_status["running"] = False
    distill_status["end_time"] = time.time()

def generate_character_card(char_name: str) -> dict:
    """生成角色卡"""
    research_dir = CHARACTERS_DIR / "_research" / char_name
    
    # 读取调研数据
    wiki_md = ""
    quotes_md = ""
    analysis_md = ""
    meta = {}
    
    wiki_path = research_dir / "wiki.md"
    quotes_path = research_dir / "quotes.md"
    analysis_path = research_dir / "analysis.md"
    meta_path = research_dir / "meta.json"
    
    if wiki_path.exists():
        with open(wiki_path, "r", encoding="utf-8") as f:
            wiki_md = f.read()
    
    if quotes_path.exists():
        with open(quotes_path, "r", encoding="utf-8") as f:
            quotes_md = f.read()
    
    if analysis_path.exists():
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_md = f.read()
    
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    
    # 生成角色卡
    card_text = _generate_template_card(char_name, wiki_md, quotes_md, analysis_md, meta)
    
    # 保存角色卡
    card_path = CHARACTERS_DIR / f"{char_name}.yaml"
    try:
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(card_text)
        return {"success": True, "path": str(card_path), "character": char_name, "size": len(card_text), "template": False}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _generate_template_card(char_name: str, wiki_md: str, quotes_md: str, analysis_md: str, meta: dict) -> str:
    """生成角色卡模板"""
    
    def _first_line(text):
        lines = text.strip().split("\n")
        return lines[0].strip() if lines else ""
    
    def _extract_table_valued(text, key):
        lines = text.split("\n")
        for line in lines:
            if line.startswith(key):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return ""
    
    def _extract_paragraph(text, header, max_len=500):
        lines = text.split("\n")
        in_section = False
        result = []
        for line in lines:
            if line.startswith(f"## {header}"):
                in_section = True
                continue
            if in_section:
                if line.startswith("## "):
                    break
                if line.strip():
                    result.append(line.strip())
        return " ".join(result)[:max_len]
    
    def _extract_list(text, header, max_items=8):
        lines = text.split("\n")
        in_section = False
        result = []
        for line in lines:
            if line.startswith(f"## {header}"):
                in_section = True
                continue
            if in_section:
                if line.startswith("## "):
                    break
                if line.startswith("- "):
                    result.append(line[2:].strip())
        return result[:max_items]
    
    def _extract_analysis_section(text, header, max_len=400):
        if not text:
            return ""
        sections = text.split("---")
        for section in sections:
            if header in section:
                lines = section.split("\n")[1:]
                return " ".join(l.strip() for l in lines if l.strip())[:max_len]
        return ""
    
    # 提取信息
    age = _extract_table_valued(wiki_md, "年龄")
    if not age:
        age = meta.get("info", {}).get("age", "")
    
    personality = _extract_analysis_section(analysis_md, "性格分析") or \
                  _extract_paragraph(wiki_md, "性格") or \
                  "该角色性格复杂，具有多面性。"
    
    description = _extract_paragraph(wiki_md, "角色简介") or \
                  _first_line(wiki_md)[:200] or \
                  f"{char_name}是一个复杂的角色。"
    
    backstory = _extract_paragraph(wiki_md, "背景故事") or \
                _extract_paragraph(wiki_md, "人物经历") or \
                "暂无详细背景故事。"
    
    scenario = _extract_paragraph(wiki_md, "出场场景") or \
               f"你正在与{char_name}进行对话。"
    
    likes = "\n".join(_extract_list(wiki_md, "喜好")) or "暂无明确喜好"
    dislikes = "\n".join(_extract_list(wiki_md, "厌恶")) or "暂无明确厌恶"
    
    behavior = """- 说话简洁，不喜欢冗长的表达
- 对陌生人保持警惕，但对朋友非常忠诚
- 遇到困难时会保持冷静"""
    
    speech = """语气：沉稳而坚定
口癖：喜欢用简练的语言表达观点
频率：话不多但字字珠玑
语言特征：善于用比喻，说话富有哲理"""
    
    # 从 quotes 提取对话示例
    quotes = quotes_md.strip().split("\n")[:5]
    mes_example = "\n".join([f"- {q}" for q in quotes if q.strip()]) or \
                  "- 这是一个示例对话。\n- 角色会根据情境做出回应。"
    
    first_mes = _first_line(quotes_md) or f"你好，我是{char_name}。"
    
    system_prompt = f"""你是{char_name}，请完全沉浸在这个角色中。
请根据角色的性格、背景故事和语言特征进行对话。
保持角色一致性，不要OOC（Out of Character）。"""
    
    # 构建角色卡 YAML
    card = f"""name: "{char_name}"
age: "{age}"
description: |
  {description}

personality: |
  {personality}

behavior: |
  {behavior}

speech: |
  {speech}

likes: |
  {likes}

dislikes: |
  {dislikes}

backstory: |
  {backstory}

scenario: |
  {scenario}

first_mes: "{first_mes}"

mes_example: |
  {mes_example}

system_prompt: |
  {system_prompt}

tags:
  - 蒸馏生成
  - {meta.get("media_type", "unknown")}
"""
    
    return card
