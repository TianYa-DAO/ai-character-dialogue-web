"""
Hermes Roleplay Engine - 会话管理模块
"""

import json
import time
import threading
from datetime import datetime
from flask import request

from .config import AUTO_SAVE_ENABLED, AUTO_SAVE_INTERVAL, AUTO_SAVE_DIR
from .utils import build_soul_from_engine

# ── 全局会话存储 ──
sessions = {}

# ── 自动保存定时器 ──
_save_timer = None

def get_session(sid="default"):
    """获取或创建会话"""
    if sid not in sessions:
        sessions[sid] = {
            "active_character": None,
            "character_data": None,
            "messages": [],
            "soul": "",
        }
    return sessions[sid]

def auto_save_session(sid: str = "default") -> dict:
    """
    自动保存会话到文件
    保存路径：~/.hermes/sessions/{sid}.json
    """
    if not AUTO_SAVE_ENABLED:
        return {"success": False, "error": "自动保存未启用"}
    
    s = sessions.get(sid)
    if not s:
        return {"success": False, "error": "会话不存在"}
    
    # 确保目录存在
    try:
        AUTO_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {"success": False, "error": f"无法创建目录: {e}"}
    
    # 保存文件
    save_path = AUTO_SAVE_DIR / f"{sid}.json"
    
    # 构建保存数据（不保存 API Key 等敏感信息）
    save_data = {
        "sid": sid,
        "saved_at": datetime.now().isoformat(),
        "active_character": s.get("active_character"),
        "character_data": {
            "name": (s.get("character_data") or {}).get("name"),
            "age": (s.get("character_data") or {}).get("age"),
            "description": (s.get("character_data") or {}).get("description", "")[:200],
        } if s.get("character_data") else None,
        "messages": s.get("messages", []),
        "message_count": len(s.get("messages", [])),
    }
    
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"[自动保存] 会话 {sid} 已保存到 {save_path}")
        return {"success": True, "path": str(save_path), "message_count": save_data["message_count"]}
    except Exception as e:
        return {"success": False, "error": f"保存失败: {e}"}

def load_session(sid: str = "default") -> dict:
    """从文件加载会话"""
    if not AUTO_SAVE_ENABLED:
        return {"success": False, "error": "自动保存未启用"}
    
    save_path = AUTO_SAVE_DIR / f"{sid}.json"
    
    if not save_path.exists():
        return {"success": False, "error": "未找到保存的会话"}
    
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        # 恢复会话
        s = sessions[sid] = {
            "active_character": save_data.get("active_character"),
            "character_data": save_data.get("character_data"),
            "messages": save_data.get("messages", []),
            "soul": "",
        }
        
        # 重新构建 soul
        if s["active_character"]:
            s["soul"] = build_soul_from_engine(s["active_character"])
        
        print(f"[会话恢复] 从 {save_path} 恢复了会话")
        return {
            "success": True,
            "message_count": len(s["messages"]),
            "saved_at": save_data.get("saved_at")
        }
    except Exception as e:
        return {"success": False, "error": f"加载失败: {e}"}

def _start_auto_save_timer():
    """启动自动保存定时器"""
    global _save_timer
    if AUTO_SAVE_ENABLED and _save_timer is None:
        def auto_save_loop():
            while AUTO_SAVE_ENABLED:
                time.sleep(AUTO_SAVE_INTERVAL)
                for sid in list(sessions.keys()):
                    if sessions[sid].get("messages"):
                        auto_save_session(sid)
        _save_timer = threading.Thread(target=auto_save_loop, daemon=True)
        _save_timer.start()
        print(f"[自动保存] 已启动，间隔 {AUTO_SAVE_INTERVAL} 秒")
