"""
Hermes Roleplay Engine - 世界书模块
"""

from flask import request

from .config import MODULES_LOADED, worldbook_engine
from .utils import json_resp

def register_worldbook_routes(app):
    """注册世界书相关路由"""
    
    @app.route("/api/worldbooks", methods=["GET"])
    def api_get_active_worldbooks():
        """获取活跃的世界书列表"""
        if not MODULES_LOADED:
            return json_resp({"error": "世界书模块未加载"}, 503)
        
        try:
            books = worldbook_engine.get_active_worldbooks()
            return json_resp({"worldbooks": books})
        except Exception as e:
            return json_resp({"error": str(e)}, 500)
    
    @app.route("/api/worldbooks/available", methods=["GET"])
    def api_get_available_worldbooks():
        """获取可用的世界书列表"""
        if not MODULES_LOADED:
            return json_resp({"error": "世界书模块未加载"}, 503)
        
        try:
            books = worldbook_engine.list_worldbooks()
            return json_resp({"worldbooks": books})
        except Exception as e:
            return json_resp({"error": str(e)}, 500)
    
    @app.route("/api/worldbooks/load/<name>", methods=["POST"])
    def api_load_worldbook(name):
        """加载世界书"""
        if not MODULES_LOADED:
            return json_resp({"error": "世界书模块未加载"}, 503)
        
        try:
            result = worldbook_engine.load_worldbook(name)
            if result and isinstance(result, dict):
                book_name = result.get("name", name)
                # 将世界书添加到活跃列表（去重）
                active = worldbook_engine.get_active_wbs()
                if active is None:
                    active = []
                # 过滤掉同名的世界书
                filtered = []
                for wb in active:
                    wb_name = wb.get("name", "")
                    if book_name.lower() not in wb_name.lower():
                        filtered.append(wb)
                # 添加新的世界书
                filtered.append({
                    "name": book_name,
                    "count": result.get("count", 0),
                    "entries": result.get("count", 0)
                })
                worldbook_engine.save_active_wbs(filtered)
                return json_resp({"success": True, "worldbook": book_name})
            return json_resp({"success": False, "error": f"世界书 '{name}' 加载失败"}, 400)
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            print(f"[worldbook] 加载错误: {error_msg}")
            return json_resp({"success": False, "error": str(e)}, 500)
    
    @app.route("/api/worldbooks/unload/<name>", methods=["POST"])
    def api_unload_worldbook(name):
        """卸载世界书"""
        if not MODULES_LOADED:
            return json_resp({"error": "世界书模块未加载"}, 503)
        
        try:
            result = worldbook_engine.unload_worldbook(name)
            if result:
                return json_resp({"success": True, "worldbook": name})
            return json_resp({"success": False, "error": f"世界书 '{name}' 卸载失败"}, 400)
        except Exception as e:
            return json_resp({"success": False, "error": str(e)}, 500)
