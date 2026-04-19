# 沃尔沃99周年 Slideshow 案例复盘

## 项目概况
- **需求**：沃尔沃99周年品牌宣传短视频，20秒，竖版
- **素材**：Notion 页面内容（5个历史车型）+ 5张图片 + 收尾图
- **最终输出**：1080×1920，Vintage Education BGM

## 迭代历程

| 版本 | 变更 | 结果 |
|------|------|------|
| v1 | ffmpeg Ken Burns 统一推近 | ❌ 动效太单调 |
| v2 | ffmpeg xfade + 不同 zoompan 方向 | ❌ 图片横向压扁 |
| v3 | ffmpeg force_original_aspect_ratio | ❌ 仍有变形 |
| v4 | MoviePy PIL cover-fill center crop | ⚠️ 用户要求露出车标 |
| v5 | 用户手动选择裁剪位置 | ✅ 通过，但字体乱码 |
| v5+ | 修复中文字体 (wqy-zenhei) | ✅ 字体正常 |
| v6 | 替换 EX90 为高清图 + BGM | ✅ BGM 版 |
| v7 | EX90 换知乎图 | ✅ |
| v8 | 分辨率提升到 1080p | ✅ 最终版 |

## 关键决策
1. **放弃 ffmpeg 滤镜**：4次尝试均导致变形，改用 MoviePy + PIL
2. **手动裁剪选择**：自动检测模型不可用，改用预览条人工选择
3. **kais-bgm 匹配**：第一批史诗风格偏童话，换积极/电子风格后匹配成功
4. **kais-search 补图**：EX90 原图太模糊，用必应搜到高清候选

## 踩坑记录
- ffmpeg zoompan 的 `force_original_aspect_ratio` 参数名在不同版本行为不一致
- PIL 打开 RGBA webp 图片时，MoviePy 可能有兼容问题，建议转 JPG
- 720p 测试通过后再升 1080p，渲染时间约 2x
