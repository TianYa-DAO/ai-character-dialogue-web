"""
Hermes Roleplay Engine - 角色管理模块
"""

import os
import json
from pathlib import Path
from flask import request

from .config import CHARACTERS_DIR, MODULES_LOADED
from .utils import json_resp, parse_character_card, build_soul_from_engine, get_character_detail, list_characters
from .session import get_session

def register_character_routes(app):
    """注册角色相关路由"""
    
    @app.route("/api/characters", methods=["GET"])
    def api_characters():
        """获取角色列表"""
        chars = list_characters()
        return json_resp(chars)
    
    @app.route("/api/character/<name>", methods=["GET"])
    def api_character_detail(name):
        """获取角色详情"""
        result = get_character_detail(name)
        if result["success"]:
            return json_resp({"success": True, "data": result["data"]})
        return json_resp(result, 404)
    
    @app.route("/api/load/<name>", methods=["POST"])
    def api_load_character(name):
        """加载角色"""
        s = get_session()
        
        result = get_character_detail(name)
        if not result["success"]:
            return json_resp({"success": False, "error": f"角色 '{name}' 未找到"}, 404)
        
        s["active_character"] = name
        s["character_data"] = result["data"]
        s["soul"] = build_soul_from_engine(name)
        
        # 初始化消息（如果有 first_mes）
        first_mes = result["data"].get("first_mes")
        s["messages"] = []
        if first_mes:
            s["messages"] = [{"role": "character", "content": first_mes, "time": ""}]
        
        return json_resp({
            "success": True,
            "name": name,
            "has_first_mes": bool(first_mes),
            "first_mes": first_mes
        })
    
    @app.route("/api/unload", methods=["POST"])
    def api_unload_character():
        """卸载角色"""
        s = get_session()
        s["active_character"] = None
        s["character_data"] = None
        s["messages"] = []
        s["soul"] = ""
        return json_resp({"success": True})
    
    @app.route("/api/character/create", methods=["POST"])
    def api_create_character():
        """创建新角色"""
        data = request.json or {}
        char_name = data.get("name")
        if not char_name:
            return json_resp({"error": "缺少角色名称"}, 400)
        
        # 检查是否已存在
        if get_character_detail(char_name)["success"]:
            return json_resp({"error": f"角色 '{char_name}' 已存在"}, 409)
        
        # 创建基础角色卡
        card_data = {
            "name": char_name,
            "age": "",
            "description": "",
            "personality": "",
            "behavior": "",
            "speech": "",
            "likes": "",
            "dislikes": "",
            "backstory": "",
            "scenario": "",
            "first_mes": "",
            "mes_example": "",
            "system_prompt": "",
            "tags": [],
        }
        
        # 保存到文件
        try:
            CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
            file_path = CHARACTERS_DIR / f"{char_name}.yaml"
            
            import yaml
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(card_data, f, ensure_ascii=False, default_flow_style=False)
            
            return json_resp({"success": True, "file": file_path.name})
        except Exception as e:
            return json_resp({"success": False, "error": str(e)}, 500)
    
    @app.route("/api/character/<name>/update", methods=["POST"])
    def api_update_character(name):
        """更新角色卡"""
        data = request.json or {}
        
        # 查找角色文件
        char_path = None
        for f in CHARACTERS_DIR.iterdir():
            if f.suffix.lower() in (".yaml", ".yml", ".json") and not f.name.startswith("_"):
                card_data = parse_character_card(f)
                if card_data.get("name") == name or f.stem == name:
                    char_path = f
                    break
        
        if not char_path:
            return json_resp({"success": False, "error": f"角色 '{name}' 未找到"}, 404)
        
        # 读取现有数据
        card_data = parse_character_card(char_path)
        
        # 更新字段（只更新提供的字段）
        for key, value in data.items():
            card_data[key] = value
        
        # 保存
        try:
            import yaml
            with open(char_path, "w", encoding="utf-8") as f:
                yaml.dump(card_data, f, ensure_ascii=False, default_flow_style=False)
            
            # 如果当前会话正在使用这个角色，更新会话中的数据
            s = get_session()
            if s.get("active_character") == name:
                s["character_data"] = card_data
                s["soul"] = build_soul_from_engine(name)
            
            return json_resp({"success": True})
        except Exception as e:
            return json_resp({"success": False, "error": str(e)}, 500)
    
    @app.route("/api/character/<name>", methods=["DELETE"])
    def api_delete_character(name):
        """删除角色"""
        # 查找角色文件
        char_path = None
        for f in CHARACTERS_DIR.iterdir():
            if f.suffix.lower() in (".yaml", ".yml", ".json") and not f.name.startswith("_"):
                card_data = parse_character_card(f)
                if card_data.get("name") == name or f.stem == name:
                    char_path = f
                    break
        
        if not char_path:
            return json_resp({"success": False, "error": f"角色 '{name}' 未找到"}, 404)
        
        # 删除文件
        try:
            char_path.unlink()
            return json_resp({"success": True})
        except Exception as e:
            return json_resp({"success": False, "error": str(e)}, 500)
