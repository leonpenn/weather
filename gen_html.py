# -*- coding: utf-8 -*-
"""从 wx_*.json 生成自包含 index.html 速查页（江苏/安徽/浙江/福建）。
日期范围动态：日期列表取自数据源 7 天预报实际提供的全部日期，
用户在页面上选择起始/结束日期（起始不早于昨日、截止为预报可提供的最远日期），
页面在浏览器端按所选范围实时重算无雨结论、名单与统计。"""
import json, datetime

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

stations, pub = [], ""
for f, prov_expect in PROV_FILES:
    for s in json.load(open(f, encoding="utf-8")):
        if s["code"] in HIDDEN_STATIONS: continue
        stations.append({"code": s["code"], "url": s["url"], "prov_expect": prov_expect})

payloads, all_dates = [], set()
for s in stations:
    j = json.load(open(f"data/wx_{s['code']}.json", encoding="utf-8"))
    p = j["data"]["predict"]; st = p["station"]
    assert st["province"].replace("省", "") == s["prov_expect"], \
        f"省份不符: {st['city']} {st['province']} != {s['prov_expect']}"
    pub = max(pub, p.get("publish_time") or "")
    for d in p["detail"]:
        all_dates.add(d["date"])
    payloads.append((s, p))

DATES = sorted(all_dates)
assert DATES, "数据源未返回任何预报日期"

data = []
for s, p in payloads:
    st = p["station"]
    daymap = {d["date"]: d for d in p["detail"]}
    cells = {}
    for dt in DATES:
        d = daymap.get(dt)
        if d is None:  # 全国同批次发布，正常不会缺日；兜底跳过
            continue
        dn, nt = d["day"]["weather"]["info"], d["night"]["weather"]["info"]
        td = int(d["day"]["weather"]["temperature"] or 0)
        tn = int(d["night"]["weather"]["temperature"] or 0)
        cells[dt] = {"dn": dn, "nt": nt,
                     "dr": any(k in dn for k in WET), "nr": any(k in nt for k in WET),
                     "pr": float(d.get("precipitation") or 0),
                     "td": td if td < 100 else None,   # NMC 缺测时段用 9999 哨兵值填充
                     "tn": tn if tn < 100 else None}
    data.append({"name": st["city"], "prov": st["province"].replace("省", ""),
                 "pref": st["city"] in PREF, "url": "https://www.nmc.cn" + st["url"], "cells": cells})

# 站点重名时，后者自动加"②"区分
seen = set()
for s in data:
    if s["name"] in seen: s["name"] += "②"
    seen.add(s["name"])

data.sort(key=lambda s: (PROV_ORDER.index(s["prov"]) if s["prov"] in PROV_ORDER else 9, s["name"]))

total = len(data)
pref_n = sum(s["pref"] for s in data)
per_prov = {pv: {"n": sum(1 for s in data if s["prov"] == pv),
                 "pref": sum(1 for s in data if s["prov"] == pv and s["pref"])} for pv in PROV_ORDER}
prov_line = " · ".join(f"{pv} {per_prov[pv]['n']}" for pv in PROV_ORDER)

DATA_JSON = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
DATES_JSON = json.dumps(DATES)
GEN = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")  # 北京时间（CI runner 时区为 UTC，直接取会差 8 小时）

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>不下雨的旅游目的地 · 江浙皖闽</title>
<style>
:root{--ink:#1c2733;--mut:#6b7a89;--line:#e3e9ef;--bg:#f6f8fa;--green:#0e9f6e;--greenbg:#e6f7f0;--blue:#3b82c4;--bluebg:#e9f2fb;--graybg:#eef1f5}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink)}
.wrap{max-width:1150px;margin:0 auto;padding:22px 16px 60px}
h1{font-size:22px;margin:6px 0 4px}
.sub{color:var(--mut);font-size:13px;line-height:1.7;margin-bottom:16px}
.sub a{color:var(--blue)}
.sub b{color:var(--ink)}
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
.filters select,.filters input,.rangepick select,.rangepick input{padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:13px;color:var(--ink)}
.rangepick{margin:8px 0 2px}
.rangepick .hint{color:var(--mut);font-size:12px;margin-left:8px}
.filters input{width:150px}
.filters .rangelbl{font-size:13px;color:var(--mut)}
.filters .cnt{color:var(--mut);font-size:12.5px;margin-left:auto}
.navbtn{display:inline-block;padding:3px 12px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--ink);text-decoration:none;font-size:12.5px;margin:2px 6px 2px 0}
.navbtn:hover{color:var(--blue);border-color:var(--blue)}
[id]{scroll-margin-top:56px}
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
  <h1>🌧️→☀️ 不下雨的旅游目的地 · 江浙皖闽</h1>
  <div class="sub">
    当前范围：<b id="rglabel">__RANGE0__</b> · 数据源：<a href="https://www.nmc.cn" target="_blank">中央气象台 nmc.cn</a> 7 天预报 · 预报发布 __PUBLISH__ · 页面生成 __GEN__ ·
    覆盖__PROVLINE__共 __TOTAL__ 站（地级市 __PREFN__ 个）<br>
    判定口径：<b>所选日期范围内，白天（08–20时）无雨即算无雨</b>，夜间降雨不影响结论；雨/雪/雷/雹均计为降水，阴/多云/雾/霾不算。
    范围可选：起始不早于昨日（数据源预报自今日起，若含昨日会自动出现在选项中），截止为预报可提供的最远日期。
    <div class="rangepick"><span class="rangelbl">分析日期范围</span>
      <select id="dfrom"></select>
      <span class="rangelbl">至</span>
      <select id="dto"></select>
      <span class="hint">对整页所有数字生效，改动后实时重算</span>
    </div><br>
    快速跳转：<a class="navbtn" href="#hero">✅ 白天全程无雨名单</a><a class="navbtn" href="#sec-days">📅 地级市逐日白天分布</a><a class="navbtn" href="#sec-table">🗂️ 全部站点明细</a>
  </div>

  <div class="cards">
    <div class="card"><b>__TOTAL__</b><span>站点总数（__PROVLINE__）</span></div>
    <div class="card green"><b id="dryn">–</b><span id="drynl">当前范围白天全程无雨</span></div>
    <div id="kpiprov" style="display:contents"></div>
  </div>

  <div class="hero" id="hero">
    <h2>✅ 白天全程无雨名单（<span id="herorange"></span>）</h2>
    <div class="heroitems" id="heroitems"></div>
    <p class="sub" style="margin:10px 0 0" id="strnote"></p>
  </div>

  <h2 class="sec" id="sec-days">📅 地级市逐日白天分布（标签按省份：苏/皖/浙/闽）</h2>
  <div class="daygrid" id="daygrid"></div>

  <h2 class="sec" id="sec-table">🗂️ 全部站点明细（__TOTAL__ 站）</h2>
  <div class="filters">
    <span class="rangelbl">省份</span>
    <select id="fprov"><option>全部</option></select>
    <select id="fres"><option value="all">全部结论</option><option value="dry">✅ 白天全程无雨</option><option value="r1">☔ 1天有雨</option><option value="r2">☔ 2天有雨</option><option value="r3">☔ ≥3天有雨</option></select>
    <input id="fq" placeholder="搜索站点名…">
    <span class="cnt" id="cnt"></span>
  </div>
  <div class="tablewrap">
  <table>
    <thead id="thr"></thead>
    <tbody id="tb"></tbody>
  </table>
  </div>

  <div class="foot">
    <b>图例</b>：☀️晴 ⛅多云 ☁️阴 🌦️小雨 🌧️中雨及以上/降水 ⛈️雷阵雨 🌨️雪 🌫️雾/霾；每格为 白天 / 夜间，<span class="n">灰字</span>为夜间天气。<br>
    默认排序：当前范围白天无雨在前 → 地级市在前；点击“站点 / 白天有雨 / 累计降水”表头可切换排序。<br>
    淮安说明：NMC 清单中“淮安”有两条同名站点（DXKse / wVmjo，同页面、预报可能不同），官网城市页展示 wVmjo 的数据，本页收录该条、DXKse 不展示（2026-09-29 与官网核对）；今后若再现其他重名站点将自动加“②”区分。<br>
    预报最长 7 天时效，雨带边缘落区变数大，出行前一晚在 nmc.cn 复核。重新抓取：运行本目录 fetch_all.py 后再跑 gen_html.py。
  </div>
</div>

<script>
const DATES = __DATES__;
const DATA = __DATA__;
const PROVS = ["江苏", "安徽", "浙江", "福建"];
const PROVSHORT = {"江苏":"苏","安徽":"皖","浙江":"浙","福建":"闽"};
const PROVIDX = {"江苏":0,"安徽":1,"浙江":2,"福建":3};
const WEEK = ["周日","周一","周二","周三","周四","周五","周六"];
const state = {start:DATES[0], end:DATES[DATES.length-1], prov:"全部", res:"all", q:"", sk:null, sd:1};
const RES = {dry:s=>s.m.dayRain===0, r1:s=>s.m.dayRain===1, r2:s=>s.m.dayRain===2, r3:s=>s.m.dayRain>=3};
const $ = id => document.getElementById(id);

function wd(ds){const p=ds.split("-");return WEEK[new Date(+p[0],+p[1]-1,+p[2]).getDay()]}
function selDates(){return DATES.filter(d=>d>=state.start && d<=state.end)}
function derive(s){
  let dayRain=0, precip=0, lo=999, hi=-999, dryAll=true, dryStrict=true;
  for(const dt of DATES){
    if(dt<state.start||dt>state.end) continue;
    const c=s.cells[dt]; if(!c) continue;
    if(c.dr){dayRain++;dryAll=false}
    if(c.dr||c.nr)dryStrict=false;
    precip+=c.pr;
    for(const t of [c.td,c.tn]){
      if(t===null) continue;
      lo=Math.min(lo,t); hi=Math.max(hi,t);
    }
  }
  return {dayRain, precip:Math.round(precip*10)/10, lo:lo===999?null:lo, hi:hi===-999?null:hi, dryAll, dryStrict};
}
let M = new Map();
function recompute(){M = new Map(DATA.map(s=>[s,derive(s)]))}

function cellHTML(dt,s){
  const c = s.cells[dt];
  if(!c) return '<td class="mut">—</td>';
  const night = ' <span class="n">'+(c.nr?'🌙':'')+c.nt+'</span>';
  return '<td class="'+(c.dr?'rain':'')+'">'+c.dn+night+'</td>';
}
function buildHead(){
  let h = '<tr><th class="sortable hfix" data-k="name">站点</th><th class="hfix prov">省份</th><th>类型</th>';
  for(const dt of selDates()) h += '<th>'+dt+'<br><small>'+wd(dt)+'</small></th>';
  h += '<th class="sortable" data-k="precip">累计降水</th><th>温度</th><th>结论</th></tr>';
  $("thr").innerHTML = h;
  document.querySelectorAll("th.sortable").forEach(th=>{
    const k = th.dataset.k;
    if(state.sk===k) th.innerHTML = th.innerHTML.replace(/[▲▼]/g,"").trimEnd() + (state.sd>0?" ▲":" ▼");
    th.onclick = ()=>{
      if(state.sk===k) state.sd = -state.sd; else {state.sk=k; state.sd=1;}
      renderBody();
    };
  });
}
function rowsHTML(){
  const q = state.q.trim();
  let list = DATA.filter(s=>{
    const m = M.get(s);
    return (state.prov==="全部" || s.prov===state.prov) &&
      (state.res==="all" || RES[state.res]({m:m})) &&
      (!q || s.name.includes(q) || s.prov.includes(q));
  });
  const by = {
    name:(a,b)=>a.name.localeCompare(b.name,"zh"),
    dayRain:(a,b)=>M.get(a).dayRain-M.get(b).dayRain,
    precip:(a,b)=>M.get(a).precip-M.get(b).precip
  };
  if(state.sk){ list = list.slice().sort(by[state.sk]); if(state.sd<0) list.reverse(); }
  else list = list.slice().sort((a,b)=>{
    const ma=M.get(a), mb=M.get(b);
    return (ma.dryAll!==mb.dryAll) ? (ma.dryAll?-1:1) :
      (a.pref!==b.pref) ? (a.pref?-1:1) :
      (ma.dayRain-mb.dayRain) || (ma.precip-mb.precip) || a.name.localeCompare(b.name,"zh");
  });
  return list.map(s=>{
    const m = M.get(s);
    const cells = selDates().map(dt=>cellHTML(dt,s)).join("");
    const tag = m.dryAll ? '<span class="tag g">✅ 无雨</span>' : '<span class="tag b">☔ 有雨</span>';
    const typ = s.pref ? '<span class="tag p">地级市</span>' : '<span class="tag">县级</span>';
    const temp = m.lo===null ? '—' : m.lo+'~'+m.hi+'°C';
    return '<tr class="'+(m.dryAll?"dry":"")+'">'+
      '<td class="name"><a href="'+s.url+'" target="_blank">'+s.name+'</a></td>'+
      '<td class="prov">'+s.prov+'</td><td>'+typ+'</td>'+cells+
      '<td>'+m.precip+' mm</td><td>'+temp+'</td><td>'+tag+'</td></tr>';
  }).join("");
}
function renderBody(){
  $("tb").innerHTML = rowsHTML();
  $("cnt").textContent = "显示 " + $("tb").querySelectorAll("tr").length + " / " + DATA.length + " 站";
}
function renderStats(){
  const rg = state.start === state.end ? state.start : state.start + " ~ " + state.end;
  $("rglabel").textContent = rg;
  $("herorange").textContent = rg;
  let dryn=0, strict=[], extra=[];
  for(const s of DATA){
    const m = M.get(s);
    if(m.dryAll){ dryn++; if(!m.dryStrict) extra.push(PROVSHORT[s.prov]+"·"+s.name); }
  }
  $("dryn").textContent = dryn;
  const kp = PROVS.map(pv=>{
    const list = DATA.filter(s=>s.prov===pv);
    const dry = list.filter(s=>M.get(s).dryAll).length;
    const pref = list.filter(s=>s.pref).length;
    return '<div class="card'+(dry?" green":"")+'"><b>'+dry+' / '+list.length+'</b><span>'+pv+'无雨站 / 总站（地级市 '+pref+'）</span></div>';
  }).join("");
  $("kpiprov").outerHTML = '<div id="kpiprov" style="display:contents">'+kp+'</div>';
  const dry = DATA.filter(s=>M.get(s).dryAll).sort((a,b)=>{
    const ma=M.get(a), mb=M.get(b);
    return (a.pref!==b.pref)?(a.pref?-1:1):(PROVIDX[a.prov]-PROVIDX[b.prov])|| (ma.precip-mb.precip) || a.name.localeCompare(b.name,"zh");
  });
  $("heroitems").innerHTML = dry.length ? dry.map(s=>{
    const m = M.get(s);
    return '<div class="heroitem"><b>'+PROVSHORT[s.prov]+'·'+s.name+'</b><span>'+s.prov+' · '+(s.pref?"地级市":"县级")+'</span>'+
      '<em>'+m.lo+'~'+m.hi+'°C · 累计降水 '+m.precip+' mm</em></div>';
  }).join("") : '<span class="mut">—</span>';
  const nStrict = DATA.filter(s=>M.get(s).dryStrict).length;
  $("strnote").innerHTML = (nStrict===dryn)
    ? "备注：若把夜间降雨也计入，名单完全相同（"+nStrict+" 站）——所选范围内无“只下夜雨”的站点。"
    : "备注：若把夜间降雨也计入，无雨站为 "+nStrict+" 站；白天口径下有夜间降雨的 "+dryn+" 站："+extra.join("、")+"。";
  const dgs = selDates().map(dt=>{
    let secs = "";
    for(const pv of PROVS){
      const dryc=[], wetc=[];
      for(const s of DATA){
        if(!s.pref || s.prov!==pv) continue;
        const c = s.cells[dt];
        (c && c.dr ? wetc : dryc).push(s.name);
      }
      const chips = a=>a.map(n=>'<span class="chip g">'+n+'</span>').join("");
      const chipb = a=>a.map(n=>'<span class="chip b">'+n+'</span>').join("");
      secs += '<p class="lbl">'+PROVSHORT[pv]+' ☀️无雨 '+dryc.length+' · 🌧️有雨 '+wetc.length+'</p><div>'+
        (dryc.length?chips(dryc):'<span class="mut">—</span>')+'<span class="sep"></span>'+(wetc.length?chipb(wetc):'<span class="mut">—</span>')+'</div>';
    }
    return '<div class="daycard"><h3>'+dt+' '+wd(dt)+'（白天）</h3>'+secs+'</div>';
  }).join("");
  $("daygrid").innerHTML = dgs;
}
function renderAll(){ buildHead(); renderStats(); renderBody(); }

// 日期范围选择器：起始不早于昨日（数据源自今日起，选项即数据实际提供的日期）
for(const id of ["dfrom","dto"]){
  $(id).innerHTML = DATES.map(d=>'<option value="'+d+'">'+d+' '+wd(d)+'</option>').join("");
}
$("dfrom").value = state.start; $("dto").value = state.end;
$("dfrom").onchange = e=>{
  state.start = e.target.value;
  if(state.end < state.start){ state.end = state.start; $("dto").value = state.end; }
  recompute(); renderAll();
};
$("dto").onchange = e=>{
  state.end = e.target.value;
  if(state.end < state.start){ state.start = state.end; $("dfrom").value = state.start; }
  recompute(); renderAll();
};
$("fprov").innerHTML = '<option>全部</option>' + PROVS.map(p=>'<option>'+p+'</option>').join("");
$("fprov").onchange = e=>{state.prov=e.target.value; renderBody();};
$("fres").onchange  = e=>{state.res=e.target.value; renderBody();};
$("fq").oninput     = e=>{state.q=e.target.value; renderBody();};
recompute(); renderAll();
</script>
</body>
</html>
"""

html = (html.replace("__DATA__", DATA_JSON)
            .replace("__DATES__", DATES_JSON)
            .replace("__PUBLISH__", pub)
            .replace("__GEN__", GEN)
            .replace("__TOTAL__", str(total))
            .replace("__PREFN__", str(pref_n))
            .replace("__PROVLINE__", prov_line)
            .replace("__RANGE0__", DATES[0] + " ~ " + DATES[-1]))

out = "index.html"
open(out, "w", encoding="utf-8").write(html)
print("written", out, f"{len(html)} chars;", f"total={total}, dates={DATES[0]}~{DATES[-1]} ({len(DATES)}天), publish={pub}")
