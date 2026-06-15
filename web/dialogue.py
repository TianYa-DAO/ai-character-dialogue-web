"""
Hermes Roleplay Engine - 对话管理模块
"""

import json
import time
from flask import request, stream_with_context, Response

from .utils import json_resp
from .session import get_session, auto_save_session, load_session
from .ai import call_deepseek_stream, call_deepseek

def register_dialogue_routes(app):
    """注册对话相关路由"""
    
    @app.route("/api/stream", methods=["POST"])
    def api_stream_message():
        """流式对话"""
        data = request.json
        user_msg = data.get("message", "")
        if not user_msg:
            return json_resp({"error": "消息不能为空"}, 400)

        s = get_session()
        s["messages"].append({
            "role": "user", "content": user_msg, "time": time.strftime("%H:%M:%S"),
        })

        if not s["soul"]:
            return json_resp({"error": "请先加载角色"}, 400)

        # 获取历史消息
        history = s["messages"]

        def generate():
            reply_buffer = ""
            for chunk in call_deepseek_stream(s["soul"], history):
                if chunk.startswith("[API错误") or chunk.startswith("[连接错误"):
                    yield f"event: message\ndata: {json.dumps({'error': chunk}, ensure_ascii=False)}\n\n"
                    return
                reply_buffer += chunk
                yield f"event: message\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            
            # 保存完整回复到消息历史
            s["messages"].append({
                "role": "character", "content": reply_buffer, "time": time.strftime("%H:%M:%S"),
            })
            yield f"event: done\ndata: {json.dumps({'finish': True}, ensure_ascii=False)}\n\n"

        return Response(stream_with_context(generate()), mimetype="text/event-stream")
    
    @app.route("/api/send", methods=["POST"])
    def api_send_message():
        """非流式对话"""
        data = request.json
        user_msg = data.get("message", "")
        if not user_msg:
            return json_resp({"error": "消息不能为空"}, 400)

        s = get_session()
        s["messages"].append({
            "role": "user", "content": user_msg, "time": time.strftime("%H:%M:%S"),
        })

        if not s["soul"]:
            return json_resp({"error": "请先加载角色"}, 400)

        # 获取历史消息（使用全部消息）
        history = s["messages"]
        reply = call_deepseek(s["soul"], history)

        s["messages"].append({
            "role": "character", "content": reply, "time": time.strftime("%H:%M:%S"),
        })

        return json_resp({"success": True, "reply": reply})
    
    @app.route("/api/clear", methods=["POST"])
    def api_clear_messages():
        """清空对话"""
        s = get_session()
        s["messages"] = []
        if s["character_data"] and s["character_data"].get("first_mes"):
            s["messages"] = [
                {"role": "character", "content": s["character_data"]["first_mes"], "time": time.strftime("%H:%M:%S")}
            ]
        return json_resp({"success": True})
    
    @app.route("/api/save-session", methods=["POST"])
    def api_save_session():
        """手动保存当前会话（自动保存）"""
        result = auto_save_session()
        return json_resp(result)
    
    @app.route("/api/load-saved", methods=["POST"])
    def api_load_saved():
        """从文件加载会话"""
        data = request.json or {}
        sid = data.get("sid", "default")
        return json_resp(load_session(sid))
    
    @app.route("/api/context-stats", methods=["GET"])
    def api_context_stats():
        """获取上下文统计信息"""
        s = get_session()
        message_count = len(s.get("messages", []))
        
        # 估算总 token 数
        total_chars = sum(len(m.get("content", "")) for m in s.get("messages", []))
        estimated_tokens = int(total_chars * 1.5)
        
        return json_resp({
            "message_count": message_count,
            "total_characters": total_chars,
            "estimated_tokens": estimated_tokens,
            "auto_save_enabled": True,
            "auto_save_interval": 60,
        })
    
    @app.route("/api/messages", methods=["GET"])
    def api_messages():
        """获取消息历史"""
        s = get_session()
        return json_resp(s.get("messages", []))
