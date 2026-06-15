#!/usr/bin/env python3
"""
Hermes Roleplay Engine — 完整 Flask 后端
集成角色引擎、世界书引擎、蒸馏器、PNG解析器
"""

import sys
from pathlib import Path

# 确保 web 目录在 sys.path 中
WEB_DIR = Path(__file__).parent
sys.path.insert(0, str(WEB_DIR.parent))

def main():
    """启动 Flask 服务器"""
    from web import app
    
    # 启动服务器
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )

if __name__ == "__main__":
    main()
