# ASMR Media Manager

ASMR 媒体整理中心 — 面向 Plex/NAS 的 ASMR 专用媒体管理系统。

将混乱无序的 ASMR 音频/视频文件自动整理为结构化媒体库，写入元数据标签，生成封面，通知 Plex 刷新，实现开箱即用的播放体验。

---

## 功能特性

### 核心流程

```
下载目录（杂乱文件）
    ↓ 目录监控 / 手动扫描
解析文件名（提取 RJ号、CV、标题）
    ↓
DLsite API 反查元数据（标题、社团、声优、标签、封面）
    ↓
手动作者规则匹配（最高优先级）
    ↓
整理到 library/作者/[RJ号] 标题/
    ↓
写回音频标签（title/album/artist/cover）
    ↓
下载封面图
    ↓
通知 Plex 刷新媒体库
    ↓
Plex 正确识别并播放
```

### 功能列表

| 功能 | 说明 |
|------|------|
| **文件扫描** | 全量/增量扫描，SHA256 哈希去重，WebSocket 实时进度 |
| **智能解析** | 从文件名+目录名提取 RJ/DL 号、CV、标题、语言、平台 |
| **DLsite 集成** | 根据 RJ 号自动获取标题、社团、声优、标签、封面，支持代理 |
| **作者规则** | 关键词匹配自动识别创作者，支持 5 种匹配方式和优先级 |
| **目录整理** | 三级结构 `作者/[RJ号] 标题/文件`，Plex 音乐库友好 |
| **标签写入** | 支持 MP3/FLAC/M4A/OPUS/OGG，含封面嵌入 |
| **封面管理** | 自动下载 DLsite 封面，嵌入音频文件+保存为 cover.jpg |
| **Plex 集成** | 整理后自动通知 Plex 刷新，支持测试连接 |
| **目录监控** | 监控多个目录，三层检测判定下载完成（临时文件/文件锁/大小稳定） |
| **批量操作** | 批量整理、批量 DLsite 补全、批量写标签 |
| **AI 分析** | 接入 OpenAI 兼容 API，智能分析文件名填充元数据 |
| **元数据编辑** | 手动编辑标题、作者、社团、CV、描述等字段 |

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
# 后端 API：http://localhost:8080/docs
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

# 首次运行：初始化数据库
python migrate.py

# 启动后端
uvicorn app.main:app --reload --port 8080

# --- 前端 ---
cd frontend
npm install
npm run dev
```

- 前端开发服务器：http://localhost:5173
- 后端 API 文档：http://localhost:8080/docs

---

## 配置说明

### 环境变量（.env）

`.env` 用于初始化部署配置。通过设置页面修改的值会保存到数据目录中的
`runtime_settings.json`，并覆盖环境变量；该文件随 Docker 的 `data` 挂载持久化，应与数据库一同备份。

```env
# 目录
DOWNLOAD_DIR=/media/downloads     # 下载目录（扫描来源）
LIBRARY_DIR=/media/library        # 整理目录（输出目标）
WATCH_DIRS=["/media/extra1"]      # 额外监控目录（JSON 数组）

# 扫描
WATCH_ENABLED=true                # 启用目录监控
WATCH_AUTO_ORGANIZE=true          # 监控到新文件后自动整理

# DLsite
DLSITE_ENABLED=true               # 启用 DLsite API
DLSITE_PROXY=http://127.0.0.1:7890  # 代理地址（大陆网络需要）

# Plex
PLEX_URL=http://192.168.1.100:32400  # Plex Server 地址
PLEX_TOKEN=your-plex-token           # Plex Token
PLEX_AUTO_REFRESH=true               # 整理后自动刷新 Plex

# AI（可选）
AI_ENABLED=false
AI_API_URL=https://api.openai.com/v1
AI_API_KEY=sk-your-key
AI_MODEL=gpt-4o-mini
```

### DLsite 配置

DLsite 是日本最大的同人内容销售平台，ASMR 作品的主要来源。启用后系统会根据 RJ 号自动获取：

- 作品标题
- 社团名称
- 声优列表
- 标签
- 封面图
- 作品描述

**大陆用户需要配置代理**才能访问 DLsite API。

### Plex 配置

1. 获取 Plex Token：
   - 方法一：Plex 设置 → 网络 → 显示高级设置 → X-Plex-Token
   - 方法二：浏览器打开 Plex → F12 → 网络 → 任意请求的 X-Plex-Token 参数
2. 在设置页面填写 Plex 地址和 Token
3. 点击「测试 Plex 连接」验证配置

---

## 使用指南

### 1. 首次使用

1. 启动服务后，进入 **设置** 页面
2. 确认下载目录和整理目录
3. 配置 DLsite（可选，建议开启）
4. 配置 Plex（可选，如果需要自动刷新）
5. 点击「保存设置」

### 2. 扫描文件

进入 **扫描管理** 页面：

1. 输入扫描路径（如 `/media/downloads`）
2. 选择扫描类型：
   - **全量扫描**：扫描所有文件
   - **增量扫描**：跳过已入库的文件
3. 勾选「扫描后自动整理」（推荐）
4. 点击「开始扫描」

扫描过程中可以实时查看进度：
- 总文件数
- 已处理数
- 新文件数
- 已整理数
- 错误数

### 3. 整理文件

整理操作会将文件从下载目录移动到结构化的媒体库目录：

```
整理前（下载目录）：
/media/downloads/
├── 花花 - 深夜哄睡.mp3
├── 01.mp3
├── [RJ123456] 某作品/
│   └── track01.flac

整理后（媒体库）：
/media/library/
├── 花花/
│   └── 深夜哄睡/
│       └── 花花 - 深夜哄睡.mp3
├── 未分类/
│   └── 01.mp3
└── 某社团/
    └── [RJ123456] 某作品/
        ├── track01.flac
        └── cover.jpg
```

**自动整理**：开启后，扫描完成自动整理到媒体库。

**手动整理**：
1. 在媒体列表页勾选文件
2. 点击「批量整理」
3. 确认目标路径后执行

**重新整理**：对已入库但目录结构不对的文件，使用「批量整理」会自动迁移到新结构。

### 4. 补全元数据

对于缺少信息的文件，可以通过以下方式补全：

**DLsite 补全**（推荐）：
1. 确保文件有 RJ 号（文件名或目录名中包含 `RJ123456`）
2. 在媒体列表页勾选文件
3. 点击「DLsite 补全」
4. 系统会自动获取标题、社团、声优、标签、封面

**AI 分析**：
1. 进入媒体详情页
2. 点击「AI 分析」
3. AI 会根据文件名推断元数据

**手动编辑**：
1. 进入媒体详情页
2. 直接编辑标题、作者、CV、描述等字段
3. 点击「保存」

### 5. 作者规则

作者规则用于自动匹配创作者信息，适用于没有 RJ 号的国内主播文件。

**创建规则**：
1. 进入 **作者规则** 页面
2. 点击「添加规则」
3. 填写：
   - **关键词**：如 `花花`、`某社团名`
   - **匹配方式**：包含（最常用）/ 精确 / 前缀 / 后缀 / 正则
   - **匹配目标**：文件名 / 目录名 / 全部
   - **创作者/社团/CV**：匹配后自动填充的值
   - **优先级**：数字越大越优先（手动规则永远覆盖 DLsite 结果）

**测试规则**：
- 点击规则行的「测试」按钮
- 查看匹配了多少文件和匹配样本

**批量创建**：
- 通过 API `POST /api/v1/author-rules/batch` 批量导入

### 6. 写入标签

标签写入会将元数据永久嵌入音频文件：

1. 在媒体列表页勾选文件
2. 点击「写入标签」
3. 系统会写入以下标签：
   - **标题**（title）
   - **专辑**（album）— 格式：`[RJ123456] 标题`
   - **艺术家**（artist）— 创作者名
   - **专辑艺术家**（album_artist）— 社团名
   - **流派**（genre）— `ASMR`
   - **封面图** — 嵌入到文件内

写入后，Plex、foobar2000、MusicBee 等播放器都能正确显示信息。

### 7. Plex 播放

整理完成后：

1. 在 Plex 中添加音乐库，指向 `/media/library` 目录
2. Plex 会自动扫描并识别：
   - 按 **艺术家** 分组
   - 按 **专辑**（`[RJ号] 标题`）分组
   - 显示 **封面图**
   - 显示 **标题、艺术家、流派** 等信息
3. 如果开启了「自动刷新」，整理后 Plex 会自动发现新文件

**Plex 库类型建议**：选择「音乐库」，扫描器选「Plex Music Scanner」。

---

## 目录结构说明

### 整理后的目录结构

```
library/
├── 花花/                              ← 作者目录
│   ├── [RJ123456] 深夜哄睡/           ← 作品目录
│   │   ├── 深夜哄睡 (RJ123456).mp3    ← 音频文件
│   │   └── cover.jpg                  ← 封面图
│   └── [RJ789012] 午后小憩/
│       ├── track01.flac
│       ├── track02.flac
│       └── cover.jpg
├── 某社团/
│   └── [RJ345678] 某作品/
│       └── ...
└── 未分类/                            ← 没有识别到作者的文件
    └── mystery.mp3
```

### 作者目录命名规则

优先级从高到低：
1. 手动作者规则匹配的 `creator`
2. DLsite API 返回的 `creator`
3. 文件内置元数据的 `artist`
4. `cv`（声优）
5. `circle`（社团）
6. `未分类`

### 作品目录命名规则

格式：`[RJ号] 标题`

- 如果有 RJ 号：`[RJ123456] 深夜哄睡`
- 如果没有 RJ 号：直接用标题
- 如果标题也没有：用原始文件名（去掉扩展名）

---

## 下载监听机制

系统通过三层检测判断文件是否下载完成：

| 层级 | 检测内容 | 说明 |
|------|---------|------|
| 第一层 | 临时文件检测 | 检查是否存在 `.part`、`.tmp`、`.crdownload`、`.aria2` 等临时文件 |
| 第二层 | 文件锁检测 | 尝试以独占模式打开文件，检查是否被下载工具占用 |
| 第三层 | 大小稳定检测 | 文件大小在 N 秒内（默认 10 秒）无变化 |

三层均通过后，才会触发自动处理流程。

### 支持的临时文件格式

`.part`、`.tmp`、`.crdownload`、`.downloading`、`.aria2`、`.bt`、`.partial`、`.!ut`、`.bc!`

### 多目录监控

在设置中可以配置多个监控目录：

```env
DOWNLOAD_DIR=/media/downloads
WATCH_DIRS=["/media/bilibili", "/media/recordings"]
```

所有目录中的新文件都会被自动检测和处理。

---

## 元数据优先级

当多个来源都有数据时，按以下优先级合并（高优先级覆盖低优先级）：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1（最高） | 手动作者规则 | 用户配置的关键词匹配 |
| 2 | DLsite API | 根据 RJ 号自动获取 |
| 3 | 文件名解析 | 正则从文件名/目录名提取 |
| 4（最低） | 文件内置元数据 | mutagen/pymediainfo 读取的标签 |

**特殊规则**：
- `title`：DLsite > 文件名解析 > 文件元数据
- `creator`：手动规则 > DLsite > 文件元数据
- `cv`：文件名解析 > DLsite（因为国内文件 CV 信息通常在文件名里）

---

## 支持的格式

| 类型 | 格式 |
|------|------|
| 音频 | MP3, FLAC, WAV, M4A, OPUS, OGG |
| 视频 | MP4, MKV, AVI, MOV, WEBM |

### 标签写入支持

| 格式 | 标签格式 | 封面支持 |
|------|---------|---------|
| MP3 | ID3v2 (TIT2/TALB/TPE1/TPE2/TCON) | ✅ APIC |
| FLAC | Vorbis (TITLE/ALBUM/ARTIST/ALBUMARTIST) | ✅ PICTURE |
| M4A | MP4 (©nam/©alb/©ART/aART) | ✅ covr |
| OPUS | Vorbis (title/album/artist/albumartist) | ✅ metadata_block_picture |
| OGG | Vorbis (同 OPUS) | ✅ metadata_block_picture |

---

## API 文档

启动后端后访问 Swagger UI：

```
http://localhost:8080/docs
```

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/scan` | 启动扫描（支持 organize 参数自动整理） |
| GET | `/api/v1/scan/jobs` | 扫描任务列表 |
| GET | `/api/v1/scan/{job_id}` | 扫描任务状态 |
| GET | `/api/v1/media` | 媒体列表（分页、筛选、unclassified 过滤） |
| GET | `/api/v1/media/stats` | 媒体统计数据 |
| GET | `/api/v1/media/{id}` | 媒体详情 |
| PATCH | `/api/v1/media/{id}` | 更新媒体信息 |
| POST | `/api/v1/media/organize/preview` | 整理预览 |
| POST | `/api/v1/media/organize/execute` | 执行整理 |
| POST | `/api/v1/media/reorganize` | 重新整理（迁移旧结构） |
| POST | `/api/v1/metadata/generate` | 生成 NFO 文件 |
| POST | `/api/v1/metadata/write-tags` | 写入音频标签 |
| POST | `/api/v1/metadata/ai-analyze` | AI 分析元数据 |
| POST | `/api/v1/metadata/fetch-dlsite` | DLsite 批量补全（并发） |
| GET | `/api/v1/author-rules` | 作者规则列表 |
| POST | `/api/v1/author-rules` | 创建规则 |
| POST | `/api/v1/author-rules/scan-test` | 测试规则匹配 |
| POST | `/api/v1/author-rules/apply` | 应用规则到已有媒体 |
| POST | `/api/v1/rename/preview` | 重命名预览 |
| POST | `/api/v1/rename/execute` | 执行重命名 |
| POST | `/api/v1/rename/rollback` | 回滚重命名 |
| GET | `/api/v1/settings` | 获取设置 |
| PATCH | `/api/v1/settings` | 更新设置 |
| POST | `/api/v1/settings/test-plex` | 测试 Plex 连接 |
| WS | `/api/v1/ws/scan/{job_id}` | 扫描进度实时推送 |

---

## 数据库迁移

启动时会自动为 SQLite 数据库添加应用所需的缺失列。若需要手动执行升级，也可以运行迁移脚本：

```bash
cd backend
python migrate.py
```

该脚本会自动检测并添加缺失的列，不会修改已有数据。

---

## 常见问题

### Q: 扫描后没有识别出 RJ 号？

A: 系统从以下位置查找 RJ 号：
- 文件名（如 `RJ123456.mp3`）
- 父目录名（如 `RJ123456/track01.mp3`）
- 祖父目录名（向上查找 2 级）
- 方括号包裹的数字（如 `[123456].mp3`）

如果都没有，说明文件确实没有 RJ 号信息。可以通过手动编辑或 AI 分析补充。

### Q: DLsite 补全失败？

A: 常见原因：
1. **网络问题**：大陆用户需要配置代理（设置 → DLsite → 代理地址）
2. **RJ 号无效**：确认文件有正确的 RJ 号
3. **请求过于频繁**：系统已内置限流（默认每秒 1 次），稍后重试

### Q: Plex 看不到新文件？

A: 检查以下几点：
1. 确认 Plex 媒体库指向了 `library_dir` 目录
2. 确认 Plex 媒体库类型是「音乐库」
3. 如果配置了 Plex 自动刷新，检查设置中的 Plex 地址和 Token 是否正确
4. 手动在 Plex 中点击「扫描库文件」

### Q: 扫描速度很慢？

A: 主要瓶颈是 DLsite API 调用。每个有 RJ 号的文件都会请求一次 DLsite：
- 已内置缓存（默认 30 分钟），重复扫描不会重复请求
- 已支持并发请求（最多 5 个并发）
- 如果不需要 DLsite，可以在设置中关闭

### Q: 文件整理后原目录还有文件？

A: 整理操作是**移动**（不是复制），原目录的文件会被移走。如果原目录还有残留：
- 可能是不支持的格式（如 `.lrc` 歌词文件）
- 可能是封面图片等关联文件
- 这些不会被自动移动

### Q: 如何备份？

A: 需要备份以下内容：
1. 数据库文件：`backend/data/asmr_manager.db`
2. 配置文件：`.env`
3. 媒体库目录：`library_dir`（整理后的文件）

---

## 项目结构

```
asmr_media_manager/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── media.py        # 媒体 CRUD + 整理
│   │   │   ├── scan.py         # 扫描任务
│   │   │   ├── metadata.py     # 元数据操作
│   │   │   ├── author_rules.py # 作者规则
│   │   │   ├── rename.py       # 重命名
│   │   │   ├── tags.py         # 标签管理
│   │   │   ├── settings.py     # 设置
│   │   │   └── ws.py           # WebSocket
│   │   ├── models/             # SQLAlchemy 模型
│   │   ├── schemas/            # Pydantic 验证
│   │   ├── services/           # 业务逻辑
│   │   │   ├── scanner.py      # 扫描服务
│   │   │   ├── rule_engine.py  # 文件名解析引擎
│   │   │   ├── dlsite_service.py   # DLsite API
│   │   │   ├── author_matcher.py   # 作者匹配
│   │   │   ├── organize_service.py # 目录整理
│   │   │   ├── metadata_service.py # 标签读写
│   │   │   ├── cover_service.py    # 封面管理
│   │   │   ├── plex_service.py     # Plex 集成
│   │   │   └── watcher.py      # 目录监控
│   │   ├── core/               # 常量、异常、中间件
│   │   └── utils/              # 工具函数
│   ├── data/                   # SQLite 数据库
│   ├── migrate.py              # 数据库迁移脚本
│   └── requirements.txt
├── frontend/                   # Vue 3 前端
│   └── src/
│       ├── api/                # Axios API 层
│       ├── stores/             # Pinia 状态管理
│       ├── views/              # 页面组件
│       ├── types/              # TypeScript 类型
│       └── router/             # 路由配置
├── config/                     # 应用配置
│   └── default.yml
├── docker/                     # Docker 配置
├── docker-compose.yml
└── .env
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy + SQLite |
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| 音频标签 | Mutagen |
| 视频信息 | pymediainfo |
| HTTP 客户端 | httpx |
| 目录监控 | watchdog |
| 部署 | Docker Compose + Nginx |

---

## 许可证

MIT License
