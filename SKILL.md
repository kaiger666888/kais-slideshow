---
name: kais-slideshow
version: 1.0.0
description: "通用轮播/幻灯片制作管线。触发词：slideshow、轮播、幻灯片、图文合集、小红书轮播、知识卡片、info-graphic、carousel、图文笔记。覆盖选题→调研→脚本→视觉→生成→合成的完整管线。"
---

# kais-slideshow — 通用轮播制作管线

## 触发词
`slideshow`, `轮播`, `幻灯片`, `图文合集`, `小红书轮播`, `知识卡片`, `info-graphic`, `carousel`, `图文笔记`, `kais-slideshow`, `做轮播`, `做卡片`

## 定位

将 kais-movie-agent 的核心流程（调研→创作→审核）泛化为**轻量级图文轮播管线**。适用于小红书轮播、知识卡片、教程合集、产品展示、信息图表等场景。

与 kais-movie-agent 的区别：

| | kais-movie-agent | kais-slideshow |
|---|---|---|
| 产出 | 视频（MP4） | 图片合集（PNG/PDF） |
| 复杂度 | 8+ Phase | 5 Phase |
| 视频生成 | Seedance/延长链 | ❌ 不需要 |
| 配音 | TTS | ❌ 不需要 |
| 后期合成 | FFmpeg 拼接+字幕 | 可选：PDF 合集 |
| 适用场景 | AI 短片/短剧 | 轮播/卡片/信息图 |

## 核心依赖

| 依赖 | 用途 | 必需 |
|------|------|------|
| kais-jimeng | 图片生成 | ✅ |
| deep-research | 品牌/选题调研 | 推荐 |
| kais-audience | 受众预测试 | 推荐 |
| Playwright | HTML→PNG 截图（文字卡片） | 可选 |
| ffmpeg | 图片→视频轮播（可选） | 可选 |

## 管线流程

```
Phase 1: 需求确认                              → 🔒 REVIEW GATE
  ↓
Phase 2: 调研与选题 (deep-research + kais-audience)  → checkpoint
  └─ 2a: 深度调研（品牌/受众/竞品）             → 自动
  └─ 2b: 选题投票筛选                           → 自动
  ↓
Phase 3: 脚本与分页设计                         → 🔒 REVIEW GATE
  └─ 确定页数、每页内容、视觉风格
  └─ 受众预测试（kais-audience 深度测评）        → 自动
  ↓
Phase 4: 视觉生成                               → 🔒 REVIEW GATE
  └─ 4a: 风格锁定（mood board / 参考图）
  └─ 4b: 逐页生成（文生图 / 图生图 / HTML卡片）
  └─ 4c: 一致性检查（风格/字体/配色统一）
  ↓
Phase 5: 合成与交付                             → checkpoint
  └─ PNG合集 / PDF / 可选转视频轮播
```

---

## Phase 1: 需求确认

收集以下信息（缺失时追问一次后用默认值）：

| 参数 | 选项 | 默认 | 说明 |
|------|------|------|------|
| **主题** | 自由文本 | — | 轮播的主题/选题 |
| **页数** | 3-20 | 6-8 | 轮播页数（小红书建议 6-9 页） |
| **比例** | 3:4 / 9:16 / 16:9 / 1:1 | 3:4 | 小红书用 3:4，抖音用 9:16 |
| **风格** | 见下方风格库 | auto | 视觉风格 |
| **品牌植入** | 是/否 | 否 | 是否有品牌软广需求 |
| **目标平台** | 小红书/抖音/B站/通用 | 小红书 | 影响尺寸和格式 |
| **交付格式** | PNG / PDF / MP4 | PNG | 输出格式 |

**风格库**：
- `minimal` — 极简白底，大字排版
- `dark` — 暗色系，科技感
- `warm` — 暖色调，情感类
- `comic` — 漫画风，故事类
- `infographic` — 信息图，数据类
- `cinematic` — 电影感，氛围类
- `handdrawn` — 手绘风，知识类
- `auto` — 根据主题自动匹配

**输出**：保存为 `PROJECT/requirement.json`

---

## Phase 2: 调研与选题

### Phase 2a: 深度调研（deep-research）

**触发条件**：有品牌植入、真实人物/事件、特定行业时启用。

调用 `deep-research` skill，调研维度：
- 品牌/产品核心卖点
- 目标受众画像
- 同类爆款案例（截图+数据）
- 平台热门选题趋势
- 相关圈层文化/禁忌

**输出**：`PROJECT/research/summary.json`

### Phase 2b: 选题投票筛选（kais-audience）

**触发条件**：调研产出 3+ 个选题方向时启用。

调用 `kais-audience` 快速投票模式，12 人虚拟评审团排名。

**输出**：`PROJECT/research/audience_vote.md`

---

## Phase 3: 脚本与分页设计

### 脚本结构

```json
{
  "title": "轮播标题",
  "subtitle": "副标题（可选）",
  "style": "minimal",
  "palette": ["#FFFFFF", "#333333", "#FF6B35"],
  "font": "Noto Sans CJK SC",
  "pages": [
    {
      "id": 1,
      "type": "cover",
      "title": "主标题",
      "subtitle": "副标题",
      "visual_prompt": "英文prompt（用于AI生成）",
      "layout": "center",
      "notes": "设计备注"
    },
    {
      "id": 2,
      "type": "content",
      "title": "要点标题",
      "body": "正文内容（支持 Markdown）",
      "visual_prompt": "配图描述",
      "visual_type": "ai_generated",
      "layout": "top-image-bottom-text",
      "highlight": "关键数据或金句"
    },
    {
      "id": 3,
      "type": "data",
      "title": "数据页标题",
      "data": [
        {"label": "指标A", "value": "95%", "trend": "up"},
        {"label": "指标B", "value": "3.2亿", "trend": "stable"}
      ],
      "visual_prompt": "数据可视化描述",
      "layout": "big-number"
    }
  ]
}
```

### 页面类型

| type | 用途 | 布局建议 |
|------|------|---------|
| `cover` | 封面 | 全图+居中文字 / 纯文字大标题 |
| `content` | 正文页 | 上图下文 / 左图右文 / 全文 |
| `data` | 数据页 | 大数字 / 图表 / 对比 |
| `quote` | 金句页 | 居中引用 / 人物+金句 |
| `timeline` | 时间线 | 纵向时间轴 / 横向步骤 |
| `comparison` | 对比页 | 左右分栏 / 表格 |
| `summary` | 总结页 | 要点回顾 / CTA |
| `end` | 尾页 | 关注引导 / 来源说明 |

### 受众预测试（自动）

脚本完成后自动运行 `kais-audience` 深度测评：
- 完播率预测（轮播 = 滑动完成率）
- 毒点检测（信息过载/排版混乱/广告突兀）
- 情绪曲线（每页的情绪标注）

**输出**：`PROJECT/research/audience_test.md`

**🔒 审核门**：将脚本摘要 + 测评结果展示给用户确认。

---

## Phase 4: 视觉生成

### Phase 4a: 风格锁定

生成 2-3 张参考图（mood board），锁定：
- 配色方案（主色 + 辅色 + 强调色）
- 字体风格
- 图片风格（写实/插画/扁平/手绘）
- 排版规范（间距/字号/对齐）

**输出**：`PROJECT/assets/style_ref_*.png` + `PROJECT/style_guide.json`

### Phase 4b: 逐页生成

根据 `visual_type` 选择生成方式：

| visual_type | 方式 | 工具 |
|-------------|------|------|
| `ai_generated` | AI 生成配图 | kais-jimeng 文生图 |
| `ai_stylized` | 图生图风格化 | kais-jimeng + 参考图 |
| `html_card` | HTML 模板渲染 | Playwright 截图 |
| `photo` | 实拍/素材图 | 用户提供的图片 |
| `none` | 纯文字排版 | HTML 模板渲染 |

**AI 生成参数**：
```bash
# 基础生成
curl -s http://localhost:8000/v1/images/generations \
  -H "Authorization: Bearer $SESSION_ID" \
  -d '{"model":"jimeng-5.0","prompt":"<visual_prompt>","ratio":"3:4","resolution":"2k"}'

# 基于风格参考图生成（保持一致性）
curl -s http://localhost:8000/v1/images/generations \
  -d '{"model":"jimeng-5.0","prompt":"<visual_prompt>","images":["<style_ref_url>"],"sample_strength":0.3,"ratio":"3:4"}'
```

**HTML 卡片模板**（文字/数据密集型页面）：
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { margin: 0; width: 1080px; height: 1440px; font-family: 'Noto Sans CJK SC'; background: #FFF; }
    .container { padding: 80px; display: flex; flex-direction: column; justify-content: center; }
    h1 { font-size: 72px; color: #333; margin-bottom: 40px; }
    .highlight { font-size: 120px; color: #FF6B35; font-weight: bold; }
  </style>
</head>
<body><div class="container">
  <h1>{{title}}</h1>
  <div class="highlight">{{highlight}}</div>
</div></body>
</html>
```

### Phase 4c: 一致性检查

检查清单：
- [ ] 配色统一（所有页面使用同一 palette）
- [ ] 字体统一（标题/正文字号一致）
- [ ] 风格统一（AI 生成图风格一致）
- [ ] 信息完整（无遗漏页面）
- [ ] 排版质量（无溢出/错位）

**🔒 审核门**：发送所有页面给用户审核。

---

## Phase 5: 合成与交付

### 输出格式

**PNG 合集**（默认）：
```bash
# 所有页面保存到 PROJECT/output/page_01.png ~ page_NN.png
```

**PDF 合集**：
```bash
ffmpeg -framerate 1 -i output/page_%02d.png -c:v pdf output/slideshow.pdf
# 或
convert output/page_*.png output/slideshow.pdf
```

**视频轮播**（可选，每页 3-5 秒自动播放）：
```bash
# 每页 5 秒，加淡入淡出转场
ffmpeg -framerate 1/5 -i output/page_%02d.png \
  -vf "fps=30,format=yuv420p" \
  -c:v libx264 -pix_fmt yuv420p \
  -t $(ls output/*.png | wc -l | xargs -I{} echo "{} * 5" | bc) \
  output/slideshow.mp4
```

**输出目录**：
```
PROJECT/
├── requirement.json
├── script.json
├── style_guide.json
├── research/
├── assets/          # AI 生成图、参考图
├── templates/       # HTML 模板
├── output/          # 最终产出
│   ├── page_01.png
│   ├── page_02.png
│   └── ...
└── slideshow.pdf    # 或 .mp4
```

---

## 审核门规范

| Phase | 审核内容 | 展示方式 |
|-------|---------|---------|
| Phase 1 | 需求参数确认 | 文字摘要 |
| Phase 3 | 脚本 + 受众测评结果 | 文字 + 关键数据 |
| Phase 4 | 所有页面预览 | 发送图片合集 |

**规则**：
1. 到达审核门必须暂停
2. 用户回复"通过"后继续
3. 用户要求修改则回滚到对应 Phase

---

## Git 版本管理

复用 kais-movie-agent 的 `git-stage-manager.js`：

| Stage | Phase | 产出 |
|-------|-------|------|
| `requirement` | 1 | requirement.json |
| `research` | 2 | research/*.json |
| `script` | 3 | script.json, style_guide.json |
| `visuals` | 4 | assets/*, output/* |
| `delivery` | 5 | slideshow.pdf/mp4 |

---

## 快速示例

```
用户: "帮我做一个小红书轮播，主题是 5 个提升专注力的方法"
→ Phase 1: 确认（3:4, 6页, minimal风格）
→ Phase 2: 调研热门专注力内容 + 受众投票
→ Phase 3: 生成脚本（封面+5个方法+尾页）
→ Phase 4: AI 生成配图 + HTML 排版文字页
→ Phase 5: 输出 7 张 PNG
```

```
用户: "给张雪机车做一个产品展示轮播，9页"
→ Phase 1: 确认（3:4, 9页, cinematic风格, 品牌植入）
→ Phase 2: deep-research 张雪品牌 + 受众测试
→ Phase 3: 脚本（品牌故事+产品卖点+用户口碑+CTA）
→ Phase 4: AI 生成场景图 + 数据页
→ Phase 5: 输出 9 张 PNG
```
