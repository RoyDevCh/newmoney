# 生产发布运营作战说明

## 1. 当前生产发布策略

当前最合适的生产模式不是“全自动发布”，而是：

1. 系统每天自动生成 7 平台内容包
2. 系统自动完成终审、修复、复检、TTS、封面图
3. 系统自动生成手动发布队列
4. 你按队列顺序人工发布
5. 当天晚间和次日回填数据
6. 系统根据数据做下一轮优化建议

这套策略的核心是：

- 内容生产自动化
- 发布决策人工把关
- 数据优化闭环化

## 2. 不同平台建议日产量

建议区分“生产量”和“发布量”。

生产量是系统每天准备的候选稿数量。
发布量是你真正发出去的数量。

当前建议基线：

| 平台 | 建议日产出 | 建议日发布 | 主要目标 |
| --- | --- | --- | --- |
| 知乎 | 2 | 1 | 高信任转化 |
| 小红书 | 3 | 2 | 收藏驱动涨粉 |
| 抖音 | 3 | 2 | 流量与主页点击 |
| B站 | 1 | 1 | 长时长信任建立 |
| 微博 | 3 | 2 | 热点触达 |
| 公众号 | 1 | 1 | 沉淀与私域承接 |
| 头条 | 3 | 2 | 阅读规模与流量收益 |

## 3. 一周内的发布节奏建议

第一周不要一上来把 7 平台全部打满。

更合理的节奏：

1. 第 1-2 天
   - 知乎 1
   - 小红书 1
   - 抖音 1
   - B站 1
   - 公众号 0-1
   - 微博 1
   - 头条 1
2. 第 3-4 天
   - 如果前两天素材稳定、你的人工发布能跟上，再把小红书、抖音、头条提升到 2
3. 第 5-7 天
   - 保持高分平台稳定发
   - 不要同时大幅加量和改风格

目标不是一周内“必赚”，而是尽快看到以下信号：

- 有稳定阅读/播放
- 有收藏和评论
- 有主页点击
- 有商品点击或资料包点击
- 有初步涨粉

如果你的承接页和商品卡已经准备好，一周内有机会出现第一笔转化，但不能把这个当成硬承诺。

## 4. 当前推荐的平台优先级

当前优先级建议：

1. 知乎
2. B站
3. 公众号
4. 小红书
5. 头条
6. 抖音
7. 微博

原因：

- 知乎/B站/公众号更适合建立高信任内容资产
- 小红书/抖音更适合放大流量和承接轻转化
- 头条适合跑阅读规模
- 微博更适合热点快反，不适合承接最核心的长期转化

## 5. 手动发布提醒机制

系统现在会自动生成两类文件：

1. 带时间戳的当次发布队列
   - `manual_publish_queue_YYYYMMDD_HHMMSS.json`
   - `manual_publish_queue_YYYYMMDD_HHMMSS.md`
2. 固定最新路径
   - `manual_publish_queue_latest.json`
   - `manual_publish_queue_latest.md`

你每天只需要打开固定最新文件即可：

- `C:\Users\Roy\.openclaw\workspace-content\manual_publish_queue_latest.md`

这个文件会告诉你：

- 今天有几条内容 ready
- 先发哪个平台
- 每个平台建议发布时间段
- 对应封面文件路径
- 视频平台对应 TTS 文件路径
- 发布后需要回填哪些数据

## 6. 每天如何把平台数据喂给系统

推荐每天两次回填：

1. 当天晚间回填首轮数据
2. 次日同一时间回填 24h 数据

输入格式支持 CSV 或 JSON。

模板文件：

- `C:\Users\Roy\.openclaw\workspace\metrics_input_template.csv`

最少建议回填这些字段：

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

运行命令：

```powershell
py -3 C:\Users\Roy\.openclaw\workspace\daily_metrics_ingest.py `
  --input C:\Users\Roy\.openclaw\workspace\metrics_input_template.csv `
  --output-json C:\Users\Roy\.openclaw\workspace-content\metrics_analysis_20260308.json `
  --output-md C:\Users\Roy\.openclaw\workspace-content\metrics_analysis_20260308.md `
  --latest-json C:\Users\Roy\.openclaw\workspace-content\metrics_analysis_latest.json `
  --latest-md C:\Users\Roy\.openclaw\workspace-content\metrics_analysis_latest.md
```

系统会自动汇总：

- 互动率
- 涨粉率
- 主页点击率
- 商品点击率
- 收益

并给出平台级优化建议。

## 7. 如何根据数据优化下一轮内容

当前建议按下面这个顺序优化：

1. 曝光低
   - 先改标题、封面、开头
2. 曝光有但互动低
   - 改 hook、结构、信息密度
3. 互动有但涨粉低
   - 改 CTA 和主页承接
4. 主页点击高但商品点击低
   - 改商品卡、资料包、落地页
5. 流量高但没收益
   - 改变现路径，不要只改文案

## 8. 是否可以开始上生产

可以。

但建议采用：

- 系统自动生产
- 你人工发布
- 每天数据回灌

而不是：

- 无人值守自动真实发布

## 9. 当前最实用的日常命令

整链路安全生产：

```powershell
py -3 C:\Users\Roy\.openclaw\workspace\autopipeline_brain_content_publisher.py --skip-publisher
```

查看今天的人工发布队列：

```powershell
notepad C:\Users\Roy\.openclaw\workspace-content\manual_publish_queue_latest.md
```

跑数据回灌分析：

```powershell
py -3 C:\Users\Roy\.openclaw\workspace\daily_metrics_ingest.py `
  --input C:\Users\Roy\.openclaw\workspace\metrics_input_template.csv `
  --output-json C:\Users\Roy\.openclaw\workspace-content\metrics_analysis_20260308.json `
  --output-md C:\Users\Roy\.openclaw\workspace-content\metrics_analysis_20260308.md `
  --latest-json C:\Users\Roy\.openclaw\workspace-content\metrics_analysis_latest.json `
  --latest-md C:\Users\Roy\.openclaw\workspace-content\metrics_analysis_latest.md
```
