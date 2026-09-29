# weather · 国庆江浙皖闽无雨城市速查

基于中央气象台（nmc.cn）7 天预报，筛选 **2026-10-02 ~ 2026-10-05 白天无雨城市** 的静态页面。

- 页面：<https://leonpenn.github.io/weather/>
- 覆盖：江苏 / 安徽 / 浙江 / 福建 共 308 站（地级市 50 个）
- 判定口径：白天（08–20时）无雨即算无雨，夜间降雨不影响结论；雨/雪/雷/雹计为降水
- 结论筛选项：白天全程无雨 / 1天有雨 / 2天有雨 / ≥3天有雨

## 自动维护

GitHub Actions（[refresh.yml](.github/workflows/refresh.yml)）在北京时间每天 08/12/18/22 点自动运行，仅限窗口期 2026-09-29 ~ 10-06：

1. `fetch_all.py` 抓取 308 站最新预报（含重试与本地缓存）
2. 数据有变化时 `gen_html.py` 重新生成 index.html，自动提交并发布到 Pages

数据无变化的运行不产生提交。手动触发：仓库 Actions 页 → refresh → Run workflow。

## 本地运行

```bash
python fetch_all.py   # 抓取数据到 data/
python gen_html.py    # 生成 index.html
```
