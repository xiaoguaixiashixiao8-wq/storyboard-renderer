# -*- coding: utf-8 -*-
"""通用分镜表生成器：读取项目目录下的 meta.json + data.json，输出单文件 HTML 分镜表。
用法：python build_storyboard.py 项目目录名
"""
import json, html, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
proj = sys.argv[1] if len(sys.argv) > 1 else ""
pdir = os.path.join(BASE, proj)
if not os.path.isdir(pdir):
    raise SystemExit("project dir not found: " + pdir)

with open(os.path.join(pdir, "meta.json"), "r", encoding="utf-8") as f:
    meta = json.load(f)
with open(os.path.join(pdir, "data.json"), "r", encoding="utf-8") as f:
    shots = json.load(f)

SIZE_ORDER = ["大远景", "远景", "全景", "中景", "近景", "特写"]
SIZE_CLASS = {
    "大远景": "wide", "远景": "wide", "全景": "wide",
    "中景": "medium", "中近景": "close", "近景": "close",
    "特写": "ecu", "大特写": "ecu",
}

total = len(shots)
counts = {}
for sh in shots:
    counts[sh["景别"]] = counts.get(sh["景别"], 0) + 1
order = [s for s in SIZE_ORDER if s in counts] + [s for s in counts if s not in SIZE_ORDER]
max_count = max(counts.values())

dialogue = [sh for sh in shots if not sh["台词"].startswith("（无")]
has_dialogue = len(dialogue) > 0
patched = [sh for sh in shots if sh.get("补镜")]
has_audio = any(sh.get("声音") for sh in shots)

size_summary = "·".join([k + str(counts[k]) for k in order])

# ---------- cards ----------
cards = []
for sh in shots:
    no = "%02d" % sh["镜号"]
    cls = SIZE_CLASS.get(sh["景别"], "wide")
    desc = html.escape(sh["画面描述"])
    flag = '<span class="shot-flag">补</span>' if sh.get("补镜") else ""
    audio = ""
    if has_audio and sh.get("声音"):
        audio = ('<p class="shot-audio"><span class="audio-tag">声音</span>'
                 + html.escape(sh["声音"]) + "</p>")
    line = sh["台词"]
    if line.startswith("（无"):
        line_html = '<p class="shot-noline">无台词</p>' if has_dialogue else ""
    else:
        line_html = (
            '<div class="shot-line">'
            '<span class="line-tag">台词</span>'
            "<p>" + html.escape(line) + "</p>"
            "</div>"
        )
    prompt = html.escape(sh["Midjourney英文提示词"])
    cards.append(
        '<article class="shot" id="shot-%s">\n'
        '  <div class="shot-rail">\n'
        '    <span class="shot-no">%s</span>\n'
        '    <span class="shot-size %s">%s</span>\n'
        "    %s\n"
        "  </div>\n"
        '  <div class="shot-main">\n'
        '    <p class="shot-desc">%s</p>\n'
        "    %s\n"
        "    %s\n"
        '    <details class="prompt">\n'
        '      <summary><span>Midjourney 提示词</span><span class="caret" aria-hidden="true"></span></summary>\n'
        '      <div class="prompt-body">\n'
        '        <pre id="prompt-%s">%s</pre>\n'
        '        <button class="copy" type="button" data-target="prompt-%s" aria-label="复制第%s镜提示词">复制</button>\n'
        "      </div>\n"
        "    </details>\n"
        "  </div>\n"
        "</article>"
        % (no, no, cls, html.escape(sh["景别"]), flag, desc, audio, line_html, no, prompt, no, no)
    )

nav_chips = "".join(
    '<a class="chip" href="#shot-%02d">%02d</a>' % (sh["镜号"], sh["镜号"]) for sh in shots
)

bars = "".join(
    '<li class="bar-row"><span class="bar-label">%s</span>'
    '<span class="bar-track"><span class="bar-fill %s" style="width:%d%%"></span></span>'
    '<span class="bar-val">%d</span></li>'
    % (k, SIZE_CLASS.get(k, "wide"), round(counts[k] / max_count * 100), counts[k])
    for k in order
)

kv_html = "".join(
    "      <dt>%s</dt><dd>%s</dd>\n" % (html.escape(a), html.escape(b)) for a, b in meta["kv"]
)

meta_chips = [
    "<li><b>%d</b> 个镜头</li>" % total,
    "<li>景别构成 <b>%s</b></li>" % size_summary,
    "<li>对白镜头 <b>%d</b></li>" % len(dialogue),
    "<li>画幅 <b>16:9</b></li>",
]
if patched:
    meta_chips.insert(3, "<li>补镜 <b>%d</b></li>" % len(patched))
meta_html = "\n    ".join(meta_chips)

CSS = """
:root{
  --bg:#0a0a0c; --panel:#111218; --panel-2:#171a22; --line:#262a35;
  --text:#e9e6e0; --muted:#9aa0ad; --dim:#6d7381;
  --gold:#c9a25a; --gold-soft:rgba(201,162,90,.14);
  --ice:#6fa8c7; --crimson:#b2454c;
  --serif:"Songti SC","Noto Serif SC",Georgia,"SimSun",serif;
  --sans:system-ui,-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  --mono:"SFMono-Regular",Consolas,"Liberation Mono",monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--text); font-family:var(--sans);
  line-height:1.65; overflow-x:hidden;
  background-image:radial-gradient(900px 500px at 12% -10%,rgba(201,162,90,.10),transparent 60%),
                   radial-gradient(700px 460px at 92% 0%,rgba(111,168,199,.08),transparent 60%);
  background-repeat:no-repeat;
}
.wrap{max-width:1180px;margin:0 auto;padding:0 clamp(16px,4vw,40px)}
:focus-visible{outline:2px solid var(--gold);outline-offset:3px;border-radius:4px}

.top{padding:clamp(38px,6vw,72px) 0 clamp(22px,3vw,32px);border-bottom:1px solid var(--line)}
.eyebrow{display:flex;align-items:center;gap:10px;font-size:12px;letter-spacing:.28em;
  text-transform:uppercase;color:var(--gold);margin:0 0 18px;font-weight:600}
.eyebrow::before{content:"";width:34px;height:1px;background:var(--gold);display:block}
h1{font-family:var(--serif);font-weight:700;font-size:clamp(32px,6vw,58px);
  line-height:1.1;margin:0 0 14px;letter-spacing:.02em}
h1 .thin{display:block;font-size:clamp(15px,2.4vw,20px);font-weight:400;color:var(--muted);
  letter-spacing:.22em;margin-top:14px;font-family:var(--sans)}
.logline{max-width:64ch;color:#c9c6bf;font-size:clamp(14px,1.6vw,16px);margin:0}
.meta{display:flex;flex-wrap:wrap;gap:10px;margin:26px 0 0;padding:0;list-style:none}
.meta li{font-size:12.5px;color:var(--muted);border:1px solid var(--line);
  background:var(--panel);padding:7px 13px;border-radius:999px;letter-spacing:.04em}
.meta li b{color:var(--text);font-weight:600;font-family:var(--serif);font-size:14px}

.overview{display:grid;gap:clamp(18px,3vw,34px);grid-template-columns:1fr;
  padding:clamp(24px,4vw,40px) 0;border-bottom:1px solid var(--line)}
@media(min-width:820px){.overview{grid-template-columns:1.15fr 1fr}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:clamp(18px,2.6vw,26px)}
.panel h2{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim);
  margin:0 0 18px;font-weight:600;font-family:var(--sans)}
.kv{margin:0;display:grid;grid-template-columns:auto 1fr;gap:10px 18px;font-size:14px}
.kv dt{color:var(--dim);white-space:nowrap;font-size:13px}
.kv dd{margin:0;color:#d5d2cb}
.bars{list-style:none;margin:0;padding:0;display:grid;gap:12px}
.bar-row{display:grid;grid-template-columns:58px 1fr 26px;align-items:center;gap:12px;font-size:13px}
.bar-label{color:var(--muted);letter-spacing:.06em;white-space:nowrap}
.bar-track{height:8px;background:#1d202a;border-radius:99px;overflow:hidden}
.bar-fill{display:block;height:100%;border-radius:99px;transform-origin:left}
.bar-fill.wide{background:linear-gradient(90deg,#8a6f36,var(--gold))}
.bar-fill.medium{background:linear-gradient(90deg,#4b5262,#8d94a4)}
.bar-fill.close{background:linear-gradient(90deg,#3f6a80,var(--ice))}
.bar-fill.ecu{background:linear-gradient(90deg,#6c2a2f,var(--crimson))}
.bar-val{text-align:right;color:var(--text);font-family:var(--serif);font-size:15px}

.toolbar{position:sticky;top:0;z-index:20;background:rgba(10,10,12,.9);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line);padding:12px 0}
.toolbar-inner{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.chips{display:flex;gap:6px;flex-wrap:wrap;flex:1 1 320px}
.chip{display:inline-flex;align-items:center;justify-content:center;min-width:34px;height:32px;
  padding:0 8px;font-family:var(--mono);font-size:12px;color:var(--muted);text-decoration:none;
  border:1px solid var(--line);border-radius:8px;background:var(--panel);
  transition:color .18s,border-color .18s,transform .18s}
.chip:hover{color:var(--gold);border-color:rgba(201,162,90,.55);transform:translateY(-1px)}
.btn{font:inherit;font-size:12.5px;color:var(--text);background:var(--panel-2);
  border:1px solid var(--line);border-radius:8px;padding:8px 14px;cursor:pointer;
  transition:border-color .18s,color .18s,transform .18s}
.btn:hover{border-color:rgba(201,162,90,.55);color:var(--gold)}
.btn:active{transform:scale(.97)}

.shots{list-style:none;margin:0;padding:clamp(26px,4vw,44px) 0 0;display:grid;gap:14px}
.shot{display:grid;grid-template-columns:64px 1fr;gap:clamp(14px,2.4vw,26px);
  background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:clamp(18px,2.6vw,26px);transition:border-color .2s,transform .2s;scroll-margin-top:96px}
.shot:hover{border-color:#333846;transform:translateY(-2px)}
.shot:target{border-color:rgba(201,162,90,.7);background:#15161d}
@media(min-width:760px){.shot{grid-template-columns:92px 1fr}}
.shot-rail{display:flex;flex-direction:column;align-items:flex-start;gap:10px;
  border-right:1px solid var(--line);padding-right:clamp(12px,2vw,20px)}
.shot-no{font-family:var(--serif);font-size:clamp(24px,3.6vw,34px);line-height:1;
  color:var(--gold);letter-spacing:.02em}
.shot-size{font-size:11.5px;letter-spacing:.14em;padding:3px 8px;border-radius:5px;
  border:1px solid;white-space:nowrap}
.shot-size.wide{color:var(--gold);border-color:rgba(201,162,90,.45);background:var(--gold-soft)}
.shot-size.medium{color:#a7aebc;border-color:rgba(167,174,188,.35);background:rgba(167,174,188,.08)}
.shot-size.close{color:var(--ice);border-color:rgba(111,168,199,.45);background:rgba(111,168,199,.1)}
.shot-size.ecu{color:#d57a80;border-color:rgba(178,69,76,.5);background:rgba(178,69,76,.12)}
.shot-flag{font-size:10.5px;letter-spacing:.12em;color:#d0a85f;border:1px dashed rgba(201,162,90,.5);
  border-radius:4px;padding:1px 6px}
.shot-main{min-width:0}
.shot-desc{margin:0;font-size:clamp(14.5px,1.7vw,16px);color:#dedbd4;line-height:1.78}
.shot-audio{display:flex;gap:10px;align-items:baseline;margin:12px 0 0;font-size:12.5px;color:#a8a08f}
.audio-tag{font-size:11px;letter-spacing:.16em;color:#8d8578;flex:0 0 auto;border:1px solid var(--line);
  border-radius:4px;padding:1px 6px}
.shot-line{display:flex;gap:12px;align-items:flex-start;margin:16px 0 0;
  border-left:2px solid var(--crimson);padding:2px 0 2px 14px}
.line-tag{font-size:11px;letter-spacing:.16em;color:#d57a80;flex:0 0 auto;padding-top:4px}
.shot-line p{margin:0;font-family:var(--serif);font-size:clamp(15px,1.9vw,17.5px);
  color:#f2ece2;letter-spacing:.02em}
.shot-noline{margin:14px 0 0;font-size:12px;color:var(--dim);letter-spacing:.14em}
.prompt{margin:16px 0 0;border-top:1px dashed var(--line);padding-top:12px}
.prompt summary{display:flex;align-items:center;justify-content:space-between;gap:12px;
  cursor:pointer;font-size:12px;letter-spacing:.14em;color:var(--dim);list-style:none}
.prompt summary::-webkit-details-marker{display:none}
.prompt summary:hover{color:var(--gold)}
.caret{width:8px;height:8px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;
  transform:rotate(45deg);transition:transform .2s;margin-right:4px}
.prompt[open] .caret{transform:rotate(-135deg)}
.prompt-body{position:relative;margin-top:12px}
.prompt pre{margin:0;padding:14px 14px 40px;background:#0c0d12;border:1px solid var(--line);
  border-radius:10px;font-family:var(--mono);font-size:12.5px;line-height:1.75;color:#b9c0cc;
  white-space:pre-wrap;overflow-wrap:anywhere;max-height:260px;overflow:auto}
.copy{position:absolute;right:10px;bottom:10px;font:inherit;font-size:11.5px;color:var(--muted);
  background:var(--panel-2);border:1px solid var(--line);border-radius:7px;padding:5px 11px;cursor:pointer;
  transition:color .18s,border-color .18s}
.copy:hover{color:var(--gold);border-color:rgba(201,162,90,.55)}
.copy.done{color:#7fbf9a;border-color:rgba(127,191,154,.5)}

.foot{margin:clamp(40px,6vw,72px) 0 0;padding:24px 0 56px;border-top:1px solid var(--line);
  display:flex;flex-wrap:wrap;gap:12px 28px;justify-content:space-between;font-size:12.5px;color:var(--dim)}
.foot p{margin:0;max-width:70ch}

@media print{
  :root{--bg:#fff;--panel:#fff;--panel-2:#fff;--line:#d6d6d6;--text:#111;--muted:#555;--dim:#666}
  body{background:#fff;color:#111;background-image:none}
  .toolbar,.copy{display:none!important}
  .shot{break-inside:avoid;page-break-inside:avoid;border:1px solid #ddd;transform:none!important}
  .shot-no{color:#8a6f36}
  .prompt pre{max-height:none;background:#f7f7f7;color:#222;border-color:#e2e2e2}
  .logline,.shot-desc{color:#222}
  .shot-line p{color:#111}
}
@media (prefers-reduced-motion:reduce){
  *{transition:none!important;animation:none!important}
  .shot:hover,.chip:hover{transform:none}
}
"""

JS = """
(function(){
  try{
    var all = document.querySelectorAll('details.prompt');
    var toggle = document.getElementById('toggle-all');
    if(toggle){
      toggle.addEventListener('click', function(){
        var open = toggle.getAttribute('data-state') !== 'open';
        for(var i=0;i<all.length;i++){ all[i].open = open; }
        toggle.setAttribute('data-state', open ? 'open' : 'closed');
        toggle.textContent = open ? '收起全部提示词' : '展开全部提示词';
      });
    }
    function fallback(text, done){
      try{
        var ta = document.createElement('textarea');
        ta.value = text; ta.setAttribute('readonly','');
        ta.style.position='fixed'; ta.style.opacity='0';
        document.body.appendChild(ta); ta.select();
        document.execCommand('copy'); document.body.removeChild(ta); done();
      }catch(err2){
        var b = document.querySelector('.copy');
        if(b){ b.textContent = '请手动选择复制'; }
      }
    }
    document.addEventListener('click', function(e){
      var btn = e.target.closest ? e.target.closest('.copy') : null;
      if(!btn) return;
      var pre = document.getElementById(btn.getAttribute('data-target'));
      if(!pre) return;
      var text = pre.textContent || '';
      var done = function(){
        var old = btn.textContent;
        btn.textContent = '已复制';
        btn.classList.add('done');
        setTimeout(function(){ btn.textContent = old; btn.classList.remove('done'); }, 1600);
      };
      try{
        if(navigator.clipboard && navigator.clipboard.writeText){
          navigator.clipboard.writeText(text).then(done, function(){ fallback(text, done); });
        } else { fallback(text, done); }
      }catch(err){ fallback(text, done); }
    });
    var links = document.querySelectorAll('a.chip');
    for(var i=0;i<links.length;i++){
      links[i].addEventListener('click', function(ev){
        var id = this.getAttribute('href').slice(1);
        var target = document.getElementById(id);
        if(!target) return;
        ev.preventDefault();
        target.scrollIntoView({behavior:'smooth', block:'start'});
      });
    }
    var reopened = [];
    window.addEventListener('beforeprint', function(){
      reopened = [];
      for(var j=0;j<all.length;j++){
        if(!all[j].open){ reopened.push(all[j]); all[j].open = true; }
      }
    });
    window.addEventListener('afterprint', function(){
      for(var k=0;k<reopened.length;k++){ reopened[k].open = false; }
      reopened = [];
    });
  }catch(e){}
})();
"""

HTML = (
    '<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    "<title>__TITLE__ · 短剧分镜表（__TOTAL__ 镜）</title>\n"
    "<style>__CSS__</style>\n</head>\n<body>\n"
    '<div class="wrap">\n'
    '<header class="top">\n'
    '  <p class="eyebrow">__EYEBROW__</p>\n'
    '  <h1>__TITLE__<span class="thin">__SUBTITLE__</span></h1>\n'
    '  <p class="logline">__LOGLINE__</p>\n'
    '  <ul class="meta">\n    __META__\n  </ul>\n'
    "</header>\n"
    '<section class="overview" aria-label="分镜概览">\n'
    '  <div class="panel">\n'
    "    <h2>场景与人物</h2>\n"
    '    <dl class="kv">\n__KV__    </dl>\n'
    "  </div>\n"
    '  <div class="panel">\n'
    "    <h2>景别分布</h2>\n"
    '    <ul class="bars">__BARS__</ul>\n'
    "  </div>\n"
    "</section>\n"
    "</div>\n"
    '<div class="toolbar">\n<div class="wrap toolbar-inner">\n'
    '<nav class="chips" aria-label="镜头索引">__NAV__</nav>\n'
    '<button class="btn" id="toggle-all" type="button" data-state="closed">展开全部提示词</button>\n'
    "</div>\n</div>\n"
    '<div class="wrap">\n'
    "<main>\n"
    '<ol class="shots">\n__CARDS__\n</ol>\n'
    "</main>\n"
    '<footer class="foot">\n'
    "  <p>__FOOTNOTE__</p>\n"
    "  <p>点击镜号可跳转 · 提示词支持一键复制</p>\n"
    "</footer>\n"
    "</div>\n"
    "<script>__JS__</script>\n"
    "</body>\n</html>\n"
)

HTML = (HTML
        .replace("__TITLE__", html.escape(meta["title"]))
        .replace("__SUBTITLE__", html.escape(meta["subtitle"]))
        .replace("__EYEBROW__", html.escape(meta["eyebrow"]))
        .replace("__LOGLINE__", html.escape(meta["logline"]))
        .replace("__META__", meta_html)
        .replace("__KV__", kv_html)
        .replace("__BARS__", bars)
        .replace("__NAV__", nav_chips)
        .replace("__CARDS__", "\n".join(cards))
        .replace("__FOOTNOTE__", html.escape(meta["footnote"]))
        .replace("__TOTAL__", str(total))
        .replace("__CSS__", CSS)
        .replace("__JS__", JS))

out = os.path.join(pdir, meta["file_name"])
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("written:", out)
print("shots:", total, "| sizes:", counts, "| dialogue:", len(dialogue), "| patched:", len(patched))
