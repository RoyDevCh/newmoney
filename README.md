# OpenClaw 内容系统

当前维护入口：

- 主手册：[SYSTEM_REFERENCE.md](C:/Users/Roy/Documents/New%20project/SYSTEM_REFERENCE.md)

这份 `README.md` 只保留最短入口说明。所有架构、运行链路、依赖、平台策略、运维方法、已知不足和后续路线，统一以 `SYSTEM_REFERENCE.md` 为准。

## 当前状态

- 当前生产模式：自动生产 + 人工发布 + 自动复盘
- 当前优先目标：提升图文稳定变现能力，再继续强化视频链路
- 当前图片策略：消费类题材优先真实图，概念类题材可走 ComfyUI
- 当前网站地址：以 `reports/dashboard_access_latest.txt` 为准

## 接手时先看什么

1. `SYSTEM_REFERENCE.md`
2. 最近一批 `pipeline_autorun_*.json`
3. 最近一批 `quality_*_recheck.json`
4. 最近一批 `manual_publish_queue_*.json`
5. `metrics_analysis_latest.json`

## 维护规则

1. 每次做完任务，先更新 `SYSTEM_REFERENCE.md`。
2. 如果改了生产逻辑，顺手更新对应的“已知不足”和“后续路线图”。
3. 如果改了 Dashboard 或远端脚本，至少做一次验证后再结束。
