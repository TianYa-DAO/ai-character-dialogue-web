"""
Hermes Roleplay Engine - Web 模块初始化
"""

import sys
import os

# 强制 UTF-8 编码（Windows 兼容）
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from flask import Flask
from pathlib import Path

# 初始化 Flask 应用
app = Flask(__name__, static_folder="static", template_folder="templates")

# Flask 配置
app.config["JSON_AS_ASCII"] = False

# 注册路由
from .character import register_character_routes
from .dialogue import register_dialogue_routes
from .distill import register_distill_routes
from .worldbook import register_worldbook_routes
from .misc import register_misc_routes
from .utils import force_utf8
from .session import _start_auto_save_timer

# 应用 UTF-8 强制中间件
app.after_request(force_utf8)

# 注册所有路由
register_character_routes(app)
register_dialogue_routes(app)
register_distill_routes(app)
register_worldbook_routes(app)
register_misc_routes(app)

# 启动自动保存定时器
_start_auto_save_timer()
