# Learn Assistant — AI 学习助手

一个基于本地大语言模型（Ollama + Qwen2.5）的智能学习辅助平台，集成知识库管理、在线测验、学习进度追踪、人脸识别登录、语音指令控制等功能。

## 项目架构

```
Learn_Assistant/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/                # 路由层（9 个模块）
│   │   │   ├── auth.py         # 密码 / JWT 登录注册
│   │   │   ├── face.py         # 人脸录入与登录
│   │   │   ├── knowledge.py    # 知识库文件上传与管理
│   │   │   ├── course.py       # 课程大纲与章节
│   │   │   ├── quiz.py         # 在线测验与试卷
│   │   │   ├── progress.py     # 学习进度
│   │   │   ├── voice.py        # 语音指令解析
│   │   │   └── wrongbook.py    # 错题本
│   │   ├── core/               # 核心模块
│   │   │   ├── config.py       # 配置（MySQL / Ollama / ChromaDB）
│   │   │   ├── database.py     # SQLAlchemy 数据库连接
│   │   │   ├── llm.py          # LLM 调用封装（ChatOllama）
│   │   │   └── security.py     # JWT 令牌 + 密码哈希
│   │   ├── models/             # SQLAlchemy 数据模型（10 张表）
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── services/           # 业务逻辑层
│   │   ├── utils/              # 工具模块
│   │   │   ├── embeddings.py   # ChromaDB 向量化存储
│   │   │   ├── file_parser.py  # PDF/DOCX/PPTX/TXT 解析
│   │   │   └── task_queue.py   # 后台任务队列
│   │   └── main.py             # FastAPI 入口
│   ├── models/                 # Embedding 模型文件
│   ├── data/                   # 运行时数据（上传文件 / ChromaDB / 人脸数据）
│   └── start.py                # 生产环境启动脚本
├── frontend/                   # Vue 3 + Vite 前端
│   └── src/
│       ├── api/                # HTTP 请求层
│       ├── router/             # 路由配置
│       ├── stores/             # Pinia 状态管理
│       ├── views/              # 页面组件
│       │   ├── Login/          # 登录/注册（密码 + 人脸）
│       │   ├── Dashboard/      # 首页仪表盘
│       │   ├── Knowledge/      # 知识库管理
│       │   ├── Course/         # 课程学习
│       │   ├── Quiz/           # 在线测验
│       │   ├── WrongBook/      # 错题本
│       │   ├── Profile/        # 个人中心
│       │   └── VoiceCommand/   # 语音指令弹窗
│       └── composables/        # 组合式函数（TTS 等）
├── docs/                       # 文档
└── README.md
```

## 系统要求

| 依赖 | 版本要求 |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| MySQL | 8.0+ |
| Ollama | 最新版 |

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd Learn_Assistant
```

### 2. 配置 MySQL

确保 MySQL 运行在 `127.0.0.1:3306`，创建数据库：

```sql
CREATE DATABASE learn_assistant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

编辑 `backend/.env`（可复制 `.env.example`）：

```ini
# MySQL 配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=learn_assistant

# Ollama 配置
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b

# 密钥
SECRET_KEY=your-secret-key-here
```

### 3. 启动 Ollama 模型

```bash
ollama pull qwen2.5:7b
ollama serve
```

### 4. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows

# 安装依赖
pip install -r requirements.txt

# 开发模式（热重载）
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 或者生产模式
python start.py
```

启动后访问 `http://127.0.0.1:8000/docs` 查看 Swagger API 文档。

### 5. 前端启动

```bash
cd frontend
npm install
npm run dev
```

启动后访问 `http://localhost:5173`。

### 6. 初始化数据

1. 注册账号 → 登录
2. 进入"知识库"页面上传学习资料（PDF / DOCX / PPTX / TXT / MD）
3. 系统自动解析文档、向量化并存入 ChromaDB
4. 刷新试卷题目（基于文档内容自动出题）
5. 开始学习

## 功能模块

### 用户认证
- 密码登录 / 注册
- **人脸识别登录** — 基于 face_recognition 库，支持录入与登录
- JWT Token 鉴权

### 知识库管理
- 上传 PDF / DOCX / PPTX / TXT / MD 文件
- 自动文本解析与分块
- ChromaDB 向量化存储
- 语义搜索（基于 sentence-transformers all-MiniLM-L6-v2）
- 文件删除时自动清理向量数据

### 课程学习
- 章节树状结构展示
- 文档内容关联
- 学习进度追踪（已完成 / 进行中 / 未开始）

### 在线测验
- 基于知识库内容自动生成题目（单选 + 判断题）
- 计时答题
- 自动批改评分
- **AI 学习建议** — 根据错题生成个性化反馈

### 错题本
- 自动收录错题
- 按章节筛选
- 错题重练 — 随机抽题再测
- 统计分析 — 错题分布、正确率

### 学习进度
- 按章节统计学习时间
- 完成度可视化
- 学习日历

### 语音指令
- 点击侧边栏麦克风按钮弹出窗口
- 按住说话 / 松开识别（Web Speech API）
- 支持导航指令：打开知识库 / 课程 / 测验 / 错题本 / 个人中心 / 首页
- 支持闲聊对话
- 语音播报反馈（TTS）

### 人脸识别
- 人脸录入（注册时绑定面部特征）
- 人脸登录（摄像头实时检测）
- 自动关闭摄像头（登录成功后）

## API 概览

所有 API 前缀为 `/api`，认证接口除外均需 Bearer Token。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 密码登录 |
| `/api/auth/face/register` | POST | 人脸录入 |
| `/api/auth/face/login` | POST | 人脸登录 |
| `/api/knowledge/documents` | GET | 文档列表 |
| `/api/knowledge/upload` | POST | 上传文件 |
| `/api/course/chapters` | GET | 章节树 |
| `/api/quiz/papers` | GET | 试卷列表 |
| `/api/quiz/papers/{id}` | GET | 试卷详情 |
| `/api/quiz/papers/{id}/submit` | POST | 提交答案 |
| `/api/quiz/papers/refresh` | POST | 刷新试卷（SSE 进度） |
| `/api/quiz/exams` | GET | 考试历史 |
| `/api/wrongbook` | GET | 错题列表 |
| `/api/wrongbook/practice` | POST | 错题重练 |
| `/api/progress/chapter` | GET | 章节进度 |
| `/api/voice/command` | POST | 语音指令解析 |

## 数据库表结构

| 表 | 说明 | 核心字段 |
|----|------|---------|
| `users` | 用户 | id, username, password_hash, face_encoding |
| `user_profiles` | 用户资料 | id, user_id, nickname, avatar |
| `chapters` | 章节 | id, title, content, parent_id, level |
| `documents` | 文档 | id, user_id, filename, file_type, chunk_count |
| `questions` | 题目 | id, chapter_id, type, content, options, answer |
| `papers` | 试卷 | id, chapter_id, title, question_count, is_ready |
| `exams` | 考试记录 | id, user_id, chapter_id, score, total_score |
| `exam_details` | 答题明细 | id, exam_id, question_id, answer, is_correct |
| `wrong_book` | 错题本 | id, user_id, question_id, wrong_count, correct_count |
| `chapter_progress` | 章节进度 | id, user_id, chapter_id, time_spent, completed |

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **ORM**: SQLAlchemy 2.0
- **数据库**: MySQL 8.0 (PyMySQL)
- **向量存储**: ChromaDB
- **Embedding**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: Ollama (qwen2.5:7b)
- **认证**: python-jose (JWT) + passlib (bcrypt)
- **人脸**: face_recognition + OpenCV + dlib
- **文档解析**: pypdf / python-docx / python-pptx

### 前端
- **框架**: Vue 3 (Composition API)
- **构建**: Vite
- **UI**: Element Plus
- **状态**: Pinia
- **路由**: Vue Router
- **语音**: Web Speech API (STT) + SpeechSynthesis (TTS)
- **HTTP**: Axios

## 常见问题

**Q: 上传文件后搜不到内容？**
检查 Ollama 是否在运行，以及 Embedding 模型文件是否存在于 `backend/models/all-MiniLM-L6-v2/`。

**Q: 人脸识别失败？**
确保摄像头权限已开启、光线充足。dlib 模型文件需要部署在纯英文路径下。

**Q: 试卷刷新后没有变化？**
刷新是增量操作 — 只为还没有试卷的章节生成新试卷。现有试卷不会被覆盖。

**Q: 语音识别不工作？**
仅 Chrome / Edge 浏览器支持 Web Speech API。Firefox 不支持语音识别，可手动输入文字。
