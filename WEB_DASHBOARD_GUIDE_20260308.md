# OpenClaw 网站控制台使用说明

## 1. 作用

这个网站控制台解决 4 件事：

1. 查看今天系统生产出的可发布内容
2. 按平台查看标题、正文、封面和 TTS
3. 上传各平台数据，回灌给系统继续优化
4. 查看每个 agent 和主流水线的最新状态
5. 回填每个平台“已发/未发/内容 ID/链接/备注”
6. 查看多日数据趋势

## 2. 启动方式

在本地项目目录运行：

```powershell
py -3 C:\Users\Roy\Documents\New project\dashboard_app.py
```

默认访问地址：

- [http://127.0.0.1:8787](http://127.0.0.1:8787)

## 3. 页面结构

### 3.1 总览

总览页会显示：

- 远端主机连接配置
- 今日待发布内容数量
- 最新复检通过率
- 最新流水线状态
- 最新数据回灌结果

### 3.2 发布台

发布台会直接显示：

- 平台
- 标题
- Hook
- 正文
- CTA
- 标签
- 封面图预览
- 视频 TTS 播放器
- 建议发布时间段
- 建议日发布量

手动发布时，优先看：

- `manual_publish_queue_latest.md`
- 网站里的“发布台”

发布后可直接在卡片下方回填：

- 是否已发布
- 内容 ID
- 发布链接
- 备注

## 4. 数据回灌

上传 CSV 或 JSON 后，系统会：

1. 把文件传到远端 `metrics_uploads`
2. 运行 `daily_metrics_ingest.py`
3. 生成最新分析文件
4. 主脑下一轮自动读取 `metrics_analysis_latest.json`

网站会先做一层字段适配，再上传到远端分析器。
也就是说平台导出的 CSV/JSON 不一定要完全等于系统模板。

推荐回填字段：

- `date`
- `platform`
- `content_id`
- `title`
- `views`
- `likes`
- `comments`
- `favorites`
- `shares`
- `follows`
- `profile_clicks`
- `product_clicks`
- `revenue`

## 5. 系统监控

监控页可以：

- 刷新 agent 健康检查
- 查看每个 agent 最近一次响应
- 查看主流水线每一步是否成功
- 查看最近的报告路径

## 6. 网站依赖的远端文件

网站主要读取：

- `manual_publish_queue_latest.json`
- `metrics_analysis_latest.json`
- 最新 `pipeline_autorun_*.json`
- 最新 `agent_health_full_*.json`
- 最新 `daily_pack_*.json`
- 最新 `quality_*_recheck.json`

## 7. 当前上线建议

这个网站适合：

- 每天查看待发布内容
- 手动发布
- 录入平台反馈
- 盯系统健康

当前不建议直接让网站触发真实自动发布。

## 8. 后续增强点

下一步最值当的增强有：

1. 增加后台数据格式适配器，减少手工整理 CSV
2. 增加发布完成回填字段，比如“已发/未发/链接/内容 ID”
3. 增加多日趋势图，而不是只看单日分析
