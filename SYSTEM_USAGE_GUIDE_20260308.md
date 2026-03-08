# OpenClaw 内容工厂使用说明

## 1. 系统定位

这套系统当前已经可以稳定完成以下工作：

1. 选题与平台变现路径匹配
2. 生成 7 平台内容包
3. 自动终审、平台扩展、低分修复、质量复检
4. 生成视频 TTS
5. 生成 7 平台封面图

当前 7 平台范围：

- 知乎
- 小红书
- 抖音
- B站
- 微博
- 公众号
- 头条

说明：

- 养号、验证码规避、伪装真人互动已明确跳过，不在本说明范围内。
- 当前推荐模式是“生产级内容生成 + 人工审核后发布”，不是完全无人值守自动外发。

## 2. 运行环境

主生产环境在远端 Windows 主机，OpenClaw 工作目录主要是：

- `C:\Users\Roy\.openclaw\workspace`
- `C:\Users\Roy\.openclaw\workspace-content`

关键依赖：

- OpenClaw
- Node.js
- Python 3
- ComfyUI
- Windows System.Speech
- AdsPower Local API

辅助脚本所在本地仓库：

- [autopipeline_brain_content_publisher.py](C:\Users\Roy\Documents\New%20project\autopipeline_brain_content_publisher.py)
- [content_autotune_runner.py](C:\Users\Roy\Documents\New%20project\content_autotune_runner.py)
- [final_publish_refiner.py](C:\Users\Roy\Documents\New%20project\final_publish_refiner.py)
- [matrix_pack_expander.py](C:\Users\Roy\Documents\New%20project\matrix_pack_expander.py)
- [low_score_repair_runner.py](C:\Users\Roy\Documents\New%20project\low_score_repair_runner.py)
- [specificity_boost_runner.py](C:\Users\Roy\Documents\New%20project\specificity_boost_runner.py)
- [content_quality_gate.py](C:\Users\Roy\Documents\New%20project\content_quality_gate.py)
- [generate_pack_assets.py](C:\Users\Roy\Documents\New%20project\generate_pack_assets.py)
- [tts_render_windows.py](C:\Users\Roy\Documents\New%20project\tts_render_windows.py)

## 3. 推荐运行方式

### 3.0 网站控制台

本地启动网站控制台：

```powershell
py -3 C:\Users\Roy\Documents\New project\dashboard_app.py
```

访问地址：

```text
http://127.0.0.1:8787
```

控制台提供：

- 今日发布台
- 数据回灌上传
- agent 健康检查
- 流水线监控
- 手动发布状态回填

### 3.1 安全整链路

只跑内容生产、复检、TTS、素材，不触发真实发布：

```powershell
py -3 C:\Users\Roy\.openclaw\workspace\autopipeline_brain_content_publisher.py --skip-publisher
```

说明：

- 会生成 7 平台稿件
- 会自动做 `quality_gate`
- 会自动做 `specificity_boost`
- 会自动做 `quality_recheck`
- 会生成 TTS
- 会生成 7 平台封面图

### 3.2 快速回归

只验证主流水线，不生成图片：

```powershell
py -3 C:\Users\Roy\.openclaw\workspace\autopipeline_brain_content_publisher.py --skip-publisher --skip-assets
```

适合：

- 改完 prompt 或脚本后快速验证
- 不想启动 ComfyUI 时做逻辑回归

### 3.3 单独生成素材

对已存在的内容包生成 7 平台封面图：

```powershell
py -3 C:\Users\Roy\.openclaw\workspace\generate_pack_assets.py ^
  --input C:\Users\Roy\.openclaw\workspace-content\daily_pack_20260308_205355.json ^
  --max-images 7 ^
  --boot-comfy ^
  --low-memory ^
  --quality-preset balanced ^
  --manifest-out C:\Users\Roy\.openclaw\workspace-content\asset_manifest_daily_20260308_205355.json
```

### 3.4 单独释放浏览器内存

24G 内存机器建议在测试发布或浏览器任务后执行：

```powershell
py -3 C:\Users\Roy\.openclaw\workspace\release_browser_memory.py --all --base-url http://local.adspower.net:50361
```

## 4. 当前标准产物

每次整链路运行后，通常会产出：

1. 报告
2. 内容包
3. 初审质量报告
4. 复检质量报告
5. TTS 目录
6. 素材 manifest

当前最新生产基线：

- 报告：`C:\Users\Roy\.openclaw\workspace\reports\pipeline_autorun_20260308_205355.json`
- 内容包：`C:\Users\Roy\.openclaw\workspace-content\daily_pack_20260308_205355.json`
- 初审质量：`C:\Users\Roy\.openclaw\workspace-content\quality_20260308_205355.json`
- 复检质量：`C:\Users\Roy\.openclaw\workspace-content\quality_20260308_205355_recheck.json`
- 素材清单：`C:\Users\Roy\.openclaw\workspace-content\asset_manifest_daily_20260308_205355.json`
- TTS 目录：`C:\Users\Roy\.openclaw\workspace-content\tts_20260308_205355`

## 5. 如何判断一轮任务是否成功

看 4 个地方：

1. 主报告 `report_steps`
2. `quality.summary`
3. `quality_recheck.summary`
4. `asset_manifest` 和 `tts` 目录

当前合格标准：

- `quality_recheck.pass_count = 7`
- `quality_recheck.pass_rate = 1.0`
- 7 平台素材都存在
- `douyin_tts.wav` 和 `bilibili_tts.wav` 存在

## 6. 当前推荐操作顺序

1. 先跑安全整链路
2. 看 `quality_recheck`
3. 抽查 7 平台文案和 CTA
4. 抽查封面图
5. 人工决定是否真实发布
6. 发布或测试完成后释放浏览器内存

## 7. 当前不建议的用法

1. 不建议直接无人值守真实发布
2. 不建议把系统输出当成“无需审稿”的最终稿
3. 不建议边跑 AdsPower 大量页面边跑高质量 ComfyUI 出图
4. 不建议在没有复检结果时直接拿内容去投放

## 8. ComfyUI 运行建议

24G 内存机器当前建议：

- 质量预设：`balanced`
- `--low-memory`
- 批量：`1`
- 出图前尽量释放浏览器内存

对应说明文档：

- [COMFYUI_QUALITY_PLAYBOOK.md](C:\Users\Roy\Documents\New%20project\COMFYUI_QUALITY_PLAYBOOK.md)

## 9. 变现策略参考文档

当前系统已经接入的研究材料：

- [PLATFORM_MONETIZATION_RESEARCH_20260308.md](C:\Users\Roy\Documents\New%20project\PLATFORM_MONETIZATION_RESEARCH_20260308.md)
- [FULL_PLATFORM_MONETIZATION_MATRIX_20260308.json](C:\Users\Roy\Documents\New%20project\FULL_PLATFORM_MONETIZATION_MATRIX_20260308.json)
- [PDF_REPORT_CROSSCHECK_20260308.md](C:\Users\Roy\Documents\New%20project\PDF_REPORT_CROSSCHECK_20260308.md)

## 10. 常见故障定位

### 10.1 `quality_gate` 低分

优先看这些问题：

- `no_source_or_test_context`
- `body_too_short_for_platform`
- `low_specificity_numbers`
- `sentences_too_long`

对应处理模块：

- [low_score_repair_runner.py](C:\Users\Roy\Documents\New%20project\low_score_repair_runner.py)
- [specificity_boost_runner.py](C:\Users\Roy\Documents\New%20project\specificity_boost_runner.py)

### 10.2 ComfyUI 不在线

检查：

- `start_comfy_directml.py`
- 显存/内存占用
- AdsPower 是否还占着资源

### 10.3 发布链路不要直接开

当前真实发布仍建议人工把关。  
如果只是验证内容工厂，不要去掉 `--skip-publisher`。
