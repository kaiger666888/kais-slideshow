---
name: kais-slideshow
version: 1.0.0
description: "通用 Slideshow 短视频生成器。从图片+文字快速生成带动效+BGM 的竖版/横版短视频。触发词：做slideshow、生成幻灯片视频、图片轮播视频、制作 slideshow、slideshow video、照片墙视频、图片加音乐、图片配乐、做照片视频、生成照片视频"
---

# kais-slideshow — 通用 Slideshow 短视频生成器

将一组图片 + 文字描述快速合成为带动效和背景音乐的短视频。

## 快速使用

用户提供图片（URL/本地/Notion）+ 文字 → 自动裁剪预览 → 用户选位置 → 动效合成 → BGM匹配 → 输出视频。

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 分辨率 | 1080×1920 | 竖版。横版用 1920×1080 |
| 帧率 | 30fps | 视频帧率 |
| 每张时长 | 3.5s | 单张图片展示秒数 |
| 过渡时长 | 0.5s | 图片间交叉淡入淡出 |
| BGM | 自动匹配 | 通过 kais-bgm 智能选曲 |

## 核心流程

### 步骤 1：素材准备

<!-- FREEDOM:high -->
收集用户提供的素材：

**支持的素材来源：**
- **Notion 页面** — 读取页面内容，提取图片 URL
- **图片 URL** — 直接下载
- **本地文件** — 从用户发送的文件获取
- **文字内容** — 每张图片对应的标题/描述

**输出**：`/tmp/slideshow_<timestamp>/images/` 目录下所有图片 + 内容列表
<!-- /FREEDOM:high -->

### 步骤 2：图片裁剪预览（Human-in-the-loop）

<!-- FREEDOM:low -->
**必须生成裁剪预览让用户确认，不可自动裁剪。**

#### 为什么需要这一步？
- 横版图裁到竖版（或反过来）时，重要内容可能被裁掉
- 不同图片主体位置不同，无法自动判断最佳裁剪位置
- 裁错一次 = 整个视频要重来

#### 裁剪算法
```python
# PIL cover-fill + 居中裁剪（零变形）
from PIL import Image

def cover_crop(img_path, target_w, target_h, crop_ratio_h, crop_ratio_v=0.5):
    """
    crop_ratio_h: 0=far-L, 0.15=left, 0.35=center-L, 0.55=center-R, 0.75=far-R, 1.0=far-R
    crop_ratio_v: 0.5=居中（默认）
    """
    img = Image.open(img_path).convert("RGB")
    iw, ih = img.size
    
    # cover-fill: 确保填满目标尺寸
    scale = max(target_w / iw, target_h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    
    # 计算裁剪偏移
    max_x = max(0, nw - target_w)
    max_y = max(0, nh - target_h)
    x_off = int(crop_ratio_h * max_x)
    y_off = int(crop_ratio_v * max_y)
    
    return img.crop((x_off, y_off, x_off + target_w, y_off + target_h))
```

#### 生成预览条
为每张图生成 5 个裁剪位置预览（far-L / left / center-L / center-R / far-R），拼成一张预览图发给用户选择。

```python
# 预览条生成示例
positions = [0, 0.15, 0.35, 0.55, 0.75]
labels = ["far-L", "left", "center-L", "center-R", "far-R"]

# 缩略图尺寸
cw, ch = 200, 356  # 保持 720:1280 比例
sheet = Image.new("RGB", (cw * 5 + 40, ch + 40), (40, 40, 40))

for i, (pos, label) in enumerate(zip(positions, labels)):
    cropped = cover_crop(img_path, W, H, pos)
    thumb = cropped.resize((cw, ch), Image.LANCZOS)
    sheet.paste(thumb, (i * (cw + 10), 25))
```

#### 交互流程
1. 生成预览条 → 发送给用户
2. 用户回复位置选择（如 `#2 left` 或直接 `center`）
3. 记录每张图的裁剪位置到配置

**裁剪位置映射：**
| 用户选择 | crop_ratio_h |
|---------|-------------|
| far-L | 0 |
| left | 0.15 |
| center-L | 0.35 |
| center-R | 0.55 |
| far-R | 0.75 |
<!-- /FREEDOM:low -->

### 步骤 3：动效合成（MoviePy）

<!-- FREEDOM:high -->
用 MoviePy + PIL 实现多样化动效，**不要用 ffmpeg zoompan/crop**（会导致图片变形）。

#### 可用动效
| 效果 | 说明 | 适用场景 |
|------|------|---------|
| zoom_in | 从 1.0x 缓慢放大到 1.15x | 车辆、产品特写 |
| zoom_out | 从 1.15x 缓慢缩小到 1.0x | 建筑、风景 |
| pan_left | 从右向左平移 | 时间线、叙事 |
| pan_right | 从左向右平移 | 揭示、展开 |
| pan_up | 从下向上平移 | 高楼、天空 |
| pan_down | 从上向下平移 | 俯瞰、地图 |
| ken_burns | 缩放+平移组合 | 经典纪录片 |

#### 动效实现（以 zoom_in 为例）
```python
import moviepy.editor as mpy
from PIL import Image

def make_zoom_clip(img_path, W, H, crop_ratio, duration, zoom_start=1.0, zoom_end=1.15):
    img = Image.open(img_path).convert("RGB")
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    base_w, base_h = int(iw * scale), int(ih * scale)
    
    max_x = max(0, base_w - W)
    max_y = max(0, base_h - H)
    cx = int(crop_ratio * max_x)
    cy = int(0.5 * max_y)
    
    def make_frame(t):
        progress = t / duration
        z = zoom_start + (zoom_end - zoom_start) * progress
        fw = int(base_w / z)
        fh = int(base_h / z)
        fx = max(0, min(cx - (fw - W) // 2, base_w - fw))
        fy = max(0, min(cy - (fh - H) // 2, base_h - fh))
        resized = img.resize((fw, fh), Image.LANCZOS)
        cropped = resized.crop((fx, fy, fx + W, fy + H))
        if cropped.size != (W, H):
            cropped = cropped.resize((W, H), Image.LANCZOS)
        return np.array(cropped)
    
    clip = mpy.VideoClip(make_frame, duration=duration)
    return clip
```

#### 关键注意事项
- **变形零容忍**：所有裁剪必须保持原始宽高比，用 `max(W/iw, H/ih)` 而非 `min`
- **动效多样化**：不要所有图用同一个效果，交替使用不同动效
- **帧率一致性**：所有 clip 统一 fps
- **交叉淡入淡出**：用 `mpy.concatenate_videoclips` 或 `mpy.CompositeVideoClip`，每张最后 0.5s 与下一张开头 0.5s 叠加
<!-- /FREEDOM:high -->

### 步骤 4：文字叠加

<!-- FREEDOM:high -->
在每张图片下方叠加文字（标题、年份等）。

```python
# 中文字体
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 48)
except:
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 48)

# 在 make_frame 中绘制文字
from PIL import ImageDraw
draw = ImageDraw.Draw(frame)
# 半透明黑底
draw.rectangle([(0, H - 120), (W, H)], fill=(0, 0, 0, 160))
# 白色文字居中
bbox = draw.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
draw.text(((W - tw) // 2, H - 100), text, fill=(255, 255, 255), font=font)
```

**注意**：必须使用支持中文的字体，否则会显示方框。备选：`wqy-zenhei`、`NotoSansCJK`、`AR PL UKai CN`。
<!-- /FREEDOM:high -->

### 步骤 5：BGM 匹配（kais-bgm）

<!-- FREEDOM:high -->
调用 kais-bgm skill 自动匹配背景音乐。

```bash
cd ~/.openclaw/workspace/skills/kais-bgm
node -e "
import { selectBGM } from './lib/bgm-selector.js';
import { readFileSync } from 'node:fs';
const lib = JSON.parse(readFileSync('./lib/bgm-library.json'));
const results = selectBGM('<场景描述>', '<情感标签>', lib, { topN: 3, minDuration: 15, maxDuration: 60 });
for (const r of results) {
  console.log('[' + r.score + '分]', r.filename, '| 时长:', r.duration.toFixed(1) + 's');
  console.log(r.path);
}
"
```

用户试听选定后，用 ffmpeg 混合：
```bash
ffmpeg -y -i video_no_audio.mp4 -i bgm.mp3 \
  -filter_complex "[1:a]afade=t=in:st=0:d=1,afade=t=out:st=19:d=1,atrim=0:20[bgm]" \
  -map 0:v -map "[bgm]" -c:v copy -c:a aac -b:a 192k output.mp4
```
<!-- /FREEDOM:high -->

### 步骤 6：输出与交付

<!-- FREEDOM:high -->
最终视频通过 message tool 以 document 形式发送给用户。

**输出规范：**
- 格式：MP4 (H.264 + AAC)
- 默认分辨率：1080×1920（竖版）
- 文件命名：`output/slideshow_<描述>.mp4`
<!-- /FREEDOM:high -->

## 完整脚本模板

```python
#!/usr/bin/env python3
"""kais-slideshow: 通用 Slideshow 短视频生成器"""
import os, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mpy

# === 配置 ===
W, H = 1080, 1920  # 竖版；横版改为 1920, 1080
FPS = 30
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
WORK_DIR = "/tmp/slideshow"  # 工作目录

# === 素材配置（根据实际内容填写）===
SLIDES = [
    {"img": "images/1.jpg",  "text": "标题1", "dur": 3.5, "effect": "zoom_in",  "crop_h": 0.35},
    {"img": "images/2.jpg",  "text": "标题2", "dur": 3.5, "effect": "pan_right", "crop_h": 0.55},
    # ... 更多图片
]
CLOSING_IMG = "images/closing.jpg"  # 可选收尾图

# === 裁剪函数 ===
def cover_crop(img_path, tw, th, crop_h=0.5, crop_v=0.5):
    img = Image.open(img_path).convert("RGB")
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    mx, my = max(0, nw - tw), max(0, nh - th)
    return img.crop((int(crop_h * mx), int(crop_v * my), int(crop_h * mx) + tw, int(crop_v * my) + th))

# === 动效函数 ===
def make_clip(slide, font):
    img = Image.open(os.path.join(WORK_DIR, slide["img"])).convert("RGB")
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    bw, bh = int(iw * scale), int(ih * scale)
    mx, my = max(0, bw - W), max(0, bh - H)
    cx, cy = int(slide["crop_h"] * mx), int(0.5 * my)
    dur = slide["dur"]
    effect = slide["effect"]
    text = slide["text"]
    
    def make_frame(t):
        p = t / dur
        if effect == "zoom_in":
            z = 1.0 + 0.15 * p
        elif effect == "zoom_out":
            z = 1.15 - 0.15 * p
        elif effect == "pan_left":
            z = 1.1
            cx = mx * (1 - p)
        elif effect == "pan_right":
            z = 1.1
            cx = mx * p
        elif effect == "pan_up":
            z = 1.1
            cy = my * (1 - p)
        elif effect == "pan_down":
            z = 1.1
            cy = my * p
        else:
            z = 1.0 + 0.1 * p
        
        fw, fh = int(bw / z), int(bh / z)
        fx = max(0, min(cx - (fw - W) // 2, bw - fw))
        fy = max(0, min(cy - (fh - H) // 2, bh - fh))
        frame = img.resize((fw, fh), Image.LANCZOS).crop((fx, fy, fx + W, fy + H))
        if frame.size != (W, H):
            frame = frame.resize((W, H), Image.LANCZOS)
        
        # 文字叠加
        draw = ImageDraw.Draw(frame)
        # 半透明黑底
        draw.rectangle([(0, H - 140), (W, H)], fill=(0, 0, 0, 160))
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, H - 110), text, fill=(255, 255, 255), font=font)
        return np.array(frame)
    
    return mpy.VideoClip(make_frame, duration=dur).set_fps(FPS)

# === 主流程 ===
def main():
    os.makedirs(os.path.join(WORK_DIR, "output"), exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, 48)
    
    # 生成所有 clip
    clips = []
    for slide in SLIDES:
        print(f"处理: {slide['text']} ({slide['effect']})")
        clips.append(make_clip(slide, font))
    
    # 收尾图（如有）
    if CLOSING_IMG and os.path.exists(os.path.join(WORK_DIR, CLOSING_IMG)):
        clips.append(make_clip({"img": CLOSING_IMG, "text": "", "dur": 3.0, "effect": "zoom_in", "crop_h": 0.5}, font))
    
    # 交叉淡入淡出拼接
    cross_dur = 0.5
    final = mpy.concatenate_videoclips(clips, method="compose", padding=-cross_dur)
    
    # 输出
    out_path = os.path.join(WORK_DIR, "output/slideshow.mp4")
    final.write_videofile(out_path, fps=FPS, codec="libx264", audio=False)
    print(f"输出: {out_path}")

if __name__ == "__main__":
    main()
```

## 教训与最佳实践（来自实际项目）

### ❌ 不要做的事
1. **不要用 ffmpeg zoompan/crop 做动效** — 多次尝试均导致图片横向压扁
2. **不要用 `min(W/iw, H/ih)` 做缩放** — 会导致黑边或变形，必须用 `max`
3. **不要跳过裁剪预览** — 一次裁错就要整条重来
4. **不要用不支持中文的默认字体** — 会显示方框

### ✅ 推荐做法
1. **PIL cover-fill + 居中裁剪** — 保证零变形
2. **每张图生成预览条** — 5个位置让用户选
3. **动效多样化** — 交替使用 zoom/pan/ken_burns
4. **BGM 淡入淡出** — 首尾各 1s，避免突兀
5. **先用低分辨率测试** — 720p 确认无误后再升 1080p

## 依赖

| 工具 | 用途 | 安装 |
|------|------|------|
| Pillow | 图片裁剪、文字绘制 | `pip install Pillow` |
| MoviePy | 视频合成 | `pip install moviepy` |
| numpy | 帧数组 | `pip install numpy` |
| ffmpeg | 编码输出 | 系统包 |
| kais-bgm | BGM 匹配 | 本地 skill |
| kais-search | 图片搜索 | 本地 skill |

## 文件结构

```
kais-slideshow/
├── SKILL.md              # 本文件
├── scripts/
│   └── generate.py       # 生成脚本模板
└── references/
    └── volvo99-case.md   # 沃尔沃99周年案例复盘
```
