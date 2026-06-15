"""
Hermes Roleplay Engine - 杂项功能模块
"""

import json
from datetime import datetime
from flask import request, send_from_directory, render_template, send_file
from pathlib import Path

from .config import MODULES_LOADED, extract_character_data, HAS_TAVILY, CHARACTERS_DIR
from .utils import json_resp, list_characters
from .session import get_session, sessions
from .ai import _tavily_context

def register_misc_routes(app):
    """注册杂项路由"""
    
    @app.route("/")
    def index():
        """主页"""
        template_path = Path(__file__).parent / "templates" / "index.html"
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content, 200, {"Content-Type": "text/html; charset=utf-8"}
    
    @app.route("/mobile")
    def mobile_ui():
        """移动端界面"""
        template_path = Path(__file__).parent / "templates" / "mobile.html"
        return send_file(str(template_path), mimetype="text/html")
    
    @app.route("/api/status", methods=["GET"])
    def api_status():
        """获取系统状态"""
        return json_resp({
            "status": "running",
            "modules_loaded": MODULES_LOADED,
            "has_tavily": HAS_TAVILY,
            "characters_count": len(list_characters()),
            "active_sessions": len(sessions),
        })
    
    @app.route("/api/saves/<char_name>", methods=["GET"])
    def api_list_saves(char_name):
        """列出角色存档"""
        saves_dir = CHARACTERS_DIR / "saves" / char_name
        saves = []
        
        if saves_dir.exists():
            for f in saves_dir.iterdir():
                if f.suffix == ".json":
                    try:
                        with open(f, "r", encoding="utf-8") as file:
                            save_data = json.load(file)
                            saves.append({
                                "slot": int(f.stem),
                                "timestamp": save_data.get("timestamp", ""),
                                "message_count": save_data.get("message_count", 0),
                                "character": save_data.get("character", char_name),
                            })
                    except Exception as e:
                        # 跳过损坏的存档文件
                        print(f"[存档] 跳过损坏文件 {f}: {e}")
        
        # 按槽位排序
        saves.sort(key=lambda x: x.get("slot", 0))
        return json_resp({"saves": saves})
    
    @app.route("/api/save", methods=["POST"])
    def api_save_scene():
        """保存场景存档"""
        data = request.json or {}
        char_name = data.get("character")
        slot = data.get("slot", 0)
        messages = data.get("messages", [])
        
        if not char_name:
            return json_resp({"error": "缺少角色名"}, 400)
        
        try:
            saves_dir = CHARACTERS_DIR / "saves" / char_name
            saves_dir.mkdir(parents=True, exist_ok=True)
            
            # 解析现有存档的timestamp格式，兼容旧格式
            save_path = saves_dir / f"{slot}.json"
            existing_timestamp = None
            if save_path.exists():
                try:
                    with open(save_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                        ts = existing.get("timestamp", "")
                        # 尝试解析旧格式 {"$date": "..."}
                        if isinstance(ts, dict) and "$date" in ts:
                            existing_timestamp = ts["$date"]
                        elif isinstance(ts, str):
                            existing_timestamp = ts
                except:
                    pass
            
            save_data = {
                "timestamp": existing_timestamp or datetime.now().isoformat(),
                "character": char_name,
                "messages": messages,
                "message_count": len(messages),
            }
            
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            return json_resp({"success": True, "slot": slot, "message_count": len(messages)})
        except Exception as e:
            return json_resp({"success": False, "error": str(e)}, 500)
    
    @app.route("/api/saves/<char_name>/<int:slot>/resume", methods=["POST"])
    def api_resume_save(char_name, slot):
        """从存档恢复"""
        save_path = CHARACTERS_DIR / "saves" / char_name / f"{slot}.json"
        
        if not save_path.exists():
            return json_resp({"error": "存档不存在"}, 404)
        
        try:
            with open(save_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            
            # 获取角色详情
            from .utils import get_character_detail, build_soul_from_engine
            char_result = get_character_detail(char_name)
            
            s = get_session()
            s["active_character"] = char_name
            
            # 恢复角色数据（如果存在）
            if char_result["success"]:
                s["character_data"] = char_result["data"]
                # 重建 soul
                s["soul"] = build_soul_from_engine(char_name)
            else:
                s["character_data"] = None
                s["soul"] = ""
            
            # 恢复消息
            s["messages"] = save_data.get("messages", [])
            
            return json_resp({
                "success": True,
                "message_count": len(s["messages"]),
                "has_character": char_result["success"]
            })
        except Exception as e:
            return json_resp({"success": False, "error": str(e)}, 500)
    
    @app.route("/api/saves/<char_name>/<int:slot>", methods=["DELETE"])
    def api_delete_save(char_name, slot):
        """删除存档"""
        save_path = CHARACTERS_DIR / "saves" / char_name / f"{slot}.json"
        
        if not save_path.exists():
            return json_resp({"error": "存档不存在"}, 404)
        
        try:
            save_path.unlink()
            return json_resp({"success": True})
        except Exception as e:
            return json_resp({"success": False, "error": str(e)}, 500)
    
    @app.route("/api/import-chat", methods=["POST"])
    def api_import_chat():
        """导入聊天记录"""
        data = request.json or {}
        messages = data.get("messages", [])
        
        s = get_session()
        s["messages"] = messages
        
        return json_resp({"success": True, "imported_count": len(messages)})
    
    @app.route("/api/png-import", methods=["POST"])
    def api_png_import():
        """从 PNG 图片导入角色卡"""
        if not MODULES_LOADED:
            return json_resp({"error": "PNG解析模块未加载"}, 503)
        
        if "file" not in request.files:
            return json_resp({"error": "缺少文件"}, 400)
        
        file = request.files["file"]
        if file.filename == "":
            return json_resp({"error": "文件名不能为空"}, 400)
        
        try:
            character_data = extract_character_data(file.read())
            
            # 保存为角色卡
            char_name = character_data.get("name", "unknown")
            card_path = CHARACTERS_DIR / f"{char_name}.yaml"
            
            import yaml
            with open(card_path, "w", encoding="utf-8") as f:
                yaml.dump(character_data, f, ensure_ascii=False, default_flow_style=False)
            
            return json_resp({
                "success": True,
                "character": char_name,
                "path": str(card_path)
            })
        except Exception as e:
            return json_resp({"success": False, "error": str(e)}, 500)
    
    @app.route("/api/engine/status", methods=["GET"])
    def api_engine_status():
        """获取引擎状态"""
        return json_resp({
            "character_engine": MODULES_LOADED,
            "worldbook_engine": MODULES_LOADED,
            "distill_engine": MODULES_LOADED,
            "png_parser": MODULES_LOADED,
        })
    
    @app.route("/api/tavily/search", methods=["POST"])
    def api_tavily_search():
        """Tavily 搜索"""
        if not HAS_TAVILY:
            return json_resp({"error": "Tavily 未配置"}, 503)
        
        data = request.json or {}
        query = data.get("query", "")
        
        if not query:
            return json_resp({"error": "缺少搜索关键词"}, 400)
        
        context = _tavily_context(query, max_results=5)
        return json_resp({"success": True, "context": context})
    
    @app.route("/api/tavily/status", methods=["GET"])
    def api_tavily_status():
        """Tavily 状态"""
        return json_resp({"enabled": HAS_TAVILY})
    
    @app.route("/api/soul", methods=["GET"])
    def api_get_soul():
        """获取当前 SOUL"""
        s = get_session()
        return json_resp({"soul": s.get("soul", "")})
    
    @app.route("/api/config", methods=["GET", "POST"])
    def api_config():
        """获取/更新配置"""
        if request.method == "GET":
            from .config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, AUTO_SAVE_ENABLED, AUTO_SAVE_INTERVAL
            return json_resp({
                "api_key_set": bool(DEEPSEEK_API_KEY),
                "model": DEEPSEEK_MODEL,
                "auto_save_enabled": AUTO_SAVE_ENABLED,
                "auto_save_interval": AUTO_SAVE_INTERVAL,
            })
        else:
            data = request.json or {}
            # 配置更新逻辑可在此扩展
            return json_resp({"success": True})
