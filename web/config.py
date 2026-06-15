"""
Hermes Roleplay Engine - 配置模块
支持从配置文件和环境变量读取配置
"""

import json
import os
import sys
from pathlib import Path

# ── 配置文件路径 ──
CONFIG_FILE = Path(__file__).parent.parent / "config.json"

def load_config():
    """加载配置文件"""
    config = {
        "deepseek": {
            "api_key": "",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
        "tavily": {
            "api_key": ""
        },
        "auto_save": {
            "enabled": True,
            "interval": 60
        },
        "app": {
            "host": "0.0.0.0",
            "port": 5000
        }
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                # 合并配置（配置文件优先）
                config.update(file_config)
                if "deepseek" in file_config:
                    config["deepseek"].update(file_config["deepseek"])
                if "tavily" in file_config:
                    config["tavily"].update(file_config["tavily"])
                if "auto_save" in file_config:
                    config["auto_save"].update(file_config["auto_save"])
                if "app" in file_config:
                    config["app"].update(file_config["app"])
        except Exception as e:
            print(f"[config] ⚠ 配置文件解析失败: {e}")
    
    return config

# 加载配置
CONFIG = load_config()

# ── UTF-8 流式解码辅助 ──
def _decode_utf8_stream(bts: bytes):
    """
    正确处理 UTF-8 流式解码：保留不完整的多字节尾部。
    返回 (解码好的字符串, 剩余的未解码字节)
    """
    i = len(bts)
    while i > 0:
        try:
            text = bts[:i].decode("utf-8")
            return text, bts[i:]
        except UnicodeDecodeError:
            i -= 1
    return "", bts

# ── 强制 UTF-8 编码（Windows 兼容） ──
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── 路径设置 ──
HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
CHARACTERS_DIR = HERMES_HOME / "characters"
SOUL_PATH = HERMES_HOME / "SOUL.md"
WEB_DIR = Path(__file__).parent

# ── 将 src/ 和 tools/ 加入 sys.path ──
SRC_DIR = WEB_DIR.parent / "src"
TOOLS_DIR = WEB_DIR.parent / "tools"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(TOOLS_DIR))

# ── 依赖检查 ──
MODULES_LOADED = True
try:
    import character_engine
    import worldbook_engine
    from distill import run_research, save_research
    from png_parser import extract_character_data
except ImportError as e:
    print(f"[web] ⚠ 模块导入失败: {e}")
    print("[web] 部分功能将不可用")
    MODULES_LOADED = False

# ── Tavily 搜索集成 ──
HAS_TAVILY = False
try:
    from tavily_client import tavily_search
    HAS_TAVILY = True
except (ImportError, RuntimeError):
    pass

# ── API 配置（优先级：环境变量 > 配置文件） ──
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or CONFIG["deepseek"]["api_key"]
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL") or CONFIG["deepseek"]["base_url"] or "https://api.deepseek.com"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL") or CONFIG["deepseek"]["model"] or "deepseek-chat"

# ── Tavily 配置 ──
TAVILY_API_KEYS = CONFIG["tavily"].get("api_keys", [])

# ── 会话自动保存配置 ──
AUTO_SAVE_ENABLED = os.environ.get("AUTO_SAVE_ENABLED") == "true" if os.environ.get("AUTO_SAVE_ENABLED") else CONFIG["auto_save"]["enabled"]
AUTO_SAVE_INTERVAL = int(os.environ.get("AUTO_SAVE_INTERVAL") or CONFIG["auto_save"]["interval"] or 60)
AUTO_SAVE_DIR = HERMES_HOME / "sessions"
