# -*- coding: utf-8 -*-
"""从 wx_*.json 生成自包含 index.html 速查页（覆盖江苏/安徽/浙江/福建）"""
import json, glob, datetime

DATES = ["2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05"]
WEEK = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
WET = ("雨", "雪", "雷", "雹")
PROV_ORDER = ["江苏", "安徽", "浙江", "福建"]
PROV_SHORT = {"江苏": "苏", "安徽": "皖", "浙江": "浙", "福建": "闽"}
PROV_FILES = [("data/ajs.json", "江苏"), ("data/aah.json", "安徽"), ("data/azj.json", "浙江"), ("data/afj.json", "福建")]
# 淮安在 NMC 清单中有两条同名站点（DXKse/wVmjo，同页面、预报可能不同）；
# 官网城市页展示 wVmjo 的数据（2026-09-29 核对），故收录 wVmjo，DXKse 不展示
HIDDEN_STATIONS = {"DXKse"}
PREF = {
    "南京","无锡","徐州","常州","苏州","南通","连云港","淮安","盐城","扬州","镇江","泰州","宿迁",
    "合肥","芜湖","蚌埠","淮南","马鞍山","淮北","铜陵","安庆","黄山","滁州","阜阳","宿州","六安","亳州","池州","宣城",
    "杭州","宁波","温州","嘉兴","湖州","绍兴","金华","衢州","舟山","台州","丽水",
    "福州","厦门","莆田","三明","泉州","漳州","南平","龙岩","宁德",
}

def emoji(info):
    if "雷" in info: return "⛈️"
    if "雪" in info: return "🌨️"
    if "雨" in info: return "🌦️" if info.startswith("小") else "🌧️"
    if info == "晴": return "☀️"
    if info == "多云": return "⛅"
    if info == "阴": return "☁️"
    if "雾" in info or "霾" in info or "沙" in info or "尘" in info: return "🌫️"
    return "☁️"

stations, pub = [], ""
for f, prov_expect in PROV_FILES:
    for s in json.load(open(f, encoding="utf-8")):
        if s["code"] in HIDDEN_STATIONS: continue
        stations.append({"code": s["code"], "name0": s["city"], "url": s["url"], "prov_expect": prov_expect})

data = []
for s in stations:
    j = json.load(open(f"data/wx_{s['code']}.json", encoding="utf-8"))
    p = j["data"]["predict"]; st = p["station"]
    pub = max(pub, p.get("publish_time") or "")
    days = {d["date"]: d for d in p["detail"]}
    cells, temps, total = [], [], 0.0
    for dt in DATES:
        d = days[dt]
        dn, nt = d["day"]["weather"]["info"], d["night"]["weather"]["info"]
        dr = any(k in dn for k in WET); nr = any(k in nt for k in WET)
        total += float(d.get("precipitation") or 0)
        temps += [int(d["day"]["weather"]["temperature"] or 0), int(d["night"]["weather"]["temperature"] or 0)]
        cells.append({"dn": dn, "nt": nt, "dr": dr, "nr": nr})
    name = st["city"]
    assert st["province"].replace("省", "") == s["prov_expect"], \
        f"省份不符: {name} {st['province']} != {s['prov_expect']}"
    data.append({"name": name, "prov": st["province"].replace("省", ""), "pref": name in PREF,
                 "url": "https://www.nmc.cn" + st["url"], "cells": cells,
                 "dayRain": sum(c["dr"] for c in cells), "dryAll": not any(c["dr"] for c in cells),
                 "dryStrict": not any(c["dr"] or c["nr"] for c in cells),
                 "precip": round(total, 1), "lo": min(temps), "hi": max(temps)})

# 校验：预期地级市是否都命中
have = {s["name"] for s in data if s["pref"]}
miss = [n for n in sorted(PREF) if n not in have]
if miss: print("警告: 未匹配到的地级市:", miss)

# 站点重名时，后者自动加"②"区分
seen = set()
for s in data:
    if s["name"] in seen: s["name"] += "②"
    seen.add(s["name"])

data.sort(key=lambda s: (not s["dryAll"], not s["pref"], s["dayRain"], s["precip"],
                         PROV_ORDER.index(s["prov"]) if s["prov"] in PROV_ORDER else 9, s["name"]))

total = len(data)
dry = [s for s in data if s["dryAll"]]
strict = [s for s in data if s["dryStrict"]]
pref_n = sum(s["pref"] for s in data)
per_prov = {pv: {"n": sum(1 for s in data if s["prov"] == pv),
                 "dry": sum(1 for s in data if s["prov"] == pv and s["dryAll"]),
                 "pref": sum(1 for s in data if s["prov"] == pv and s["pref"])} for pv in PROV_ORDER}
print("省份统计:", {k: (v["dry"], "/", v["n"]) for k, v in per_prov.items()})

headers = "".join(
    f'<th>{dt}<br><small>{WEEK[datetime.date.fromisoformat(dt).weekday()]}</small></th>'
    for dt in DATES)

daycards = []
for i, dt in enumerate(DATES):
    secs = []
    for pv in PROV_ORDER:
        dryc = [s["name"] for s in data if s["pref"] and s["prov"] == pv and not s["cells"][i]["dr"]]
        wetc = [s["name"] for s in data if s["pref"] and s["prov"] == pv and s["cells"][i]["dr"]]
        dchips = "".join(f'<span class="chip g">{n}</span>' for n in dryc) or '<span class="mut">—</span>'
        wchips = "".join(f'<span class="chip b">{n}</span>' for n in wetc) or '<span class="mut">—</span>'
        secs.append(f'<p class="lbl">{PROV_SHORT[pv]} ☀️无雨 {len(dryc)} · 🌧️有雨 {len(wetc)}</p>'
                    f'<div>{dchips}<span class="sep"></span>{wchips}</div>')
    daycards.append(f'<div class="daycard"><h3>{dt} {WEEK[datetime.date.fromisoformat(dt).weekday()]}（白天）</h3>'
                    + "".join(secs) + '</div>')

dry_hero = "".join(
    f'<div class="heroitem"><b>{PROV_SHORT[s["prov"]]}·{s["name"]}</b><span>{s["prov"]} · {"地级市" if s["pref"] else "县级"}</span>'
    f'<em>{s["lo"]}~{s["hi"]}°C · 累计降水 {s["precip"]} mm</em></div>'
    for s in dry)

if len(strict) == len(dry):
    strict_note = f"若把夜间降雨也计入，名单完全相同（{len(strict)} 站）——本次过程为系统性降雨，四省无“只下夜雨”的站点。"
else:
    extra = [f'{PROV_SHORT[s["prov"]]}·{s["name"]}' for s in dry if not s["dryStrict"]]
    strict_note = f"若把夜间降雨也计入，无雨站为 {len(strict)} 站；白天口径下有夜间降雨的 {len(extra)} 站：{'、'.join(extra)}。"

prov_options = "".join(f"<option>{pv}</option>" for pv in PROV_ORDER)
prov_line = " · ".join(f"{pv} {per_prov[pv]['n']}" for pv in PROV_ORDER)
kpi_prov = "".join(
    f'<div class="card{" green" if per_prov[pv]["dry"] else ""}"><b>{per_prov[pv]["dry"]} / {per_prov[pv]["n"]}</b>'
    f'<span>{pv}无雨站 / 总站（地级市 {per_prov[pv]["pref"]}）</span></div>'
    for pv in PROV_ORDER)

DATA_JSON = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
GEN = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")  # 北京时间（CI runner 时区为 UTC，直接取会差 8 小时）

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>国庆无雨城市速查 · 江浙皖闽 2026-10-02 ~ 2026-10-05</title>
<style>
:root{--ink:#1c2733;--mut:#6b7a89;--line:#e3e9ef;--bg:#f6f8fa;--green:#0e9f6e;--greenbg:#e6f7f0;--blue:#3b82c4;--bluebg:#e9f2fb;--graybg:#eef1f5}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink)}
.wrap{max-width:1150px;margin:0 auto;padding:22px 16px 60px}
h1{font-size:22px;margin:6px 0 4px}
.sub{color:var(--mut);font-size:13px;line-height:1.7;margin-bottom:16px}
.sub a{color:var(--blue)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:12px;margin:16px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.card b{font-size:24px;display:block;line-height:1.2}
.card span{color:var(--mut);font-size:12.5px}
.card.green b{color:var(--green)}
.hero{background:linear-gradient(135deg,#e6f7f0,#e9f2fb);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:16px 0}
.hero h2{margin:0 0 10px;font-size:15px}
.heroitems{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.heroitem{background:#ffffffcc;border-radius:10px;padding:10px 12px}
.heroitem b{font-size:16px}
.heroitem span{display:block;color:var(--mut);font-size:12px;margin-top:2px}
.heroitem em{display:block;font-style:normal;font-size:12.5px;color:var(--green);font-weight:600;margin-top:4px}
h2.sec{font-size:15px;margin:26px 0 10px}
.daygrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}
.daycard{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.daycard h3{margin:0 0 8px;font-size:14px}
.daycard .lbl{font-size:12px;color:var(--mut);margin:8px 0 4px}
.daycard div{line-height:2}
.sep{display:inline-block;width:8px}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;margin:2px 2px}
.chip.g{background:var(--greenbg);color:#0b7d58}
.chip.b{background:var(--bluebg);color:#2a6395}
.filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:16px 0 10px;position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:5}
.filters select,.filters input{padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:13px;color:var(--ink)}
.filters input{width:150px}
.filters .cnt{color:var(--mut);font-size:12.5px;margin-left:auto}
.tablewrap{overflow:auto;max-height:72vh;border:1px solid var(--line);border-radius:12px;background:#fff}
table{border-collapse:separate;border-spacing:0;width:100%;min-width:860px}
th,td{padding:7px 10px;font-size:13.5px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
thead th{position:sticky;top:0;background:#eef3f8;font-size:12.5px;z-index:2;box-shadow:inset 0 -1px 0 var(--line)}
th.sortable{cursor:pointer;user-select:none}
th.sortable:hover{background:#e2eaf2}
td .n{color:#8494a5;font-size:12px;margin-left:8px}
td.name a{color:var(--ink);text-decoration:none;border-bottom:1px dotted #b8c4cf}
td.name a:hover{color:var(--blue)}
.tag{display:inline-block;padding:1px 9px;border-radius:999px;font-size:12px;font-weight:600}
.tag.g{background:var(--greenbg);color:#0b7d58}
.tag.b{background:var(--graybg);color:#5b6b7b}
.tag.p{background:var(--bluebg);color:#2a6395}
td.rain{background:var(--bluebg)}
tr.dry td{background:#f2fbf6}
tr.dry td:first-child{box-shadow:inset 3px 0 0 var(--green)}
/* 站点/省份列固定：110px 为站点列定宽，省份列 left 偏移与其对应 */
td.name{position:sticky;left:0;z-index:1;background:#fff;width:110px;min-width:110px}
td.prov{position:sticky;left:110px;z-index:1;background:#fff;width:58px;min-width:58px;box-shadow:inset -1px 0 0 var(--line),3px 0 6px -3px rgba(28,39,51,.18)}
tr.dry td.name,tr.dry td.prov{background:#f2fbf6}
thead th.hfix{left:0;z-index:3;width:110px;min-width:110px}
thead th.prov{left:110px;width:58px;min-width:58px;box-shadow:inset 0 -1px 0 var(--line),inset -1px 0 0 var(--line),3px 0 6px -3px rgba(28,39,51,.18)}
.foot{color:var(--mut);font-size:12.5px;line-height:1.9;margin-top:18px}
.mut{color:var(--mut)}
</style>
</head>
<body>
<div class="wrap">
  <h1>🌧️→☀️ 国庆无雨城市速查 · 江浙皖闽（2026-10-02 ~ 2026-10-05）</h1>
  <div class="sub">
    数据源：<a href="https://www.nmc.cn" target="_blank">中央气象台 nmc.cn</a> 7 天预报 · 预报发布 __PUBLISH__ · 页面生成 __GEN__ ·
    覆盖__PROVLINE__共 __TOTAL__ 站（地级市 __PREFN__ 个）<br>
    判定口径：<b>白天（08–20时）无雨即算无雨</b>，夜间降雨不影响结论；雨/雪/雷/雹均计为降水，阴/多云/雾/霾不算。
  </div>

  <div class="cards">
    <div class="card"><b>__TOTAL__</b><span>站点总数（__PROVLINE__）</span></div>
    <div class="card green"><b>__DRYN__</b><span>2026-10-02 ~ 2026-10-05 白天全程无雨</span></div>
    __KPIPROV__
  </div>

  <div class="hero">
    <h2>✅ 白天全程无雨名单（2026-10-02 ~ 2026-10-05）</h2>
    <div class="heroitems">__DRYHERO__</div>
    <p class="sub" style="margin:10px 0 0">备注：__STRICTNOTE__</p>
  </div>

  <h2 class="sec">📅 地级市逐日白天分布（标签按省份：苏/皖/浙/闽）</h2>
  <div class="daygrid">__DAYCARDS__</div>

  <h2 class="sec">🗂️ 全部站点明细（__TOTAL__ 站）</h2>
  <div class="filters">
    <select id="fprov"><option>全部</option>__PROVOPTS__</select>
    <select id="fres"><option value="all">全部结论</option><option value="dry">✅ 白天全程无雨</option><option value="r1">☔ 1天有雨</option><option value="r2">☔ 2天有雨</option><option value="r3">☔ ≥3天有雨</option></select>
    <select id="ftyp"><option value="all">全部类型</option><option value="pref">地级市</option><option value="cty">县级</option></select>
    <input id="fq" placeholder="搜索站点名…">
    <span class="cnt" id="cnt"></span>
  </div>
  <div class="tablewrap">
  <table>
    <thead><tr>
      <th class="sortable hfix" data-k="name">站点</th>
      <th class="hfix prov">省份</th>
      <th>类型</th>
      __HEADERS__
      <th class="sortable" data-k="dayRain">白天有雨(天)</th>
      <th class="sortable" data-k="precip">累计降水</th>
      <th>温度</th>
      <th>结论</th>
    </tr></thead>
    <tbody id="tb"></tbody>
  </table>
  </div>

  <div class="foot">
    <b>图例</b>：☀️晴 ⛅多云 ☁️阴 🌦️小雨 🌧️中雨及以上/降水 ⛈️雷阵雨 🌨️雪 🌫️雾/霾；每格为 白天 / 夜间，<span class="n">灰字</span>为夜间天气。<br>
    默认排序：白天无雨在前 → 地级市在前；点击“站点 / 白天有雨 / 累计降水”表头可切换排序。<br>
    淮安说明：NMC 清单中”淮安”有两条同名站点（DXKse / wVmjo，同页面、预报可能不同），官网城市页展示 wVmjo 的数据，本页收录该条、DXKse 不展示（2026-09-29 与官网核对）；今后若再现其他重名站点将自动加”②”区分。<br>
    预报为 3–6 天时效，雨带边缘落区变数大，建议 2026-10-01 晚在 nmc.cn 复核。重新抓取：运行本目录 fetch_all.py 后再跑 gen_html.py。
  </div>
</div>

<script>
const DATA = __DATA__;
const state = {prov:"全部", res:"all", typ:"all", q:"", sk:null, sd:1};
const RES = {dry:s=>s.dayRain===0, r1:s=>s.dayRain===1, r2:s=>s.dayRain===2, r3:s=>s.dayRain>=3};
const $ = id => document.getElementById(id);

function cellHTML(c){
  const cls = c.dr ? "rain" : "";
  const night = c.nr ? ' <span class="n">🌙'+c.nt+'</span>' : ' <span class="n">'+c.nt+'</span>';
  return '<td class="'+cls+'">'+c.dn+night+'</td>';
}
function rowsHTML(){
  const q = state.q.trim();
  let list = DATA.filter(s =>
    (state.prov==="全部" || s.prov===state.prov) &&
    (state.res==="all" || RES[state.res](s)) &&
    (state.typ==="all" || (state.typ==="pref" ? s.pref : !s.pref)) &&
    (!q || s.name.includes(q) || s.prov.includes(q)));
  const by = {
    name:(a,b)=>a.name.localeCompare(b.name,"zh"),
    dayRain:(a,b)=>a.dayRain-b.dayRain,
    precip:(a,b)=>a.precip-b.precip
  };
  if(state.sk){ list = list.slice().sort(by[state.sk]); if(state.sd<0) list.reverse(); }
  else list = list.slice().sort((a,b)=>
    (a.dryAll!==b.dryAll) ? (a.dryAll?-1:1) :
    (a.pref!==b.pref) ? (a.pref?-1:1) :
    (a.dayRain-b.dayRain) || (a.precip-b.precip) || a.name.localeCompare(b.name,"zh"));
  return list.map(s=>{
    const cells = s.cells.map(cellHTML).join("");
    const tag = s.dryAll ? '<span class="tag g">✅ 无雨</span>' : '<span class="tag b">☔ 有雨</span>';
    const typ = s.pref ? '<span class="tag p">地级市</span>' : '<span class="tag">县级</span>';
    return '<tr class="'+(s.dryAll?"dry":"")+'">'+
      '<td class="name"><a href="'+s.url+'" target="_blank">'+s.name+'</a></td>'+
      '<td class="prov">'+s.prov+'</td><td>'+typ+'</td>'+cells+
      '<td>'+(4-s.dayRain)+' / 4</td><td>'+s.precip+' mm</td><td>'+s.lo+'~'+s.hi+'°C</td><td>'+tag+'</td></tr>';
  }).join("");
}
function render(){
  $("tb").innerHTML = rowsHTML();
  const n = $("tb").querySelectorAll("tr").length;
  $("cnt").textContent = "显示 " + n + " / " + DATA.length + " 站";
}
$("fprov").onchange = e=>{state.prov=e.target.value; render();};
$("fres").onchange  = e=>{state.res=e.target.value; render();};
$("ftyp").onchange  = e=>{state.typ=e.target.value; render();};
$("fq").oninput     = e=>{state.q=e.target.value; render();};
document.querySelectorAll("th.sortable").forEach(th=>{
  th.onclick = ()=>{
    const k = th.dataset.k;
    if(state.sk===k) state.sd = -state.sd; else {state.sk=k; state.sd=1;}
    document.querySelectorAll("th.sortable").forEach(t=>t.textContent=t.textContent.replace(/[▲▼]/g,"").trim());
    th.innerHTML = th.textContent.replace(/[▲▼]/g,"").trim() + (state.sd>0?" ▲":" ▼");
    render();
  };
});
render();
</script>
</body>
</html>
"""

html = (html.replace("__DATA__", DATA_JSON)
            .replace("__PUBLISH__", pub)
            .replace("__GEN__", GEN)
            .replace("__TOTAL__", str(total))
            .replace("__PREFN__", str(pref_n))
            .replace("__PROVLINE__", prov_line)
            .replace("__KPIPROV__", kpi_prov)
            .replace("__DRYN__", str(len(dry)))
            .replace("__STRICTNOTE__", strict_note)
            .replace("__HEADERS__", headers)
            .replace("__DRYHERO__", dry_hero)
            .replace("__DAYCARDS__", "".join(daycards))
            .replace("__PROVOPTS__", prov_options))

out = "index.html"
open(out, "w", encoding="utf-8").write(html)
print("written", out, f"{len(html)} chars;", f"total={total}, dry={len(dry)}, strict={len(strict)}, publish={pub}")
