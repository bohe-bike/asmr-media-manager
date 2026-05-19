# ASMR 媒体整理中心 - 技术设计文档

## 一、架构概览

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 (Vue 3 + TypeScript)                  │
│                    SPA + TypeScript + Vite                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                   后端 API (FastAPI)                          │
│              异步 Python + Uvicorn + Pydantic                 │
├──────────┬───────────┬────────────┬────────────┬────────────┤
│  扫描    │  规则     │  元数据    │  作者      │  整理      │
│  模块    │  引擎    │   模块     │  匹配      │  输出      │
├──────────┴───────────┴────────────┴────────────┴────────────┤
│                    数据层 (SQLite)                             │
│                  SQLAlchemy + Alembic                         │
└─────────────────────────────────────────────────────────────┘

数据流向：

下载目录 (Download) ──监控──→ 扫描 → 解析 → 匹配 → 重命名 → 整理目录 (Organized)
  /media/downloads                                           /media/library
```

### 1.2 双目录工作流

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   下载目录        │     │    处理流水线      │     │    整理目录        │
│ /media/downloads │     │                  │     │ /media/library   │
│                  │     │  1. 下载完成检测   │     │                  │
│ 新文件下载中...   │────→│  2. 文件扫描      │────→│ 作者名/           │
│ [RJ123456]       │     │  3. 文件名解析    │     │   ├── 作品A.mp4  │
│   *.flac         │     │  4. 作者关键词匹配 │     │   ├── 作品B.flac │
│                  │     │  5. 元数据提取    │     │   └── 作品C.mp3  │
│                  │     │  6. 自动重命名    │     │                  │
│                  │     │  7. 移动到整理目录 │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

**核心流程：**

1. **下载完成检测** — 等待文件下载完成后再处理（见 4.1 扫描模块）
2. **文件扫描** — 识别新下载的媒体文件
3. **文件名解析** — 提取 RJ 号、CV、标题
4. **作者匹配** — 基于关键词规则自动赋值 creator
5. **元数据提取** — 读取音频/视频元数据
6. **自动重命名** — 按模板重命名文件
7. **移动到整理目录** — 按 `作者名/` 归档，音频和视频放在同一作者目录下

### 1.2 技术选型

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端 | Vue 3 | 3.4+ | SPA 框架 |
| 前端 | TypeScript | 5.x | 类型安全 |
| 前端 | Vite | 5.x | 构建工具 |
| 前端 | Pinia | 2.x | 状态管理 |
| 前端 | Element Plus | 2.x | UI 组件库 |
| 后端 | Python | 3.11+ | 运行时 |
| 后端 | FastAPI | 0.110+ | Web 框架 |
| 后端 | SQLAlchemy | 2.x | ORM |
| 后端 | Alembic | 1.x | 数据库迁移 |
| 数据库 | SQLite | 3.x | 主存储 |
| AI | Ollama | latest | 本地 LLM 运行时 |
| AI | PaddleOCR | 2.x | 本地 OCR |
| 媒体 | Mutagen | 1.x | 音频元数据 |
| 媒体 | pymediainfo | 6.x | 视频元数据 |
| 媒体 | FFmpeg/FFprobe | 6.x | 媒体分析 |
| 文件监听 | Watchdog | 3.x | 文件系统监控 |
| 容器 | Docker | 24.x | 部署 |

### 1.3 项目结构

```
asmr_media_manager/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 应用配置
│   │   ├── database.py             # 数据库连接
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── scan.py             # 扫描接口
│   │   │   ├── media.py            # 媒体增删改查接口
│   │   │   ├── rename.py           # 重命名接口
│   │   │   ├── metadata.py         # 元数据接口
│   │   │   ├── tags.py             # 标签接口
│   │   │   └── settings.py         # 设置接口
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── media.py            # 媒体模型
│   │   │   ├── tag.py              # 标签模型
│   │   │   └── scan_job.py         # 扫描任务模型
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── media.py            # Pydantic 模式
│   │   │   ├── tag.py
│   │   │   └── scan.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scanner.py          # 文件扫描服务
│   │   │   ├── rule_engine.py      # 文件名解析
│   │   │   ├── author_matcher.py   # 作者关键词匹配
│   │   │   ├── metadata_service.py # 元数据读写
│   │   │   ├── rename_service.py   # 重命名逻辑
│   │   │   ├── tag_service.py      # 标签管理
│   │   │   ├── dedup_service.py    # 去重
│   │   │   ├── ai_service.py       # AI 集成
│   │   │   ├── cover_service.py    # 封面管理
│   │   │   └── organize_service.py # 整理输出（按作者归档）
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── exceptions.py       # 自定义异常
│   │   │   └── constants.py        # 应用常量
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── hash.py             # 哈希工具
│   │       ├── file_utils.py       # 文件辅助
│   │       └── text_utils.py       # 文本处理
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── test_scanner.py
│   │   ├── test_rule_engine.py
│   │   ├── test_rename.py
│   │   └── test_metadata.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/
│   │   │   ├── media.ts
│   │   │   ├── scan.ts
│   │   │   └── settings.ts
│   │   ├── views/
│   │   │   ├── Dashboard.vue       # 仪表盘
│   │   │   ├── MediaList.vue       # 媒体列表
│   │   │   ├── MediaDetail.vue     # 媒体详情
│   │   │   ├── ScanManager.vue     # 扫描管理
│   │   │   ├── RenamePreview.vue   # 重命名预览
│   │   │   └── Settings.vue        # 设置页
│   │   ├── components/
│   │   │   ├── MediaCard.vue       # 媒体卡片
│   │   │   ├── TagEditor.vue       # 标签编辑器
│   │   │   ├── CoverViewer.vue     # 封面查看器
│   │   │   └── ScanProgress.vue    # 扫描进度
│   │   ├── api/
│   │   │   └── index.ts
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docker-compose.yml
├── config/
│   └── default.yml
├── .env.example
├── CLAUDE.md
└── README.md
```

---

## 二、数据库设计

### 2.1 实体关系图

```
┌──────────────────┐       ┌──────────────────┐
│      media        │       │       tags        │
│    (媒体表)       │       │     (标签表)       │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ file_path        │       │ name             │
│ file_name        │       │ category         │
│ file_hash        │       │ source           │
│ file_size        │       │ created_at       │
│ media_type       │       └────────┬─────────┘
│ format           │                │
│ duration         │                │
│ bitrate          │       ┌────────▼─────────┐
│ sample_rate      │       │   media_tags     │
│ channels         │       │ (媒体标签关联表)   │
│ resolution       │       ├──────────────────┤
│ title            │       │ media_id (FK)    │
│ rj_id            │       │ tag_id (FK)      │
│ dl_id            │       │ confidence       │
│ creator          │       │ source           │
│ circle           │       └──────────────────┘
│ cv               │
│ platform         │       ┌──────────────────┐
│ language         │       │   scan_jobs      │
│ cover_path       │       │  (扫描任务表)     │
│ nfo_path         │       ├──────────────────┤
│ status           │       │ id (PK)          │
│ plex_ready       │       │ scan_path        │
│ created_at       │       │ status           │
│ updated_at       │       │ total_files      │
│ scanned_at       │       │ processed_files  │
└──────────────────┘       │ new_files        │
                           │ errors           │
                           │ started_at       │
                           │ finished_at      │
                           └──────────────────┘
```

### 2.2 表定义

#### media 表（媒体表）

```sql
CREATE TABLE media (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL UNIQUE,          -- 文件完整路径
    file_name       TEXT NOT NULL,                 -- 文件名
    file_hash       TEXT NOT NULL,                 -- SHA256 哈希值
    file_size       INTEGER NOT NULL,              -- 文件大小（字节）
    media_type      TEXT NOT NULL CHECK(media_type IN ('audio', 'video')),  -- 媒体类型
    format          TEXT NOT NULL,                 -- 文件格式（FLAC/MP3/MP4等）
    duration        REAL,                          -- 时长（秒）
    bitrate         INTEGER,                       -- 比特率（kbps）
    sample_rate     INTEGER,                       -- 采样率（Hz）
    channels        INTEGER,                       -- 声道数
    width           INTEGER,                       -- 视频宽度
    height          INTEGER,                       -- 视频高度
    title           TEXT,                          -- 作品标题
    rj_id           TEXT,                          -- DLsite RJ 号
    dl_id           TEXT,                          -- DLsite DL 号
    creator         TEXT,                          -- 创作者
    circle          TEXT,                          -- 社团
    cv              TEXT,                          -- CV（声优）
    platform        TEXT CHECK(platform IN ('dlsite', 'patreon', 'youtube', 'other')),  -- 来源平台
    language        TEXT CHECK(language IN ('ja', 'zh', 'en', 'other')),  -- 语言
    cover_path      TEXT,                          -- 封面路径
    nfo_path        TEXT,                          -- NFO 文件路径
    status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processed', 'renamed', 'error')),  -- 处理状态
    plex_ready      BOOLEAN NOT NULL DEFAULT 0,    -- 是否已生成 Plex 结构
    error_message   TEXT,                          -- 错误信息
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 更新时间
    scanned_at      DATETIME                       -- 最后扫描时间
);

CREATE INDEX idx_media_rj_id ON media(rj_id);
CREATE INDEX idx_media_creator ON media(creator);
CREATE INDEX idx_media_cv ON media(cv);
CREATE INDEX idx_media_media_type ON media(media_type);
CREATE INDEX idx_media_status ON media(status);
CREATE INDEX idx_media_file_hash ON media(file_hash);
```

#### tags 表（标签表）

```sql
CREATE TABLE tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,              -- 标签名称
    category    TEXT CHECK(category IN ('type', 'mood', 'content', 'technical', 'custom')),  -- 标签分类
    source      TEXT CHECK(source IN ('filename', 'ai', 'user', 'dlsite')),  -- 标签来源
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP  -- 创建时间
);

CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_category ON tags(category);
```

#### media_tags 表（媒体标签关联表）

```sql
CREATE TABLE media_tags (
    media_id    INTEGER NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    confidence  REAL DEFAULT 1.0 CHECK(confidence BETWEEN 0.0 AND 1.0),  -- 置信度
    source      TEXT CHECK(source IN ('filename', 'ai', 'user', 'dlsite')),  -- 关联来源
    PRIMARY KEY (media_id, tag_id)
);
```

#### scan_jobs 表（扫描任务表）

```sql
CREATE TABLE scan_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_path       TEXT NOT NULL,                 -- 扫描路径
    status          TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'running', 'completed', 'failed')),  -- 任务状态
    scan_type       TEXT NOT NULL DEFAULT 'full' CHECK(scan_type IN ('full', 'incremental')),  -- 扫描类型
    total_files     INTEGER DEFAULT 0,             -- 总文件数
    processed_files INTEGER DEFAULT 0,             -- 已处理文件数
    new_files       INTEGER DEFAULT 0,             -- 新发现文件数
    error_files     INTEGER DEFAULT 0,             -- 错误文件数
    errors          TEXT,                          -- 错误详情（JSON）
    started_at      DATETIME,                      -- 开始时间
    finished_at     DATETIME,                      -- 结束时间
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP  -- 创建时间
);
```

#### author_rules 表（作者规则表）

```sql
CREATE TABLE author_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword         TEXT NOT NULL,                 -- 匹配关键词
    match_type      TEXT NOT NULL DEFAULT 'contains' CHECK(match_type IN ('contains', 'exact', 'regex', 'prefix', 'suffix')),  -- 匹配方式
    match_target    TEXT NOT NULL DEFAULT 'filename' CHECK(match_target IN ('filename', 'metadata_artist', 'metadata_album', 'directory', 'all')),  -- 匹配目标
    creator         TEXT,                          -- 匹配后赋值的创作者
    circle          TEXT,                          -- 匹配后赋值的社团
    cv              TEXT,                          -- 匹配后赋值的 CV
    priority        INTEGER NOT NULL DEFAULT 0,    -- 优先级（数值越大越优先）
    enabled         BOOLEAN NOT NULL DEFAULT 1,    -- 是否启用
    hit_count       INTEGER NOT NULL DEFAULT 0,    -- 命中次数（用于统计）
    last_hit_at     DATETIME,                      -- 最后命中时间
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_author_rules_keyword ON author_rules(keyword);
CREATE INDEX idx_author_rules_creator ON author_rules(creator);
CREATE INDEX idx_author_rules_circle ON author_rules(circle);
CREATE INDEX idx_author_rules_enabled ON author_rules(enabled);
CREATE INDEX idx_author_rules_priority ON author_rules(priority);
```

**匹配方式说明：**

| match_type | 说明 | 示例 |
|-----------|------|------|
| contains | 包含关键词（模糊匹配） | 关键词 `涼花` 匹配 `涼花みなせ` |
| exact | 完全匹配 | 关键词 `涼花みなせ` 精确匹配 |
| regex | 正则表达式匹配 | 关键词 `涼花.*せ` 正则匹配 |
| prefix | 前缀匹配 | 关键词 `涼花` 匹配以 `涼花` 开头的文本 |
| suffix | 后缀匹配 | 关键词 `みなせ` 匹配以 `みなせ` 结尾的文本 |

**匹配目标说明：**

| match_target | 说明 |
|-------------|------|
| filename | 匹配文件名 |
| metadata_artist | 匹配音频元数据中的 artist 字段 |
| metadata_album | 匹配音频元数据中的 album 字段 |
| directory | 匹配所在目录名 |
| all | 匹配以上所有目标 |

**匹配流程：**

```
文件扫描
  ↓
收集匹配文本（文件名 + 元数据 + 目录名）
  ↓
遍历 enabled=true 的规则，按 priority 降序
  ↓
第一条命中的规则 → 赋值 creator / circle / cv
  ↓
更新 hit_count 和 last_hit_at
  ↓
无命中 → 保持为空，等待用户手动补充或新建规则
```

---

## 三、API 设计

### 3.1 API 概述

基础路径：`/api/v1`

所有响应遵循标准格式：

```json
{
    "code": 200,
    "message": "success",
    "data": {}
}
```

错误响应：

```json
{
    "code": 400,
    "message": "错误描述",
    "detail": "详细错误信息"
}
```

### 3.2 扫描接口

#### POST /api/v1/scan

启动扫描任务。

**请求：**

```json
{
    "path": "/media/asmr",
    "scan_type": "full",
    "recursive": true
}
```

**响应：**

```json
{
    "code": 200,
    "data": {
        "job_id": 1,
        "status": "pending",
        "message": "扫描任务已创建"
    }
}
```

#### GET /api/v1/scan/{job_id}

获取扫描任务状态。

**响应：**

```json
{
    "code": 200,
    "data": {
        "id": 1,
        "scan_path": "/media/asmr",
        "status": "running",
        "scan_type": "full",
        "total_files": 1500,
        "processed_files": 750,
        "new_files": 12,
        "error_files": 3,
        "started_at": "2026-05-18T10:00:00Z",
        "progress_percent": 50.0
    }
}
```

#### GET /api/v1/scan/jobs

获取扫描任务列表。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |
| status | string | - | 按状态筛选 |

### 3.3 媒体接口

#### GET /api/v1/media

获取媒体列表。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |
| media_type | string | - | 媒体类型：audio/video |
| status | string | - | 按状态筛选 |
| creator | string | - | 按创作者筛选 |
| cv | string | - | 按 CV 筛选 |
| rj_id | string | - | 按 RJ 号筛选 |
| tag | string | - | 按标签筛选 |
| search | string | - | 全文搜索 |
| sort_by | string | created_at | 排序字段 |
| sort_order | string | desc | 排序方向：asc/desc |

**响应：**

```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "id": 1,
                "file_name": "[RJ123456] 深夜耳搔治愈.flac",
                "media_type": "audio",
                "title": "深夜耳搔治愈",
                "rj_id": "RJ123456",
                "cv": "涼花みなせ",
                "circle": "CircleName",
                "platform": "dlsite",
                "duration": 3600.5,
                "format": "FLAC",
                "file_size": 524288000,
                "status": "processed",
                "tags": ["耳搔", "助眠"],
                "cover_url": "/api/v1/media/1/cover",
                "created_at": "2026-05-18T10:00:00Z"
            }
        ],
        "total": 1500,
        "page": 1,
        "page_size": 20
    }
}
```

#### GET /api/v1/media/{id}

获取媒体详情。

**响应：**

```json
{
    "code": 200,
    "data": {
        "id": 1,
        "file_path": "/media/asmr/[RJ123456] 深夜耳搔治愈.flac",
        "file_name": "[RJ123456] 深夜耳搔治愈.flac",
        "file_hash": "sha256:abc123...",
        "file_size": 524288000,
        "media_type": "audio",
        "format": "FLAC",
        "duration": 3600.5,
        "bitrate": 1411,
        "sample_rate": 44100,
        "channels": 2,
        "title": "深夜耳搔治愈",
        "rj_id": "RJ123456",
        "cv": "涼花みなせ",
        "circle": "CircleName",
        "platform": "dlsite",
        "language": "ja",
        "tags": [
            {"id": 1, "name": "耳搔", "source": "filename"},
            {"id": 2, "name": "助眠", "source": "ai"}
        ],
        "cover_path": "/media/asmr/[RJ123456] 深夜耳搔治愈/cover.jpg",
        "status": "processed",
        "plex_ready": true,
        "created_at": "2026-05-18T10:00:00Z",
        "updated_at": "2026-05-18T10:05:00Z"
    }
}
```

#### PATCH /api/v1/media/{id}

更新媒体元数据。

**请求：**

```json
{
    "title": "更新后的标题",
    "cv": "新CV名",
    "tags": ["耳搔", "助眠", "新标签"]
}
```

#### GET /api/v1/media/{id}/cover

获取媒体封面图片。

直接返回图片文件，Content-Type 为对应的图片类型。

### 3.4 重命名接口

#### POST /api/v1/rename/preview

预览重命名操作。

**请求：**

```json
{
    "media_ids": [1, 2, 3],
    "pattern": "[{cv}] {title} ({rj_id})"
}
```

**响应：**

```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "media_id": 1,
                "old_path": "/media/asmr/[RJ123456] 深夜耳搔治愈.flac",
                "new_path": "/media/asmr/[涼花みなせ] 深夜耳搔治愈 (RJ123456).flac",
                "new_dir": "/media/asmr/[涼花みなせ] 深夜耳搔治愈 (RJ123456)",
                "conflict": false
            }
        ],
        "conflicts": [],
        "total": 3
    }
}
```

#### POST /api/v1/rename/execute

执行重命名操作。

**请求：**

```json
{
    "media_ids": [1, 2, 3],
    "pattern": "[{cv}] {title} ({rj_id})",
    "create_dirs": true,
    "move_cover": true
}
```

**响应：**

```json
{
    "code": 200,
    "data": {
        "success": 3,
        "failed": 0,
        "results": [
            {
                "media_id": 1,
                "old_path": "/media/asmr/[RJ123456] 深夜耳搔治愈.flac",
                "new_path": "/media/asmr/[涼花みなせ] 深夜耳搔治愈 (RJ123456)/[涼花みなせ] 深夜耳搔治愈 (RJ123456).flac",
                "status": "success"
            }
        ]
    }
}
```

#### POST /api/v1/rename/rollback

回滚重命名操作。

**请求：**

```json
{
    "job_id": 1
}
```

### 3.5 元数据接口

#### POST /api/v1/metadata/generate

生成元数据文件（NFO 等）。

**请求：**

```json
{
    "media_ids": [1, 2, 3],
    "generate_nfo": true,
    "generate_covers": true
}
```

#### POST /api/v1/metadata/write-tags

将元数据标签写入音频文件。

**请求：**

```json
{
    "media_ids": [1, 2, 3],
    "fields": ["artist", "album", "genre", "comment"]
}
```

### 3.6 标签接口

#### GET /api/v1/tags

获取所有标签。

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| category | string | 按分类筛选 |
| search | string | 按名称搜索 |

#### POST /api/v1/tags

创建新标签。

**请求：**

```json
{
    "name": "新标签",
    "category": "custom"
}
```

#### POST /api/v1/media/{id}/tags

为媒体添加标签。

**请求：**

```json
{
    "tag_ids": [1, 2],
    "source": "user"
}
```

#### DELETE /api/v1/media/{id}/tags/{tag_id}

移除媒体标签。

### 3.7 作者规则接口

#### GET /api/v1/author-rules

获取作者规则列表。

**查询参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量 |
| creator | string | - | 按创作者筛选 |
| circle | string | - | 按社团筛选 |
| keyword | string | - | 按关键词搜索 |
| enabled | bool | - | 按启用状态筛选 |

**响应：**

```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "id": 1,
                "keyword": "涼花みなせ",
                "match_type": "contains",
                "match_target": "all",
                "creator": "涼花みなせ",
                "circle": "てぃーぐる",
                "cv": "涼花みなせ",
                "priority": 10,
                "enabled": true,
                "hit_count": 42,
                "last_hit_at": "2026-05-18T10:00:00Z",
                "created_at": "2026-05-01T00:00:00Z"
            }
        ],
        "total": 150,
        "page": 1,
        "page_size": 20
    }
}
```

#### POST /api/v1/author-rules

创建作者规则。

**请求：**

```json
{
    "keyword": "涼花みなせ",
    "match_type": "contains",
    "match_target": "all",
    "creator": "涼花みなせ",
    "circle": "てぃーぐる",
    "cv": "涼花みなせ",
    "priority": 10
}
```

**响应：**

```json
{
    "code": 200,
    "data": {
        "id": 1,
        "keyword": "涼花みなせ",
        "match_type": "contains",
        "match_target": "all",
        "creator": "涼花みなせ",
        "circle": "てぃーぐる",
        "cv": "涼花みなせ",
        "priority": 10,
        "enabled": true,
        "hit_count": 0,
        "created_at": "2026-05-18T10:00:00Z"
    }
}
```

#### POST /api/v1/author-rules/batch

批量创建作者规则。

**请求：**

```json
{
    "rules": [
        {
            "keyword": "涼花みなせ",
            "creator": "涼花みなせ",
            "circle": "てぃーぐる",
            "cv": "涼花みなせ"
        },
        {
            "keyword": "月乃",
            "creator": "月乃",
            "circle": "Lovesmile",
            "cv": "月乃"
        }
    ]
}
```

#### PATCH /api/v1/author-rules/{id}

更新作者规则。

**请求：**

```json
{
    "keyword": "涼花みなせ",
    "priority": 20,
    "enabled": false
}
```

#### DELETE /api/v1/author-rules/{id}

删除作者规则。

#### POST /api/v1/author-rules/scan-test

测试规则匹配效果（不实际修改数据）。

**请求：**

```json
{
    "rule_id": 1
}
```

**响应：**

```json
{
    "code": 200,
    "data": {
        "total_media": 1500,
        "matched_media": 42,
        "samples": [
            {
                "file_name": "[RJ123456] 深夜耳搔治愈.flac",
                "matched_text": "涼花みなせ",
                "match_source": "metadata_artist"
            }
        ]
    }
}
```

#### POST /api/v1/author-rules/apply

将规则应用到已有媒体（重新匹配）。

**请求：**

```json
{
    "rule_ids": [1, 2, 3],
    "overwrite": false
}
```

**响应：**

```json
{
    "code": 200,
    "data": {
        "total_checked": 1500,
        "newly_classified": 38,
        "skipped": 4,
        "overwritten": 0
    }
}
```

`overwrite` 为 `false` 时，已有 creator 的媒体不会被覆盖。

### 3.8 去重接口

#### GET /api/v1/dedup/groups

获取重复文件分组。

**响应：**

```json
{
    "code": 200,
    "data": {
        "groups": [
            {
                "group_id": "hash:abc123",
                "type": "file_hash",
                "items": [
                    {
                        "id": 1,
                        "file_path": "/media/asmr/file1.flac",
                        "file_size": 524288000,
                        "format": "FLAC",
                        "quality_score": 95
                    },
                    {
                        "id": 2,
                        "file_path": "/media/asmr/file1.mp3",
                        "file_size": 52428800,
                        "format": "MP3",
                        "quality_score": 60
                    }
                ],
                "recommended_keep": 1
            }
        ],
        "total_groups": 50
    }
}
```

#### POST /api/v1/dedup/resolve

处理重复文件。

**请求：**

```json
{
    "group_id": "hash:abc123",
    "keep_id": 1,
    "delete_others": false,
    "move_others_to": "/media/asmr/duplicates"
}
```

### 3.8 设置接口

#### GET /api/v1/settings

获取当前设置。

**响应：**

```json
{
    "code": 200,
    "data": {
        "download_dir": "/media/downloads",
        "library_dir": "/media/library",
        "watch_enabled": true,
        "stable_seconds": 10,
        "rename_pattern": "[{cv}] {title} ({rj_id})",
        "video_rename_pattern": "[{creator}] {title}",
        "default_language": "ja",
        "ai_enabled": false,
        "ai_model": "qwen2:7b",
        "ocr_enabled": false,
        "cover_filenames": ["cover.jpg", "folder.jpg"],
        "supported_audio_formats": ["mp3", "flac", "wav", "m4a", "opus", "ogg"],
        "supported_video_formats": ["mp4", "mkv", "avi", "mov", "webm"]
    }
}
```

#### PATCH /api/v1/settings

更新设置。

### 3.9 WebSocket 接口

#### WS /api/v1/ws/scan/{job_id}

实时扫描进度推送。

**消息（服务端 -> 客户端）：**

```json
{
    "type": "progress",
    "data": {
        "processed_files": 751,
        "total_files": 1500,
        "current_file": "/media/asmr/[RJ789012] 新文件.flac",
        "new_files": 13
    }
}
```

```json
{
    "type": "completed",
    "data": {
        "total_files": 1500,
        "new_files": 15,
        "error_files": 3,
        "duration_seconds": 45
    }
}
```

```json
{
    "type": "error",
    "data": {
        "file": "/media/asmr/corrupted.flac",
        "error": "无法读取文件元数据"
    }
}
```

---

## 四、模块设计

### 4.1 扫描模块（Scanner）

**职责：** 监控下载目录、检测下载完成、发现媒体文件、计算哈希值。

```python
class ScannerService:
    def __init__(self, download_dir: str, library_dir: str):
        self.download_dir = download_dir
        self.library_dir = library_dir
        self._pending_files: dict[str, FileInfo] = {}  # 待确认下载完成的文件

    async def start_watch(self) -> None:
        """启动下载目录监听，自动检测新文件并等待下载完成"""
        ...

    async def _on_file_created(self, file_path: str) -> None:
        """文件创建事件：开始监控下载状态"""
        self._pending_files[file_path] = FileInfo(
            path=file_path,
            first_seen=datetime.utcnow(),
            last_size=0,
            stable_since=None,
        )

    async def _check_download_complete(self) -> list[str]:
        """定期检查待处理文件是否下载完成，返回已完成的文件列表"""
        completed = []
        for path, info in list(self._pending_files.items()):
            if not os.path.exists(path):
                del self._pending_files[path]
                continue
            current_size = os.path.getsize(path)
            if current_size == info.last_size:
                if info.stable_since is None:
                    info.stable_since = datetime.utcnow()
                elif (datetime.utcnow() - info.stable_since).seconds >= self.stable_seconds:
                    # 文件大小稳定超过阈值，判定为下载完成
                    completed.append(path)
                    del self._pending_files[path]
            else:
                info.last_size = current_size
                info.stable_since = None  # 大小变化，重置稳定计时
        return completed

    async def scan_directory(
        self,
        path: str,
        scan_type: str = "full",
        recursive: bool = True
    ) -> ScanJob:
        """启动扫描任务"""
        ...

    async def process_and_organize(self, file_path: str) -> Media:
        """完整处理流程：扫描 → 解析 → 匹配 → 重命名 → 移动到整理目录"""
        # 1. 计算哈希、提取元数据
        media = await self._process_file(file_path)
        # 2. 规则引擎解析文件名
        parsed = await self.rule_engine.parse(file_path)
        # 3. 作者关键词匹配
        author_match = await self.author_matcher.match(media)
        if author_match:
            media.creator = author_match["creator"]
            media.circle = author_match["circle"]
            media.cv = author_match["cv"]
        # 4. 自动重命名并移动到整理目录
        new_path = await self.organize_service.move_to_library(media)
        media.file_path = new_path
        media.status = "processed"
        await self.db.commit()
        return media

    async def _compute_hash(self, file_path: str) -> str:
        """计算文件 SHA256 哈希值"""
        ...

    def _is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        ...
```

**下载完成检测策略：**

```text
文件创建 → 加入待监控列表 → 每 5 秒检查文件大小
  ↓
大小不变且持续 10 秒 → 判定为下载完成 → 进入处理流水线
  ↓
大小仍在变化 → 继续等待
```

| 检测方式 | 说明 |
|---------|------|
| 文件大小稳定 | 文件大小连续 N 秒无变化，判定下载完成 |
| 临时文件消失 | 部分下载工具会创建 `.part` / `.tmp` 文件，消失后判定完成 |
| 锁定文件检测 | 检查文件是否被其他进程锁定 |

**关键设计决策：**

- 使用 `asyncio` 实现非阻塞 I/O
- 增量扫描跳过 `mtime` 未变化的文件
- SHA256 按 64KB 分块计算，支持大文件
- 集成 Watchdog 实现下载目录实时监听
- 批量数据库插入（每 100 条记录一个事务）
- **下载完成检测**：文件大小稳定 10 秒后才触发处理，避免处理未完成的文件

### 4.2 规则引擎（Rule Engine）

**职责：** 解析文件名和目录名，提取结构化元数据。

```python
class RuleEngine:
    # 预定义模式（按优先级排序）
    PATTERNS = [
        # RJ 号模式
        r'RJ(\d{6,8})',
        r'DL(\d{6,8})',
        r'\[(\d{6,8})\]',

        # CV 模式
        r'CV[\.．:：]\s*(.+?)[\]\)】]',
        r'\[CV[\.．]?(.+?)\]',

        # 社团/创作者模式
        r'\[(.+?)\]',  # 通用方括号内容
    ]

    async def parse(self, file_path: str) -> dict:
        """解析文件路径，返回结构化元数据"""
        ...

    def _extract_rj_id(self, text: str) -> str | None:
        """从文本中提取 RJ/DL 号"""
        ...

    def _extract_cv(self, text: str) -> str | None:
        """从文本中提取 CV 名称"""
        ...

    def _extract_title(self, filename: str, extracted: dict) -> str:
        """从文件名中提取并清理标题"""
        ...

    def _detect_language(self, text: str) -> str:
        """检测文本主要语言"""
        ...

    def _detect_platform(self, metadata: dict) -> str:
        """根据元数据推断来源平台"""
        ...
```

**模式优先级：**

1. 显式 RJ/DL 号标记 `[RJ123456]`
2. CV 标记 `CV.名前`
3. 社团/创作者方括号 `[CreatorName]`
4. 启发式标题提取

### 4.3 作者匹配服务（AuthorMatcher）

**职责：** 基于用户定义的关键词规则，自动匹配并赋值创作者、社团、CV。

```python
class AuthorMatcher:
    def __init__(self, db_session):
        self.db = db_session
        self._rules_cache = None
        self._cache_loaded_at = None

    async def match(self, media: Media) -> dict | None:
        """对单个媒体执行作者匹配，返回匹配结果或 None"""
        # 收集所有可匹配的文本
        texts = self._collect_match_texts(media)
        # 按优先级加载规则
        rules = await self._get_enabled_rules()
        for rule in rules:
            for target, text in texts.items():
                if self._match_rule(rule, text):
                    await self._record_hit(rule)
                    return {
                        "creator": rule.creator,
                        "circle": rule.circle,
                        "cv": rule.cv,
                        "matched_keyword": rule.keyword,
                        "matched_target": target,
                        "rule_id": rule.id,
                    }
        return None

    def _collect_match_texts(self, media: Media) -> dict:
        """收集所有可用于匹配的文本"""
        texts = {"filename": media.file_name, "directory": ""}
        if media.file_path:
            texts["directory"] = os.path.basename(os.path.dirname(media.file_path))
        if media.creator:
            texts["metadata_artist"] = media.creator
        if media.title:
            texts["metadata_album"] = media.title
        return texts

    def _match_rule(self, rule: AuthorRule, text: str) -> bool:
        """根据规则类型执行匹配"""
        if not text:
            return False
        if rule.match_type == "contains":
            return rule.keyword in text
        elif rule.match_type == "exact":
            return rule.keyword == text
        elif rule.match_type == "prefix":
            return text.startswith(rule.keyword)
        elif rule.match_type == "suffix":
            return text.endswith(rule.keyword)
        elif rule.match_type == "regex":
            return bool(re.search(rule.keyword, text))
        return False

    async def _record_hit(self, rule: AuthorRule) -> None:
        """记录规则命中次数和时间"""
        rule.hit_count += 1
        rule.last_hit_at = datetime.utcnow()
        await self.db.commit()

    async def _get_enabled_rules(self) -> list[AuthorRule]:
        """获取已启用的规则，按优先级降序排列（带缓存）"""
        now = datetime.utcnow()
        if (self._rules_cache is None or
                (now - self._cache_loaded_at).seconds > 300):
            self._rules_cache = await self.db.execute(
                select(AuthorRule)
                .where(AuthorRule.enabled == True)
                .order_by(AuthorRule.priority.desc())
            )
            self._cache_loaded_at = now
        return self._rules_cache

    async def apply_to_existing(
        self,
        rule_ids: list[int] | None = None,
        overwrite: bool = False
    ) -> dict:
        """将规则应用到已有媒体记录"""
        stats = {"total_checked": 0, "newly_classified": 0, "skipped": 0, "overwritten": 0}
        query = select(Media)
        if not overwrite:
            query = where(Media.creator.is_(None))
        medias = await self.db.execute(query)
        for media in medias:
            stats["total_checked"] += 1
            result = await self.match(media)
            if result:
                if media.creator and not overwrite:
                    stats["skipped"] += 1
                    continue
                if media.creator and overwrite:
                    stats["overwritten"] += 1
                else:
                    stats["newly_classified"] += 1
                media.creator = result["creator"]
                media.circle = result["circle"]
                media.cv = result["cv"]
        await self.db.commit()
        return stats
```

**工作流程：**

```
新文件扫描完成
  ↓
调用 AuthorMatcher.match(media)
  ↓
收集匹配文本（文件名 + 目录名 + 元数据）
  ↓
遍历规则（按 priority 降序），第一条命中即返回
  ↓
命中 → 赋值 creator / circle / cv，更新 hit_count
  ↓
未命中 → creator 为空，等待用户手动补充或新建规则
```

**关键设计决策：**

- 规则按 `priority` 降序匹配，第一条命中即停止（短路逻辑）
- 规则列表带 5 分钟缓存，避免频繁查询数据库
- `hit_count` 用于统计哪些规则最有效，辅助用户优化规则
- `apply_to_existing` 支持对已有媒体重新匹配，`overwrite=false` 时不覆盖已有 creator
- 匹配目标支持 `all`（同时搜索文件名 + 元数据 + 目录名）

### 4.4 元数据服务（Metadata Service）

**职责：** 读写媒体文件元数据。

```python
class MetadataService:
    async def read_audio_metadata(self, file_path: str) -> dict:
        """使用 Mutagen 读取音频文件元数据"""
        ...

    async def read_video_metadata(self, file_path: str) -> dict:
        """使用 pymediainfo 读取视频文件元数据"""
        ...

    async def write_audio_tags(
        self,
        file_path: str,
        tags: dict
    ) -> bool:
        """将标签写入音频文件"""
        ...

    async def generate_nfo(
        self,
        media: Media,
        output_path: str
    ) -> str:
        """为视频媒体生成 NFO 文件"""
        ...

    async def generate_plex_metadata(
        self,
        media: Media,
        output_dir: str
    ) -> dict:
        """生成完整的 Plex 元数据集合"""
        ...
```

**音频标签映射：**

| 数据库字段 | ID3 标签 | Vorbis 注释 |
|-----------|---------|------------|
| title | TITALB | TITLE |
| cv | TPE1 | ARTIST |
| circle | TPE2 | ALBUMARTIST |
| tags | TCON | GENRE |
| rj_id | COMM | COMMENT |

### 4.4 AI 服务（AI Service）

**职责：** 对接本地大语言模型，实现内容理解。

```python
class AIService:
    def __init__(self, model: str = "qwen2:7b"):
        self.model = model
        self.ollama_url = "http://localhost:11434"

    async def infer_tags(self, title: str) -> list[dict]:
        """使用 LLM 从标题推断标签"""
        prompt = f"""分析以下ASMR作品标题，提取标签。
标题：{title}

返回JSON格式：
{{"tags": ["标签1", "标签2"], "mood": "氛围", "type": "类型"}}

只返回JSON，不要其他内容。"""
        ...

    async def run_ocr(self, image_path: str) -> list[str]:
        """对图片运行 OCR 识别文字"""
        ...

    async def classify_content(self, metadata: dict) -> dict:
        """根据可用元数据对内容进行分类"""
        ...
```

**AI 原则：**

- 所有处理通过 Ollama 在本地完成
- 数据不离开本地网络
- AI 结果附带置信度分数并缓存
- 用户可覆盖任何 AI 建议
- AI 为可选功能，系统无 AI 也能完整运行

### 4.5 整理输出服务（Organize Service）

**职责：** 将处理完成的媒体文件移动到整理目录，按作者归档。

```python
class OrganizeService:
    def __init__(self, library_dir: str):
        self.library_dir = library_dir

    async def move_to_library(self, media: Media) -> str:
        """将媒体文件移动到整理目录的作者名下，返回新路径"""
        # 确定作者目录
        author = media.creator or media.cv or "未分类"
        author_dir = os.path.join(self.library_dir, self._sanitize(author))
        os.makedirs(author_dir, exist_ok=True)
        # 生成新文件名
        new_name = self._build_filename(media)
        new_path = os.path.join(author_dir, new_name)
        # 处理文件名冲突
        new_path = self._resolve_conflict(new_path)
        # 移动文件
        shutil.move(media.file_path, new_path)
        # 移动关联文件（封面、NFO 等）
        await self._move_associated_files(media.file_path, new_path)
        return new_path

    def _build_filename(self, media: Media) -> str:
        """根据媒体类型和元数据生成文件名"""
        if media.media_type == "audio":
            return self._build_audio_filename(media)
        else:
            return self._build_video_filename(media)

    def _build_audio_filename(self, media: Media) -> str:
        """音频文件名：[CV] 标题 (RJ号).ext"""
        parts = []
        if media.cv:
            parts.append(f"[{media.cv}]")
        if media.title:
            parts.append(media.title)
        if media.rj_id:
            parts.append(f"({media.rj_id})")
        name = " ".join(parts) if parts else media.file_name
        ext = os.path.splitext(media.file_name)[1]
        return self._sanitize(name) + ext

    def _build_video_filename(self, media: Media) -> str:
        """视频文件名：[创作者] 标题.ext"""
        parts = []
        if media.creator:
            parts.append(f"[{media.creator}]")
        if media.title:
            parts.append(media.title)
        name = " ".join(parts) if parts else media.file_name
        ext = os.path.splitext(media.file_name)[1]
        return self._sanitize(name) + ext

    def _sanitize(self, name: str) -> str:
        """清理文件名中的非法字符"""
        ...

    def _resolve_conflict(self, path: str) -> str:
        """文件名冲突时自动加序号"""
        ...

    async def _move_associated_files(self, old_path: str, new_path: str) -> None:
        """移动关联文件（封面、NFO 等）"""
        ...
```

**输出结构（按作者归档，音频视频同目录）：**

```
/media/library/
├── 涼花みなせ/
│   ├── [涼花みなせ] 深夜耳搔治愈 (RJ123456).flac
│   ├── [涼花みなせ] 治愈系耳搔 (RJ789012).flac
│   └── [涼花みなせ] 视频作品.mp4
├── Gibi ASMR/
│   ├── [Gibi ASMR] Cranial Nerve Exam.mp4
│   └── [Gibi ASMR] Sleep Clinic.mp4
├── 月乃/
│   ├── [月乃] 雨声助眠 (RJ345678).mp3
│   └── [月乃] 视频ASMR.mp4
└── 未分类/
    └── unknown_file.flac
```

**设计要点：**

- 音频和视频放在同一作者目录下，不做二次分类
- 未匹配到作者的文件放入 `未分类/` 目录
- 文件名冲突自动加序号（如 `作品 (2).flac`）
- 移动文件时同步移动封面等关联文件

### 4.6 去重服务（Dedup Service）

**职责：** 检测和管理重复文件。

```python
class DedupService:
    async def find_duplicates(
        self,
        method: str = "all"
    ) -> list[DuplicateGroup]:
        """使用指定方法查找重复文件"""
        ...

    async def _find_by_hash(self) -> list[DuplicateGroup]:
        """通过 SHA256 哈希查找完全相同的文件"""
        ...

    async def _find_by_rj_id(self) -> list[DuplicateGroup]:
        """通过 RJ 号查找重复文件"""
        ...

    async def _compute_quality_score(self, media: Media) -> int:
        """计算质量分数，用于去重推荐"""
        ...

    async def resolve(
        self,
        group_id: str,
        keep_id: int,
        action: str = "move"
    ) -> dict:
        """处理重复文件分组"""
        ...
```

**质量评分计算：**

| 因素 | 权重 |
|------|------|
| 格式（FLAC > MP3） | 40 |
| 比特率 | 25 |
| 是否有封面 | 15 |
| 是否有元数据 | 10 |
| 文件大小 | 10 |

### 4.7 封面服务（Cover Service）

**职责：** 管理媒体封面图片。

```python
class CoverService:
    SUPPORTED_NAMES = [
        "cover.jpg", "folder.jpg", "front.jpg",
        "poster.jpg", "thumb.jpg"
    ]

    async def find_local_cover(self, media_path: str) -> str | None:
        """在媒体目录中查找封面图片"""
        ...

    async def extract_from_video(
        self,
        video_path: str,
        timestamp: float = 10.0
    ) -> str:
        """从视频中截取帧作为封面"""
        ...

    async def optimize_cover(
        self,
        image_path: str,
        max_size: tuple = (1000, 1000)
    ) -> str:
        """调整封面图片尺寸并优化"""
        ...

    async def generate_poster(self, cover_path: str) -> str:
        """从封面生成海报图"""
        ...
```

---

## 五、配置设计

### 5.1 配置文件（config/default.yml）

```yaml
# ASMR 媒体整理中心配置

# 目录设置
directories:
  download: /media/downloads   # 下载目录（监控此目录的新文件）
  library: /media/library     # 整理目录（按作者归档的输出目录）

# 扫描设置
scan:
  recursive: true              # 是否递归扫描子目录
  watch_enabled: true          # 是否启用下载目录实时监听
  stable_seconds: 10           # 文件大小稳定多少秒后判定下载完成
  check_interval: 5            # 检查下载完成的间隔（秒）

# 支持的媒体格式
formats:
  audio:
    - mp3
    - flac
    - wav
    - m4a
    - opus
    - ogg
  video:
    - mp4
    - mkv
    - avi
    - mov
    - webm

# 重命名设置
rename:
  audio_pattern: "[{cv}] {title} ({rj_id})"    # 音频命名模式
  video_pattern: "[{creator}] {title}"          # 视频命名模式
  sanitize_spaces: true                         # 是否清理多余空格
  max_filename_length: 200                      # 文件名最大长度
  create_subdirs: true                          # 是否创建子目录

# AI 设置
ai:
  enabled: false               # 是否启用 AI
  provider: ollama             # AI 提供商
  model: qwen2:7b             # 使用的模型
  ollama_url: http://localhost:11434  # Ollama 服务地址
  tag_inference: true          # 是否启用标签推断
  ocr_enabled: false           # 是否启用 OCR
  ocr_engine: paddleocr       # OCR 引擎

# 整理输出设置
organize:
  unclassified_dir: "未分类"   # 未匹配作者的文件存放目录
  generate_nfo: false          # 是否生成 NFO 文件（Phase 2）
  copy_covers: true            # 是否移动封面文件

# 封面设置
cover:
  search_names:                # 封面文件名搜索列表
    - cover.jpg
    - folder.jpg
    - front.jpg
  max_size: 1000               # 封面最大尺寸（像素）
  extract_from_video: true     # 是否从视频截取封面
  extract_timestamp: 10.0      # 截取时间点（秒）

# 去重设置
dedup:
  auto_detect: true            # 是否自动检测重复
  methods:                     # 去重方法
    - hash
    - rj_id
  keep_strategy: highest_quality  # 保留策略：保留最高质量

# 数据库设置
database:
  url: sqlite:///data/asmr_manager.db
  echo: false                  # 是否输出 SQL 日志

# 服务器设置
server:
  host: 0.0.0.0
  port: 8080
  workers: 1
  cors_origins:                # CORS 允许的来源
    - http://localhost:5173
    - http://localhost:3000

# 日志设置
logging:
  level: INFO                  # 日志级别
  file: data/logs/app.log     # 日志文件路径
  max_size_mb: 10              # 单个日志文件最大大小
  backup_count: 5              # 保留的日志备份数量
```

### 5.2 环境变量

```bash
# .env.example
APP_ENV=production
DATABASE_URL=sqlite:///data/asmr_manager.db
DOWNLOAD_DIR=/media/downloads
LIBRARY_DIR=/media/library
OLLAMA_URL=http://localhost:11434
AI_MODEL=qwen2:7b
LOG_LEVEL=INFO
```

---

## 六、错误处理

### 6.1 异常层级

```python
class AppException(Exception):
    """应用基础异常"""
    code: int = 500
    message: str = "服务器内部错误"

class NotFoundException(AppException):
    code = 404
    message = "资源未找到"

class ValidationException(AppException):
    code = 400
    message = "参数验证失败"

class ScanException(AppException):
    code = 500
    message = "扫描错误"

class MetadataException(AppException):
    code = 500
    message = "元数据处理错误"

class RenameException(AppException):
    code = 400
    message = "重命名操作错误"

class AIException(AppException):
    code = 503
    message = "AI 服务不可用"
```

### 6.2 错误响应格式

```json
{
    "code": 400,
    "message": "参数验证失败",
    "detail": "无效的重命名模式：缺少必需字段 {title}",
    "errors": [
        {
            "field": "pattern",
            "message": "必须包含至少一个变量"
        }
    ]
}
```

---

## 七、性能设计

### 7.1 性能目标

| 指标 | 目标值 |
|------|--------|
| 扫描速度 | 1000 文件/分钟 |
| 哈希计算速度 | 500 MB/s |
| API 响应时间（p95） | < 200ms |
| 数据库查询（p95） | < 50ms |
| 前端加载时间 | < 2s |
| 空闲内存占用 | < 200MB |
| 扫描时内存占用 | < 500MB |

### 7.2 优化策略

**数据库优化：**

- 索引字段：`rj_id`、`creator`、`cv`、`media_type`、`status`、`file_hash`
- 启用 WAL 模式支持并发读取
- 批量插入（每事务 100 条记录）
- 连接池管理

**扫描优化：**

- 所有文件操作使用异步 I/O
- 并行哈希计算（可配置工作线程数）
- 增量扫描基于文件修改时间
- 跳过未变化的文件

**API 优化：**

- 所有列表接口支持分页
- 响应压缩（gzip）
- 静态资源使用 ETag 缓存
- 使用 WebSocket 替代轮询获取实时更新

**前端优化：**

- 大列表使用虚拟滚动
- 图片懒加载
- 搜索输入防抖
- 乐观 UI 更新

---

## 八、安全设计

### 8.1 安全原则

- **默认仅本地运行：** 无需外部网络访问
- **无云依赖：** 所有处理在本地完成
- **第一阶段无用户认证：** 设计为单用户本地部署
- **输入验证：** 所有用户输入通过 Pydantic 验证
- **路径遍历防护：** 所有文件路径经过验证和清理
- **禁止任意代码执行：** 不使用 eval()、exec()，防止 shell 注入

### 8.2 文件系统安全

```python
def validate_path(requested_path: str, allowed_roots: list[str]) -> str:
    """确保路径在允许的目录范围内"""
    real_path = os.path.realpath(requested_path)
    for root in allowed_roots:
        if real_path.startswith(os.path.realpath(root)):
            return real_path
    raise ValidationException("路径不在允许的目录中")
```

### 8.3 CORS 配置

```python
CORS_ORIGINS = [
    "http://localhost:5173",   # Vite 开发服务器
    "http://localhost:3000",   # 生产环境前端
    "http://localhost:8080",   # 同源
]
```

---

## 九、测试策略

### 9.1 测试结构

```
tests/
├── unit/
│   ├── test_rule_engine.py      # 模式匹配测试
│   ├── test_hash_utils.py       # 哈希计算测试
│   ├── test_text_utils.py       # 文本处理测试
│   └── test_rename_patterns.py  # 重命名模式测试
├── integration/
│   ├── test_scanner.py          # 端到端扫描测试
│   ├── test_metadata.py         # 元数据读写测试
│   ├── test_api_media.py        # 媒体 API 测试
│   └── test_api_rename.py       # 重命名 API 测试
├── fixtures/
│   ├── sample_audio.flac        # 测试音频样本
│   ├── sample_video.mp4         # 测试视频样本
│   └── test_filenames.txt       # 测试文件名集合
└── conftest.py
```

### 9.2 关键测试用例

**规则引擎测试：**

```python
def test_parse_rj_id():
    engine = RuleEngine()
    result = engine.parse("[RJ123456] 深夜耳搔治愈.flac")
    assert result["rj_id"] == "RJ123456"

def test_parse_cv():
    engine = RuleEngine()
    result = engine.parse("[CV.涼花みなせ] 作品.flac")
    assert result["cv"] == "涼花みなせ"

def test_parse_complex_filename():
    engine = RuleEngine()
    result = engine.parse("[RJ123456][CV.涼花みなせ][24bit] 深夜耳搔治愈.flac")
    assert result["rj_id"] == "RJ123456"
    assert result["cv"] == "涼花みなせ"
    assert result["title"] == "深夜耳搔治愈"
```

**扫描器测试：**

```python
async def test_incremental_scan(scanner, sample_dir):
    # 第一次扫描：发现所有文件
    job1 = await scanner.scan_directory(sample_dir, scan_type="full")
    assert job1.new_files == 10

    # 第二次扫描：无新文件
    job2 = await scanner.scan_directory(sample_dir, scan_type="incremental")
    assert job2.new_files == 0

    # 添加新文件后再次扫描
    create_test_file(sample_dir, "new.flac")
    job3 = await scanner.scan_directory(sample_dir, scan_type="incremental")
    assert job3.new_files == 1
```

---

## 十、部署方案

### 10.1 Docker Compose

```yaml
version: "3.8"

services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ${DOWNLOAD_DIR}:/media/downloads    # 下载目录（读写）
      - ${LIBRARY_DIR}:/media/library      # 整理目录（读写）
    environment:
      - DATABASE_URL=sqlite:///data/asmr_manager.db
      - DOWNLOAD_DIR=/media/downloads
      - LIBRARY_DIR=/media/library
      - OLLAMA_URL=http://ollama:11434
      - LOG_LEVEL=INFO
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    profiles:
      - ai

volumes:
  ollama_data:
```

### 10.2 后端 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    mediainfo \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY backend/ .

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 10.3 前端 Dockerfile

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
```

### 10.4 Nginx 配置

```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 十一、开发流程

### 11.1 开发环境搭建

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 11.2 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述信息"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 11.3 代码质量检查

```bash
# 后端
ruff check .
ruff format .
mypy app/

# 前端
npm run lint
npm run type-check
```

---

## 十二、监控与日志

### 12.1 日志格式

```json
{
    "timestamp": "2026-05-18T10:00:00Z",
    "level": "INFO",
    "module": "scanner",
    "message": "文件已处理",
    "file_path": "/media/asmr/[RJ123456] 深夜耳搔治愈.flac",
    "duration_ms": 45,
    "extra": {
        "hash": "sha256:abc123...",
        "media_type": "audio"
    }
}
```

### 12.2 健康检查

```
GET /api/v1/health

响应：
{
    "status": "healthy",
    "version": "1.0.0",
    "database": "connected",
    "ai_service": "available",
    "uptime_seconds": 3600
}
```

---

## 十三、Phase 1 MVP 范围

### 13.1 包含功能

| 功能 | 优先级 |
|------|--------|
| 文件扫描（全量 + 增量） | P0 |
| 文件名解析（RJ 号、CV、标题） | P0 |
| 音频元数据读写（Mutagen） | P0 |
| 视频元数据读取（pymediainfo） | P0 |
| 按模式自动重命名 | P0 |
| Plex 目录结构输出 | P0 |
| 基础标签管理 | P0 |
| 作者关键词规则管理（CRUD） | P0 |
| 作者自动匹配（扫描时自动赋值） | P0 |
| Web UI（媒体列表、详情、设置） | P0 |
| Docker 部署 | P0 |
| 数据库（SQLite + 迁移） | P0 |

### 13.2 不包含功能（Phase 2+）

| 功能 | 阶段 |
|------|------|
| AI 标签推断（Ollama） | 2 |
| OCR 识别（PaddleOCR） | 2 |
| 文件去重 | 2 |
| 封面管理 | 2 |
| 文件监听（实时） | 2 |
| WebSocket 进度推送 | 2 |
| NFO 文件生成 | 2 |
| 批量操作 UI | 2 |
| 自动标签学习 | 3 |
| 语音识别 | 3 |
