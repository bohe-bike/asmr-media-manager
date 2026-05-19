# ASMR 媒体整理中心（ASMR Media Manager）

## 一、项目概述

### 1.1 项目背景

当前针对 ASMR / VTuber / 同人音视频 的媒体管理生态非常碎片化。

现有工具：

- Plex
- Jellyfin
- FileBot
- Mp3tag
- tinyMediaManager
- Lidarr
- Sonarr

都只能解决部分问题。

而 ASMR 媒体存在以下特点：

- 文件命名极度混乱
- 缺乏标准数据库
- 多语言（中 / 日 / 英）
- 同时存在音频与视频
- RJ / DLsite 体系特殊
- VTuber / Patreon / YouTube 来源复杂
- Metadata 不统一
- Plex 无法自动识别
- NSFW 内容无法依赖云端 AI

因此，需要一个：

> 面向 Plex / NAS / 本地媒体库 的 ASMR 专用媒体整理系统。

---

# 二、项目目标

## 2.1 核心目标

实现：

- 自动扫描媒体目录
- 自动识别文件信息
- 自动分类音频 / 视频
- 自动重命名
- 自动生成 Plex 友好的目录结构
- 自动写入 Metadata
- 自动封面管理
- 自动标签管理
- 自动去重
- AI 辅助内容理解

---

## 2.2 非目标（第一阶段不做）

以下内容不属于第一阶段：

- 媒体播放功能
- 视频转码平台
- 在线流媒体
- 云端 AI 分析
- 多人协作
- 社区资源共享
- 公网分享
- 深度成人内容检测

---

# 三、用户画像

## 3.1 目标用户

### 1. Plex / Jellyfin 用户

特点：

- 使用 NAS
- 收藏大量媒体
- 注重媒体库整洁
- 有长期维护需求

---

### 2. ASMR 收藏用户

特点：

- DLsite / RJ 资源
- VTuber ASMR
- Patreon 内容
- YouTube ASMR
- 音频与视频混合

---

### 3. 本地媒体爱好者

特点：

- Docker 用户
- 自托管
- 自动化需求高
- 不希望依赖云服务

---

# 四、核心功能需求（PRD）

# 4.1 媒体扫描

## 功能描述

扫描用户指定目录。

支持：

- 递归扫描
- 增量扫描
- 定时扫描
- 实时监听

---

## 支持媒体格式

### 音频

- mp3
- flac
- wav
- m4a
- opus
- ogg

### 视频

- mp4
- mkv
- avi
- mov
- webm

---

## 输出结果

生成：

- 文件索引
- hash
- 基础 Metadata
- 媒体类型

---

# 4.2 文件识别引擎

## 功能描述

从文件名、目录名、封面中提取媒体信息。

---

## 识别信息

| 字段 | 示例 |
|---|---|
| RJ号 | RJ123456 |
| 标题 | 深夜耳搔 |
| CV | 涼花みなせ |
| 社团 | CircleName |
| 平台 | DLsite |
| 类型 | Audio / Video |
| 标签 | 耳搔 / 助眠 |
| 语言 | ja / zh / en |

---

## 输入示例

```txt
[RJ123456][CV.涼花みなせ][24bit] 深夜耳搔治愈
```

---

## 输出示例

```json
{
  "rj_id": "RJ123456",
  "cv": "涼花みなせ",
  "title": "深夜耳搔治愈",
  "media_type": "audio",
  "language": "ja"
}
```

---

# 4.3 自动分类系统

## 功能描述

根据规则与 AI 推断自动分类。

---

## 一级分类

```txt
Audio/
Video/
VTuber/
真人/
NSFW/
```

---

## 二级分类

按：

- CV
- 创作者
- 社团
- 平台

---

## 三级分类

按具体作品。

---

# 4.4 自动重命名

## 功能描述

统一媒体命名规则。

---

## 音频命名规则

```txt
[CV] 标题 (RJ号)
```

示例：

```txt
[涼花みなせ] 深夜耳搔治愈 (RJ123456)
```

---

## 视频命名规则

```txt
[创作者] 标题
```

示例：

```txt
[Gibi ASMR] Cranial Nerve Exam
```

---

## 批量预览

支持：

- 重命名预览
- 冲突检测
- 回滚

---

# 4.5 Metadata 管理

## 功能描述

生成 Plex/Jellyfin 可读取 Metadata。

---

## 音频 Metadata

写入：

| 字段 | 内容 |
|---|---|
| Artist | CV |
| Album | 作品名 |
| Genre | 标签 |
| Comment | RJ号 |

---

## 视频 Metadata

生成：

```txt
poster.jpg
fanart.jpg
nfo
```

---

# 4.6 封面管理

## 功能描述

自动识别与管理封面。

---

## 支持来源

- 本地 cover.jpg
- 视频截图
- OCR 提取
- 用户手动上传

---

## 输出

统一：

```txt
cover.jpg
poster.jpg
background.jpg
```

---

# 4.7 标签系统

## 功能描述

统一媒体标签体系。

---

## 标签示例

```txt
耳搔
舔耳
助眠
耳语
女友
御姐
雨声
剧情向
VTuber
真人
```

---

## 标签来源

- 文件名
- AI 推断
- 用户手动编辑

---

# 4.8 去重系统

## 功能描述

检测重复媒体。

---

## 去重维度

| 类型 | 方法 |
|---|---|
| 文件hash | SHA256 |
| 音频指纹 | chromaprint |
| 视频hash | perceptual hash |
| RJ号 | 规则匹配 |

---

## 保留策略

优先保留：

- FLAC
- 高码率
- 高分辨率
- 完整 Metadata

---

# 4.9 AI 辅助分析

## 功能描述

使用本地 AI 模型辅助媒体理解。

---

## AI 功能

### 1. 标题理解

输入：

```txt
【睡前3小时】超近距离耳语♡
```

输出：

```json
{
  "tags": ["耳语", "助眠"],
  "duration_type": "long_sleep"
}
```

---

### 2. 自动标签

自动生成：

- 助眠
- 耳搔
- 雨声
- 女友

---

### 3. OCR

识别：

- RJ号
- CV
- 标题

---

## AI 原则

- 完全本地运行
- 不上传用户媒体
- 不依赖云 API
- AI 仅辅助

---

# 五、系统架构设计

# 5.1 总体架构

```txt
Frontend
   ↓
Backend API
   ↓
Media Scanner
   ↓
Rule Engine
   ↓
AI Service
   ↓
Metadata Engine
   ↓
Plex Output
```

---

# 5.2 技术选型

## 后端

### Python

原因：

- ffmpeg 生态成熟
- AI 生态完善
- Metadata 库丰富
- Plex API 支持完善

---

## Web Framework

### FastAPI

原因：

- 异步性能优秀
- Swagger 自动生成
- Docker 友好
- 开发速度快

---

## 前端

### Vue 3 + TypeScript

原因：

- 管理后台适合
- 开发效率高
- 生态成熟

---

## 数据库

### SQLite（第一阶段）

后期可升级：

- PostgreSQL

---

## AI 推理

### 本地 LLM

推荐：

- Qwen
- Gemma
- Phi

---

## OCR

推荐：

- PaddleOCR

---

# 六、模块设计

# 6.1 扫描模块

## 功能

- 文件遍历
- hash 计算
- 文件监听

---

## 技术

- watchdog
- asyncio

---

# 6.2 规则引擎

## 功能

解析：

- 文件名
- 目录名
- 正则规则

---

## 示例规则

```regex
RJ\d+
```

---

# 6.3 Metadata 模块

## 音频

库：

- mutagen

---

## 视频

库：

- pymediainfo
- ffprobe

---

# 6.4 AI 模块

## 功能

- 标签推断
- 文本理解
- OCR

---

## 运行模式

- 本地模型
- 离线运行

---

# 6.5 Plex 输出模块

## 功能

输出标准目录。

---

## 输出示例

```txt
ASMR Audio/
└── [涼花みなせ] 深夜耳搔治愈 (RJ123456)
```

---

# 七、数据库设计

# 7.1 media 表

| 字段 | 类型 |
|---|---|
| id | INTEGER |
| path | TEXT |
| hash | TEXT |
| media_type | TEXT |
| title | TEXT |
| creator | TEXT |
| rj_id | TEXT |
| language | TEXT |
| created_at | DATETIME |

---

# 7.2 tags 表

| 字段 | 类型 |
|---|---|
| id | INTEGER |
| name | TEXT |

---

# 7.3 media_tags 表

| 字段 | 类型 |
|---|---|
| media_id | INTEGER |
| tag_id | INTEGER |

---

# 八、API 设计

# 8.1 扫描目录

```http
POST /api/scan
```

---

# 8.2 获取媒体列表

```http
GET /api/media
```

---

# 8.3 重命名媒体

```http
POST /api/rename
```

---

# 8.4 生成 Metadata

```http
POST /api/metadata
```

---

# 九、Docker 部署设计

# 9.1 Docker Compose

```yaml
services:
  app:
    image: asmr-manager
    ports:
      - 8080:8080
    volumes:
      - ./media:/media
      - ./config:/config
      - ./data:/data
```

---

# 十、安全设计

# 10.1 原则

- 完全本地运行
- 不上传媒体
- 不依赖云 AI
- 无公网访问要求

---

# 10.2 NSFW 原则

- 不做内容审核
- 不做云端识别
- 不做违规传播
- 用户本地自管理

---

# 十一、性能设计

# 11.1 大媒体库优化

目标：

- 支持 10 万文件
- 支持增量扫描
- 支持缓存

---

# 11.2 缓存设计

缓存：

- hash
- OCR
- AI 推断结果

---

# 十二、开发路线图

# Phase 1 MVP

## 功能

- 文件扫描
- 自动分类
- 自动重命名
- Metadata
- Plex 输出

---

## 时间

预计：

- 2~4 周

---

# Phase 2

## 功能

- OCR
- AI 标签
- 去重
- 封面管理

---

# Phase 3

## 功能

- 本地 AI 增强
- 自动标签学习
- 智能推荐
- 语音识别

---

# 十三、未来扩展

# 13.1 支持平台

未来可扩展：

- Jellyfin
- Emby
- Kodi
- Navidrome

---

# 13.2 插件系统

支持：

- 自定义规则
- 自定义 Metadata
- 自定义 AI Prompt

---

# 十四、最终目标

打造：

> 面向 ASMR / VTuber / 同人媒体 的 Plex 媒体整理中心。

核心定位：

- 本地运行
- NAS 友好
- Docker 友好
- Plex 优先
- AI 辅助
- 高自动化
- 长期媒体归档

