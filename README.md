\# 🤖 AI 聊天机器人



一个基于 FastAPI + 智谱 GLM-4 的全栈 AI 聊天应用，支持多模型切换、流式对话、语音交互、用户认证和知识库管理。





\## ✨ 功能特性



\### 用户系统

\- 注册 / 登录 / JWT 认证

\- 每个用户独立会话空间

\- 密码加密存储



\### 聊天功能

\- 流式输出（打字机效果）

\- 多模型切换（智谱 GLM-4-Flash / GLM-4-Plus / DeepSeek V3 / DeepSeek R1）

\- 上下文记忆（最近 10 条消息）

\- 消息复制



\### 交互体验

\- 语音输入（🎤 麦克风）

\- 语音输出（🔊 朗读）

\- 暗黑模式（🌙 一键切换）

\- 消息搜索

\- 导出聊天记录（TXT）

\- 重命名对话



\### 知识库管理

\- 上传文档（支持 PDF / Word / TXT）

\- 文档列表管理





\## 🛠️ 技术栈



\### 前端

| 技术 | 说明 |

|------|------|

| HTML5 + CSS3 | 界面结构与样式 |

| JavaScript (ES6+) | 交互逻辑 |

| Flexbox | 响应式布局 |

| Web Speech API | 语音输入/输出 |

| Fetch API | HTTP 请求 |

| localStorage | 本地存储 |

| ES Modules | 模块化加载 |

| 动态 import() | 懒加载 / 代码分割 |



\### 后端

| 技术 | 说明 |

|------|------|

| Python 3.x | 编程语言 |

| FastAPI | Web 框架 |

| Uvicorn | ASGI 服务器 |

| SQLAlchemy | ORM 数据库操作 |

| SQLite | 数据库 |

| Pydantic | 数据验证 |

| python-jose | JWT 认证 |

| passlib | 密码加密 |



\### AI 与集成

| 技术 | 说明 |

|------|------|

| 智谱 GLM-4 | 大语言模型 API |

| DeepSeek API | 大语言模型 API |

| OpenAI SDK | DeepSeek 兼容层 |

| SSE (Server-Sent Events) | 流式响应 |



\### 第三方库

```

fastapi

uvicorn

sqlalchemy

python-jose\[cryptography]

passlib\[bcrypt]

python-dotenv

zhipuai

openai

pypdf

docx2txt

numpy

```



\## 📁 项目结构

```

my\_ai\_app/

├── app/

│ ├── init.py

│ ├── auth.py # 用户认证（注册/登录/JWT）

│ ├── chat.py # AI 聊天（流式输出）

│ ├── config.py # 配置管理

│ ├── database.py # 数据库连接

│ ├── main.py # 应用入口

│ ├── models.py # 数据模型

│ ├── rag.py # 知识库管理

│ ├── sessions.py # 会话管理

│ └── upload.py # 文档上传

├── static/

│ ├── index.html # 聊天主界面

│ ├── login.html # 登录/注册页面

│ └── js/

│ ├── core.js # 核心功能

│ ├── export.js # 导出功能

│ ├── rename.js # 重命名功能

│ ├── search.js # 搜索功能

│ ├── theme.js # 暗黑模式

│ └── voice.js # 语音功能

├── .env # 环境变量

├── .gitignore

├── chat.db # SQLite 数据库

└── requirements.txt

```







\## 🚀 快速开始

```



1\. 克隆项目

git clone https://github.com/leaf-6/my\_ai\_app.git

cd my\_ai\_app



2\. 创建虚拟环境

python -m venv venv

venv\\Scripts\\activate



3\. 安装依赖

pip install -r requirements.txt



4\. 配置环境变量

创建 .env 文件：

ZHIPU\_API\_KEY=你的智谱API密钥

DEEPSEEK\_API\_KEY=你的DeepSeek密钥（可选）

SECRET\_KEY=你的JWT密钥



5\. 初始化数据库

python -c "from app.database import init\_db; init\_db()"



6\. 启动服务

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000



7\. 访问应用

打开浏览器：http://127.0.0.1:8000

```



\## API 接口

```

方法	路径	说明

POST	/api/register	用户注册

POST	/api/login	用户登录

GET	/api/sessions	获取会话列表

POST	/api/sessions	创建新会话

DELETE	/api/sessions/{id}	删除会话

GET	/api/sessions/{id}/messages	获取会话消息

POST	/chat	发送消息（流式）

POST	/api/upload/document	上传文档

GET	/ping	健康检查\\

```



学习路线（涵盖的知识点）

第一阶段：基础认知

* 前后端分离架构
* RESTful API 设计
* HTTP 请求/响应机制
* JSON 数据格式



第二阶段：前端开发

* HTML 结构语义化
* CSS 布局（Flexbox）
* CSS 变量与主题切换
* JavaScript DOM 操作
* 事件监听与处理
* Fetch API 发送请求
* localStorage 本地存储
* ES Modules (import/export)
* 动态 import() 懒加载



第三阶段：后端开发

* FastAPI 路由与中间件
* Pydantic 数据验证
* SQLAlchemy ORM
* SQLite 数据库操作
* JWT 认证流程
* 密码加密
* 依赖注入（Depends）
* 环境变量管理



第四阶段：AI 集成

* 大语言模型 API 调用
* 流式响应（SSE）
* 上下文记忆实现
* 多模型切换架构



第五阶段：交互体验

* 语音识别（Web Speech API）
* 语音合成（Web Speech API）
* 流式渲染（打字机效果）
* 骨架屏加载
* 暗黑模式实现



可证

MIT



作者

leaf-6

