# ASMR Media Manager

ASMR 媒体整理中心 — 面向 Plex/NAS 的 ASMR 专用媒体管理系统。

## 功能概览

- **文件扫描**：自动扫描目录，识别音频/视频文件，计算哈希去重
- **智能解析**：从文件名自动提取 RJ/DL 号、CV、标题、语言、平台
- **作者规则**：通过关键词匹配自动识别创作者、社团，支持优先级排序
- **重命名**：按模板批量重命名，支持预览、执行、回滚
- **整理输出**：按作者归档到整理目录，自动处理文件名冲突
- **标签管理**：自定义标签，支持手动和自动来源
- **元数据编辑**：读写音频标签（Mutagen）、读取视频信息（pymediainfo）
- **AI 分析**：接入线上 AI（OpenAI/DeepSeek 等），自动分析文件名填充元数据
- **下载监听**：监控下载目录，文件下载完成后自动触发处理（三层检测机制）
- **实时进度**：WebSocket 推送扫描进度

---

## 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone <repo-url>
cd asmr_media_manager

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，设置下载目录和整理目录

# 3. 启动
docker-compose up -d

# 4. 访问
# 前端：http://localhost:3000
# 后端 API：http://localhost:3000/api/v1
# Swagger 文档：http://localhost:8080/docs
```

### 方式二：本地开发

```bash
# --- 后端 ---
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# --- 前端 ---
cd frontend
npm install
npm run dev
```

- 前端开发服务器：http://localhost:5173
- 后端 API 文档：http://localhost:8080/docs

### 方式三：Windows 启动脚本

双击 `start.bat`，自动启动后端和前端。

---

## 配置说明

### 环境变量（.env）

```env
# 目录
DOWNLOAD_DIR=/media/downloads     # 下载目录（扫描来源）
LIBRARY_DIR=/media/library        # 整理目录（输出目标）

# 数据库
DATABASE_URL=sqlite+aiosqlite:///backend/data/asmr_manager.db

# AI 设置
AI_ENABLED=true
AI_API_URL=https://api.openai.com/v1
AI_API_KEY=sk-your-key-here
AI_MODEL=gpt-4o-mini

# 扫描
WATCH_ENABLED=true
STABLE_SECONDS=10                 # 文件大小稳定秒数（判定下载完成）
```

### AI 配置

支持所有 OpenAI 兼容 API：

| 服务商 | API 地址 | 模型示例 |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` |
| 月之暗面 | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |

配置方式：
1. 前端 → 设置 → AI 设置 → 填写 API 地址、密钥、模型
2. 或直接编辑 `.env` 文件

---

## 使用指南

### 1. 扫描文件

1. 进入 **扫描管理** 页面
2. 输入下载目录路径（如 `/media/downloads`）
3. 选择扫描类型（全量/增量）
4. 点击「开始扫描」
5. 实时查看扫描进度

扫描会自动：
- 识别音频/视频文件
- 计算 SHA256 哈希（去重）
- 从文件名解析 RJ 号、CV、标题等信息
- 匹配作者规则

### 2. 浏览媒体库

1. 进入 **媒体库** 页面
2. 使用搜索框按文件名、标题、CV 搜索
3. 按类型（音频/视频）、状态（待处理/已处理）筛选
4. 点击卡片进入详情页

### 3. 编辑元数据

1. 在媒体详情页，编辑标题、RJ 号、CV、社团等字段
2. 点击「AI 分析」可自动填充（需先配置 AI）
3. 点击「保存」
4. 在标签管理区添加/删除标签

### 4. 批量操作

1. 在媒体列表页勾选多个文件
2. 点击顶部的批量操作按钮：
   - **批量重命名**：跳转到重命名预览页
   - **写入标签**：将元数据写入音频文件

### 5. 重命名

1. 选择文件后进入 **重命名预览** 页面
2. 查看旧文件名 → 新文件名的映射
3. 可自定义命名模板（可用变量：`{cv}` `{title}` `{rj_id}` `{creator}` `{circle}`）
4. 确认后点击「执行重命名」
5. 如需回滚，点击「回滚」按钮

### 6. 作者规则

1. 进入 **作者规则** 页面
2. 创建规则：
   - **关键词**：匹配的文本（如声优名、社团名）
   - **匹配方式**：包含 / 精确匹配 / 正则
   - **匹配目标**：文件名 / 目录名 / CV 字段
   - **填充字段**：创作者、社团、CV
   - **优先级**：数字越大优先级越高
3. 点击「测试」查看匹配效果
4. 点击「应用」将规则应用到已有媒体

### 7. 设置

进入 **设置** 页面可配置：

- **目录设置**：下载目录、整理目录
- **扫描设置**：是否启用监听、文件稳定秒数
- **重命名设置**：音频/视频命名模板
- **AI 设置**：API 地址、密钥、模型
- **支持格式**：查看当前支持的音视频格式

---

## 下载监听机制

系统通过三层检测判断文件是否下载完成：

1. **临时文件检测**：检查是否存在 `.part`、`.tmp`、`.crdownload` 等临时文件
2. **文件锁检测**：检查文件是否被其他进程占用
3. **大小稳定检测**：文件大小在 N 秒内（默认 10 秒）无变化

三层均通过后，才会触发自动处理流程。网络卡顿不会导致误判。

---

## 支持的格式

| 类型 | 格式 |
|------|------|
| 音频 | MP3, FLAC, WAV, M4A, OPUS, OGG |
| 视频 | MP4, MKV, AVI, MOV, WEBM |

---

## API 文档

启动后端后访问 Swagger UI：

```
http://localhost:8080/docs
```

主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/scan` | 启动扫描 |
| GET | `/api/v1/scan/jobs` | 扫描任务列表 |
| GET | `/api/v1/media` | 媒体列表（分页、筛选） |
| GET | `/api/v1/media/{id}` | 媒体详情 |
| PATCH | `/api/v1/media/{id}` | 更新媒体信息 |
| POST | `/api/v1/rename/preview` | 重命名预览 |
| POST | `/api/v1/rename/execute` | 执行重命名 |
| POST | `/api/v1/rename/rollback` | 回滚重命名 |
| GET | `/api/v1/tags` | 标签列表 |
| POST | `/api/v1/tags` | 创建标签 |
| GET | `/api/v1/author-rules` | 作者规则列表 |
| POST | `/api/v1/author-rules` | 创建规则 |
| POST | `/api/v1/metadata/ai-analyze` | AI 分析元数据 |
| GET | `/api/v1/settings` | 获取设置 |
| PATCH | `/api/v1/settings` | 更新设置 |
| WS | `/api/v1/ws/scan/{job_id}` | 扫描进度推送 |

---

## 项目结构

```
asmr_media_manager/
├── backend/                # Python FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由（9 个模块）
│   │   ├── models/         # 数据库模型（4 张表）
│   │   ├── schemas/        # Pydantic 数据验证
│   │   ├── services/       # 业务逻辑（10 个服务）
│   │   ├── core/           # 常量、异常、中间件
│   │   └── utils/          # 工具函数
│   ├── tests/              # 单元测试（49 个）
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── api/            # Axios API 层
│       ├── stores/         # Pinia 状态管理
│       ├── views/          # 页面组件（7 个）
│       ├── types/          # TypeScript 类型
│       └── router/         # 路由配置
├── docker/                 # Docker 配置
├── config/                 # 应用配置
├── docker-compose.yml
└── .env.example
```

---

## 常见问题

**Q: 扫描后没有识别出 RJ 号？**
A: 确保文件名或目录名中包含 `RJ` 开头的数字（如 `RJ123456`）或方括号包裹的纯数字（如 `[123456]`）。

**Q: AI 分析按钮灰色不可用？**
A: 需先在 设置 → AI 设置 中配置 API 地址和密钥。

**Q: 下载中的文件被误处理？**
A: 系统有三层检测机制防止误处理。如果仍有问题，可增大「稳定秒数」设置（默认 10 秒）。

**Q: 重命名后如何回滚？**
A: 在重命名预览页或通过 API `POST /api/v1/rename/rollback` 传入媒体 ID 即可回滚。

**Q: 如何添加新的 AI 服务商？**
A: 只要兼容 OpenAI API 格式即可，填入对应的 API 地址、密钥和模型名。
