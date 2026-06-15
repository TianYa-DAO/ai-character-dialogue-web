# AI人物对话Web可视化平台

**仓库地址**: [https://github.com/TianYa-DAO/ai-character-dialogue-web](https://github.com/TianYa-DAO/ai-character-dialogue-web)

> 基于 Hermes Roleplay Engine 的 AI 角色对话 Web 可视化平台 — 沉浸式角色扮演 + 世界书管理 + 存档系统 + Web UI

**原项目地址**: https://github.com/Lzh-xbccz/hermes-roleplay-engine  
**原作者**: [@Lzh-xbccz](https://github.com/Lzh-xbccz)

---

## ✨ 项目概述

本项目是基于 Hermes Roleplay Engine（HRE）构建的 Web 可视化平台，提供直观的角色对话界面、世界书管理和存档系统，让 AI 角色扮演体验更加沉浸式和便捷。

## 🚀 核心功能

### Web 可视化界面
- **角色选择** — 直观的角色列表展示，支持快速切换角色
- **对话界面** — 简洁优雅的聊天界面，支持实时消息推送
- **世界书管理** — 世界书加载/卸载，关键词触发式描写规范注入
- **存档系统** — 每角色3槽位存档，支持手动/自动存档

### AI 角色引擎特性
- **5维心理建模** — 依恋模式/防御机制/核心图式/需求层级/道德推理
- **身体一致性锁定** — 自动推断角色性别，生成不可违反的身体档案
- **情感描写规范** — 微表情系统、心理独白三层结构、情绪惯性
- **对话生动性** — 口癖贯穿、情绪改变语言方式、潜台词、身体语言
- **文学导向描写** — 比喻通感替代检查清单，描写服务于情感
- **防抢话** — 四重约束，严禁代控用户行为

## 📦 快速开始

### 环境要求
- Python 3.10+
- Flask、requests、sseclient-py

### 安装依赖
```bash
# 安装 Web 服务依赖
pip install flask requests sseclient-py
```

### 配置 API
编辑 `web/config.py` 文件：
```python
# AI API 配置
API_KEY = "your-api-key"
API_BASE_URL = "https://api.deepseek.com"  # 或其他兼容 API

# 服务配置
HOST = "0.0.0.0"
PORT = 5000
```

### 启动服务
```bash
cd web
python app.py
```

服务启动后访问：http://localhost:5000

## 📁 项目结构

```
ai-character-dialogue-web/
├── web/                          # Web 服务模块
│   ├── app.py                   # Flask 应用入口
│   ├── config.py                # 配置文件
│   ├── ai.py                    # AI API 调用模块
│   ├── dialogue.py              # 对话管理（SSE 实时推送）
│   ├── worldbook.py             # 世界书 API 路由
│   ├── misc.py                  # 杂项 API（配置、存档等）
│   ├── templates/
│   │   └── index.html           # 前端页面
│   └── static/
│       └── style.css            # 样式文件
├── src/                          # 核心引擎
│   ├── character_engine.py      # 角色引擎
│   └── worldbook_engine.py      # 世界书管理
├── tools/                        # 工具集
│   ├── distill.py               # 角色蒸馏器
│   ├── tavily_client.py         # Tavily API 客户端
│   ├── smart_crawl.py           # 统一爬虫入口
│   └── png_parser.py            # PNG 角色卡导入
└── README.md                    # 项目说明
```

## ⚙️ API 配置

支持的 AI API：
- **DeepSeek API** — 默认支持
- **OpenAI API** — 需修改模型名称
- **其他兼容 OpenAI 格式的 API**

## 📝 角色卡格式

支持 YAML 和 JSON 格式：

```yaml
name: 角色名
age: "年龄，性别"
description: |
  外貌描写（200-400字）
personality: |
  性格描写（表层→深层→矛盾点→对用户态度）
behavior: |
  行为模式
speech: |
  语气/口癖
likes: 喜好
dislikes: 厌恶
backstory: |
  背景故事
scenario: |
  当前场景设定（用 {{user}} 和 {{char}} 占位）
first_mes: |
  第一条消息（决定文风，最重要）
mes_example: |
  对话范例
system_prompt: |
  心理建模规则
```

## 🧠 5维心理建模

| 维度 | 理论来源 | 决定内容 |
|------|---------|---------|
| 依恋模式 | Bowlby/Ainsworth | 面对亲近时推开还是靠近 |
| 防御机制 | Anna Freud | 受伤时用什么方式保护自己 |
| 核心图式 | Beck/Young | 用什么滤镜解读世界 |
| 需求层级 | Maslow | 什么话题能真正触动角色 |
| 道德推理 | Kohlberg | 做对错判断的底层逻辑 |

## ⚠️ 安全红线

- **未成年人保护**：角色年龄 < 18 岁时，禁止一切不当内容描写
- 加载角色时自动检查年龄字段
- 违反时立即停止并卸载角色

## 📄 许可证

MIT License

## 👤 作者

**TianYa-DAO**  
GitHub: [@TianYa-DAO](https://github.com/TianYa-DAO)

---

> 沉浸式 AI 角色扮演体验，让每次对话都有可追溯的行为逻辑。