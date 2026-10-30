# world_monitor_reports

本仓库由本机自托管 [World Monitor](https://github.com/koala73/worldmonitor) 实例（`http://192.168.110.184:27182`）的定时任务自动生成并推送，**内容为机器产出，未经人工编辑**。

## 结构

```
INDEX.md              所有报告的索引（日期 / 类型 / 路径 / 一句话结论 / 数据完整度）
TEMPLATES.md          报告结构、写作口径与分层规格
daily/YYYY-MM-DD.md   日报（每日 07:30 CST）
weekly/YYYY-Www.md    周报（每周日 09:00 CST，ISO 周）
monthly/YYYY-MM.md    月报（当月最后一天 21:00 CST）
yearly/YYYY.md        年报（12-31 21:00 CST）
raw/YYYY-MM-DD/       当日原始 API 快照（news/market/risk/natural/health .json）
raw/series.csv        每日关键指标累积序列（行情、新闻条数、数据源健康度、CII）
```

## 阅读须知

- 新闻 digest 有约 96 小时窗口与每类 ≤20 条的上限，单份报告只代表取数那一刻的切片。
- `importanceScore` 是关键词 + 来源权重打分，不是模型研判。
- CII（国家风险综合指数）在动态分量缺数据时 `degraded=true`、`dynamicScore=0`，此时只能作静态基线，不能用于排名或趋势结论。
- 无 API key 的数据源（ACLED / UCDP / 预测市场等）返回空数组而不是报错——空 ≠ 无事件。

## 推送机制

`wm-fetch` 取数后自动提交推送；兜底定时器每 15 分钟推送一次；凭据不进仓库。
