# weather · 不下雨的旅游目的地（江浙皖闽）

基于中央气象台（nmc.cn）7 天预报的**滚动**无雨城市速查静态页面：用户在页面上自选日期范围，结论按所选范围实时重算。

- 页面：<https://leonpenn.github.io/weather/>
- 覆盖：江苏 / 安徽 / 浙江 / 福建 共 307 站（地级市 50 个）
- 时间范围：页面可选起始/结束日期；起始不早于昨日（数据源预报自今日起，若含昨日会自动出现在选项中），截止为预报可提供的最远日期（约今日+6）
- 判定口径：所选范围内，白天（08–20时）无雨即算无雨，夜间降雨不影响结论；雨/雪/雷/雹计为降水
- 结论筛选项：白天全程无雨 / 1天有雨 / 2天有雨 / ≥3天有雨
- 淮安去重：NMC 清单中"淮安"有两条站点（DXKse / wVmjo），同名同页面但预报不同；官网城市页展示的是 wVmjo 的数据，页面收录该条、DXKse 不展示（2026-09-29 与官网核对）

## 自动维护

GitHub Actions（[refresh.yml](.github/workflows/refresh.yml)）在北京时间每小时 07 分运行（cron 用 UTC，北京 = UTC+8），常驻无窗口期：

1. `fetch_all.py` 抓取 307+1 站最新预报（每次强制更新；抓取失败时用上次缓存兜底）
2. 数据有变化时 `gen_html.py` 重新生成 index.html，自动提交并发布到 Pages

数据无变化的运行不产生提交。手动触发：仓库 Actions 页 → refresh → Run workflow。

## 本地运行

```bash
python fetch_all.py   # 抓取数据到 data/
python gen_html.py    # 生成 index.html（日期列表自动取自数据）
```
