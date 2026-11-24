"""Giao diện HTML/CSS/JS cho bản web (nhúng sẵn, không cần file ngoài)."""

from flask import render_template_string


def page(tpl: str, **ctx) -> str:
    # render_template_string tự escape biến -> an toàn với chuỗi do người dùng nhập
    return render_template_string(BASE_HTML.replace("{BODY}", tpl), **ctx)


BASE_HTML = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0d1014">
<meta name="robots" content="noindex">
<title>Tapo Viewer</title>
<style>
:root{--bg:#0d1014;--panel:#171b21;--panel2:#1f242c;--line:#2a313b;--text:#e8ecf1;--muted:#8b95a3;
--accent:#2f8cff;--accent2:#1f6fd6;--rec:#ff3b30;--ok:#30d158;--warn:#ffb020;--radius:12px}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
button,input,select{font:inherit;color:inherit}
a{color:inherit;text-decoration:none}
button{white-space:nowrap;cursor:pointer;border:1px solid var(--line);background:var(--panel2);border-radius:9px;padding:8px 12px}
button:hover{border-color:#3a4452}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button.primary:hover{background:var(--accent2)}
button.danger{color:#ff6b62}
button.on{background:var(--accent);border-color:var(--accent);color:#fff}
button.rec-on{background:var(--rec);border-color:var(--rec);color:#fff}
input,select{background:#0f1318;border:1px solid var(--line);border-radius:9px;padding:9px 11px;width:100%}
input:focus,select:focus{outline:2px solid var(--accent);outline-offset:-1px}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 4px}
.muted{color:var(--muted)}
.err{background:#3a1416;border:1px solid #6b2226;color:#ffb4ae;padding:9px 12px;border-radius:9px;margin:10px 0}
/* auth */
.auth{min-height:100vh;display:grid;place-items:center;padding:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:26px;width:100%;max-width:380px}
.card h1{margin:0 0 4px;font-size:22px}
.card button{width:100%;margin-top:18px;padding:11px}
.logo{width:44px;height:44px;border-radius:12px;background:var(--accent);display:grid;place-items:center;margin-bottom:14px}
/* app */
header{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:8px;padding:10px 14px;
background:rgba(13,16,20,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
header h1{font-size:17px;margin:0 auto 0 0;display:flex;align-items:center;gap:8px}
header .user{color:var(--muted);font-size:13px}
.grid{display:grid;gap:8px;padding:8px;grid-template-columns:repeat(auto-fill,minmax(min(100%,420px),1fr))}
.grid.cols-1{grid-template-columns:1fr}
.grid.cols-2{grid-template-columns:repeat(2,1fr)}
.grid.cols-3{grid-template-columns:repeat(3,1fr)}
@media (max-width:700px){.grid.cols-2,.grid.cols-3{grid-template-columns:1fr}}
.tile{position:relative;background:#000;border-radius:var(--radius);overflow:hidden;aspect-ratio:16/9;cursor:pointer;border:1px solid var(--line)}
.tile img,.viewer img{width:100%;height:100%;object-fit:contain;display:block}
.cap{position:absolute;left:0;right:0;top:0;padding:8px 10px;display:flex;gap:8px;align-items:center;
background:linear-gradient(#000a,#0000);font-size:13px;pointer-events:none}
.dot{width:8px;height:8px;border-radius:50%;background:var(--warn);flex:none}
.dot.ok{background:var(--ok)}
.rec{color:var(--rec);font-weight:600;margin-left:auto}
.overlay-msg{position:absolute;inset:0;display:grid;place-items:center;color:var(--muted);font-size:14px;text-align:center;padding:20px;pointer-events:none}
.empty{padding:60px 20px;text-align:center;color:var(--muted)}
/* viewer */
.viewer{position:fixed;inset:0;z-index:20;background:#000;display:none;flex-direction:column}
.viewer.open{display:flex}
.vtop{display:flex;align-items:center;gap:8px;padding:10px 12px;background:#0b0d10;border-bottom:1px solid var(--line)}
.vtop b{margin-right:auto}
.vbody{flex:1;display:flex;min-height:0}
.vimg{flex:1;position:relative;min-width:0}
.vside{width:250px;background:var(--panel);border-left:1px solid var(--line);padding:14px;overflow:auto}
@media (max-width:800px){.vbody{flex-direction:column}.vimg{flex:none;aspect-ratio:16/9;max-height:60vh}
.vside{flex:1;width:auto;border-left:0;border-top:1px solid var(--line)}}
@media (max-width:600px){header{gap:6px;padding:8px 10px}header h1{font-size:15px}header .user,.hide-sm{display:none}
header button,header select{padding:7px 9px}}
.pad{display:grid;grid-template-columns:repeat(3,52px);grid-template-rows:repeat(3,52px);gap:6px;justify-content:center;margin:6px 0 12px}
.pad button{padding:0;font-size:18px}
.row{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}
.row>*{flex:1}
h3{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:16px 0 6px}
/* settings */
.sheet{position:fixed;inset:0;z-index:30;background:#000a;display:none;align-items:flex-start;justify-content:center;padding:16px;overflow:auto}
.sheet.open{display:flex}
.sheet .box{background:var(--panel);border:1px solid var(--line);border-radius:16px;width:100%;max-width:640px;padding:20px}
.list{border:1px solid var(--line);border-radius:10px;overflow:hidden}
.item{display:flex;align-items:center;gap:8px;padding:10px 12px;border-top:1px solid var(--line)}
.item:first-child{border-top:0}
.item .grow{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.form2{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}
@media (max-width:560px){.form2{grid-template-columns:1fr}}
.toast{position:fixed;left:50%;bottom:20px;transform:translateX(-50%);background:#222a35;border:1px solid var(--line);
padding:10px 16px;border-radius:10px;z-index:50;max-width:92vw;display:none}
.toast.show{display:block}
.toast.bad{border-color:#6b2226;background:#3a1416}
</style>
</head>
<body>{BODY}</body>
</html>"""

_LOGO = ('<div class="logo"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" '
         'stroke-width="2"><circle cx="12" cy="11" r="7"/><circle cx="12" cy="11" r="3"/><path d="M8 21h8"/></svg></div>')

LOGIN_HTML = """<div class="auth"><form class="card" method="post" autocomplete="on">""" + _LOGO + """
<h1>Đăng nhập</h1><div class="muted">Tapo Viewer – xem camera</div>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
<label>Tên đăng nhập</label><input name="username" autocomplete="username" required autofocus>
<label>Mật khẩu</label><input name="password" type="password" autocomplete="current-password" required>
<button class="primary">Đăng nhập</button></form></div>"""

SETUP_HTML = """<div class="auth"><form class="card" method="post">""" + _LOGO + """
<h1>Tạo tài khoản quản trị</h1>
<div class="muted">Lần đầu sử dụng. Tài khoản này dùng để đăng nhập xem camera từ trình duyệt.</div>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
<label>Tên đăng nhập</label><input name="username" autocomplete="username" required autofocus maxlength="32">
<label>Mật khẩu (ít nhất 8 ký tự)</label><input name="password" type="password" autocomplete="new-password" required minlength="8">
<label>Nhập lại mật khẩu</label><input name="password2" type="password" autocomplete="new-password" required minlength="8">
<button class="primary">Tạo tài khoản</button></form></div>"""

MAIN_HTML = """
<header>
  <h1>""" + _LOGO.replace('class="logo"', 'class="logo" style="width:30px;height:30px;margin:0;border-radius:8px"') + """Tapo Viewer</h1>
  <select id="layout" title="Bố cục" style="width:auto">
    <option value="auto">Tự động</option><option value="1">1 cột</option>
    <option value="2">2 cột</option><option value="3">3 cột</option>
  </select>
  <button id="btnSettings" hidden title="Cài đặt">⚙<span class="hide-sm"> Cài đặt</span></button>
  <span class="user" id="who"></span>
  <form method="post" action="/logout" style="margin:0"><button>Đăng xuất</button></form>
</header>
<main id="grid" class="grid"></main>

<section class="viewer" id="viewer">
  <div class="vtop">
    <button id="vClose">← Quay lại</button><b id="vName"></b>
    <button id="vHd" title="Chất lượng">HD</button>
    <button id="vFull" title="Toàn màn hình">⛶</button>
  </div>
  <div class="vbody">
    <div class="vimg"><img id="vImg" alt=""><div class="overlay-msg" id="vMsg"></div></div>
    <aside class="vside">
      <div class="row"><a id="vSnap" download><button type="button" style="width:100%">📷 Chụp ảnh</button></a>
        <button id="vRec" class="admin">⏺ Ghi hình</button></div>
      <div id="ptzBox">
        <h3>Xoay camera</h3>
        <div class="pad">
          <span></span><button data-m="0,1">▲</button><span></span>
          <button data-m="-1,0">◀</button><button id="vCal" class="admin" title="Hiệu chỉnh">⟲</button><button data-m="1,0">▶</button>
          <span></span><button data-m="0,-1">▼</button><span></span>
        </div>
        <label>Bước xoay: <span id="stepV">15</span>°</label>
        <input type="range" id="step" min="5" max="60" value="15">
        <div class="row" style="margin-top:10px"><button id="vPresets">📍 Vị trí đã lưu</button>
          <button id="vSavePreset" class="admin">+ Lưu vị trí</button></div>
        <div id="presetList"></div>
        <div class="admin">
          <h3>Camera</h3>
          <div class="row"><button id="vPrivOn">🔒 Bật riêng tư</button><button id="vPrivOff">🔓 Tắt riêng tư</button></div>
          <div class="row"><button id="vLedOn">💡 Bật LED</button><button id="vLedOff">Tắt LED</button></div>
          <label>Hồng ngoại / ban đêm</label>
          <select id="vNight"><option value="">— chọn —</option><option value="auto">Tự động</option>
            <option value="on">Luôn bật</option><option value="off">Tắt</option></select>
        </div>
      </div>
      <p class="muted" style="font-size:12px;margin-top:16px">Phím tắt: mũi tên = xoay, Esc = quay lại.</p>
    </aside>
  </div>
</section>

<section class="sheet" id="settings"><div class="box">
  <div style="display:flex;align-items:center"><h2 style="margin:0 auto 0 0">Cài đặt</h2><button id="sClose">Đóng</button></div>
  <h3>Camera</h3><div class="list" id="camList"></div>
  <form id="camForm" style="margin-top:10px">
    <b id="camFormTitle">Thêm camera</b>
    <div class="form2">
      <div><label>Tên camera</label><input name="name" placeholder="Tầng G" maxlength="40"></div>
      <div><label>Địa chỉ IP</label><input name="ip" placeholder="192.168.1.50"></div>
      <div><label>Tài khoản camera (Camera Account)</label><input name="username" autocomplete="off"></div>
      <div><label>Mật khẩu camera</label><input name="password" type="password" autocomplete="new-password"></div>
      <div><label>Chất lượng</label><select name="stream"><option value="stream1">HD 1080p (stream1)</option>
        <option value="stream2">SD 360p (stream2) – nhẹ</option></select></div>
      <div><label>Cổng RTSP</label><input name="port" value="554" inputmode="numeric"></div>
      <div><label>Mật khẩu TP-Link (để xoay camera)</label><input name="cloud_password" type="password" autocomplete="new-password"></div>
      <div><label>URL tùy chỉnh (không bắt buộc)</label><input name="custom_url"></div>
    </div>
    <p class="muted" style="font-size:12px" id="pwHint" hidden>Để trống ô mật khẩu = giữ mật khẩu cũ.</p>
    <div class="row"><button class="primary">Lưu camera</button><button type="button" id="camCancel">Hủy</button></div>
  </form>
  <h3>Tài khoản đăng nhập web</h3><div class="list" id="userList"></div>
  <form id="userForm" style="margin-top:10px">
    <b>Thêm tài khoản / đổi mật khẩu</b>
    <div class="form2">
      <div><label>Tên đăng nhập</label><input name="name" maxlength="32" autocomplete="off" required></div>
      <div><label>Mật khẩu (≥ 8 ký tự)</label><input name="password" type="password" autocomplete="new-password"></div>
      <div><label>Quyền</label><select name="role"><option value="viewer">Chỉ xem (+ xoay camera)</option>
        <option value="admin">Quản trị (toàn quyền)</option></select></div>
    </div>
    <div class="row"><button class="primary">Lưu tài khoản</button></div>
  </form>
</div></section>
<div class="toast" id="toast"></div>

<script>
const $ = s => document.querySelector(s);
const H = {"X-Requested-With": "tapo", "Content-Type": "application/json"};
let cams = [], me = null, cur = null, hd = true, gridKey = "", paused = false;

function toast(msg, bad) {
  const t = $("#toast"); t.textContent = msg; t.className = "toast show" + (bad ? " bad" : "");
  clearTimeout(t._h); t._h = setTimeout(() => t.className = "toast", 3500);
}
async function api(url, method = "GET", body) {
  const r = await fetch(url, {method, headers: H, body: body ? JSON.stringify(body) : undefined});
  if (r.status === 401) { location.href = "/login"; throw new Error("401"); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || ("Lỗi " + r.status));
  return j;
}
function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) k === "class" ? e.className = v : k.startsWith("on") ? e[k] = v : e.setAttribute(k, v);
  for (const k of kids) e.append(k);
  return e;
}

// ---------------------------------------------------------------- grid
function streamUrl(id, w, fps) { return `/stream/${id}.mjpg?w=${w}&fps=${fps}&t=${Date.now()}`; }
function gridW() { return cams.length <= 1 ? 1280 : 640; }

function buildGrid() {
  const g = $("#grid"); g.innerHTML = "";
  if (!cams.length) {
    g.append(el("div", {class: "empty"}, me && me.role === "admin"
      ? "Chưa có camera. Bấm ⚙ Cài đặt để thêm camera." : "Chưa có camera nào."));
    return;
  }
  for (const c of cams) {
    const img = el("img", {alt: c.name, loading: "lazy"});
    const t = el("div", {class: "tile", "data-id": c.id, onclick: () => openViewer(c.id)},
      img, el("div", {class: "overlay-msg"}),
      el("div", {class: "cap"}, el("span", {class: "dot"}), el("span", {class: "nm"}, c.name), el("span", {class: "rec"})));
    g.append(t);
  }
  setGridStreams(!paused && !cur);
}
function setGridStreams(on) {
  document.querySelectorAll(".tile").forEach(t => {
    const img = t.querySelector("img"), id = t.dataset.id;
    if (on && !img.getAttribute("src")) img.src = streamUrl(id, gridW(), 8);
    if (!on && img.getAttribute("src")) { img.removeAttribute("src"); img.src = ""; img.removeAttribute("src"); }
  });
}
function updateTiles() {
  for (const c of cams) {
    const t = document.querySelector(`.tile[data-id="${c.id}"]`); if (!t) continue;
    t.querySelector(".dot").className = "dot" + (c.connected ? " ok" : "");
    t.querySelector(".nm").textContent = c.name + (c.connected ? `  ${Math.round(c.fps)} fps` : "");
    t.querySelector(".rec").textContent = c.recording ? "● REC" : "";
    t.querySelector(".overlay-msg").textContent = c.connected ? "" : c.status;
  }
  if (cur !== null) {
    const c = cams.find(x => x.id === cur);
    if (c) {
      $("#vMsg").textContent = c.connected ? "" : c.status;
      $("#vRec").className = "admin" + (c.recording ? " rec-on" : "");
      $("#vRec").textContent = c.recording ? "⏹ Dừng ghi" : "⏺ Ghi hình";
    }
  }
}
async function poll() {
  try {
    const j = await api("/api/status");
    me = j.user; cams = j.cameras;
    $("#who").textContent = me.name;
    $("#btnSettings").hidden = me.role !== "admin";
    document.querySelectorAll(".admin").forEach(e => e.style.display = me.role === "admin" ? "" : "none");
    const key = cams.map(c => c.id + ":" + c.name).join("|");
    if (key !== gridKey) { gridKey = key; buildGrid(); }
    updateTiles();
  } catch (e) { if (e.message !== "401") console.warn(e); }
}

// -------------------------------------------------------------- viewer
function openViewer(id) {
  const c = cams.find(x => x.id === id); if (!c) return;
  cur = id; setGridStreams(false);
  $("#vName").textContent = c.name;
  $("#vSnap").href = `/snapshot/${id}.jpg`;
  $("#ptzBox").style.display = c.ptz ? "" : "none";
  $("#presetList").innerHTML = "";
  setViewerStream();
  $("#viewer").classList.add("open");
  history.pushState({v: 1}, "");
  updateTiles();
}
function setViewerStream() {
  const img = $("#vImg");
  img.src = cur === null || paused ? "" : streamUrl(cur, hd ? 1280 : 640, hd ? 15 : 8);
  $("#vHd").textContent = hd ? "HD" : "Tiết kiệm";
  $("#vHd").className = hd ? "on" : "";
}
function closeViewer(fromPop) {
  if (cur === null) return;
  cur = null; $("#vImg").removeAttribute("src");
  $("#viewer").classList.remove("open");
  if (document.fullscreenElement) document.exitFullscreen();
  setGridStreams(!paused);
  if (!fromPop) history.back();
}
window.addEventListener("popstate", () => closeViewer(true));
$("#vClose").onclick = () => closeViewer();
$("#vHd").onclick = () => { hd = !hd; setViewerStream(); };
$("#vFull").onclick = () => document.fullscreenElement ? document.exitFullscreen() : $("#viewer").requestFullscreen?.();

async function act(action, body, okMsg) {
  try { const j = await api(`/api/cam/${cur}/${action}`, "POST", body || {}); if (okMsg || j.msg) toast(j.msg || okMsg); poll(); return j; }
  catch (e) { toast(e.message, true); }
}
function move(dx, dy) { const s = +$("#step").value; act("move", {x: dx * s, y: dy * s}); }
document.querySelectorAll(".pad [data-m]").forEach(b => b.onclick = () => { const [x, y] = b.dataset.m.split(",").map(Number); move(x, y); });
$("#step").oninput = e => $("#stepV").textContent = e.target.value;
$("#vCal").onclick = () => confirm("Camera sẽ xoay một vòng để hiệu chỉnh. Tiếp tục?") && act("calibrate", {}, "Đang hiệu chỉnh...");
$("#vRec").onclick = () => act("record");
$("#vPrivOn").onclick = () => act("privacy", {enabled: true}, "Đã bật chế độ riêng tư");
$("#vPrivOff").onclick = () => act("privacy", {enabled: false}, "Đã tắt chế độ riêng tư");
$("#vLedOn").onclick = () => act("led", {enabled: true}, "Đã bật LED");
$("#vLedOff").onclick = () => act("led", {enabled: false}, "Đã tắt LED");
$("#vNight").onchange = e => e.target.value && act("night", {mode: e.target.value}, "Đã đổi chế độ hồng ngoại");
$("#vSavePreset").onclick = () => { const n = prompt("Tên vị trí:"); if (n) act("save_preset", {name: n}, "Đã lưu vị trí"); };
$("#vPresets").onclick = async () => {
  const j = await act("presets"); const box = $("#presetList"); box.innerHTML = "";
  if (!j) return;
  if (!j.presets.length) { box.append(el("p", {class: "muted"}, "Chưa có vị trí nào.")); return; }
  const row = el("div", {class: "row"});
  for (const p of j.presets) row.append(el("button", {onclick: () => act("goto_preset", {id: p.id}, "Đang xoay tới " + p.name)}, p.name));
  box.append(row);
};
document.addEventListener("keydown", e => {
  if (cur === null || /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
  const m = {ArrowUp: [0, 1], ArrowDown: [0, -1], ArrowLeft: [-1, 0], ArrowRight: [1, 0]}[e.key];
  if (m && cams.find(c => c.id === cur)?.ptz) { e.preventDefault(); move(...m); }
  if (e.key === "Escape" && !document.fullscreenElement) closeViewer();
});

// Ẩn tab -> dừng tải hình để tiết kiệm dữ liệu
document.addEventListener("visibilitychange", () => {
  paused = document.hidden;
  if (cur !== null) setViewerStream(); else setGridStreams(!paused);
});

// ------------------------------------------------------------ layout
const lay = $("#layout");
try { lay.value = localStorage.getItem("layout") || "auto"; } catch (e) {}
function applyLayout() { $("#grid").className = "grid" + (lay.value === "auto" ? "" : " cols-" + lay.value); }
lay.onchange = () => { try { localStorage.setItem("layout", lay.value); } catch (e) {} applyLayout(); };
applyLayout();

// ----------------------------------------------------------- settings
let editIdx = null;
$("#btnSettings").onclick = () => { $("#settings").classList.add("open"); loadSettings(); };
$("#sClose").onclick = () => $("#settings").classList.remove("open");
async function loadSettings() {
  const [c, u] = await Promise.all([api("/api/cameras"), api("/api/users")]);
  const cl = $("#camList"); cl.innerHTML = "";
  if (!c.cameras.length) cl.append(el("div", {class: "item muted"}, "Chưa có camera."));
  c.cameras.forEach((cam, i) => cl.append(el("div", {class: "item"},
    el("div", {class: "grow"}, el("b", {}, cam.name), el("span", {class: "muted"}, "  " + (cam.ip || cam.custom_url) + " · " + (cam.stream === "stream2" ? "SD" : "HD"))),
    el("button", {onclick: () => editCam(i, cam)}, "Sửa"),
    el("button", {class: "danger", onclick: async () => {
      if (!confirm("Xóa camera " + cam.name + "?")) return;
      try { await api("/api/cameras/" + i, "DELETE"); toast("Đã xóa camera"); loadSettings(); poll(); } catch (e) { toast(e.message, true); }
    }}, "Xóa"))));
  const ul = $("#userList"); ul.innerHTML = "";
  u.users.forEach(x => ul.append(el("div", {class: "item"},
    el("div", {class: "grow"}, el("b", {}, x.name), el("span", {class: "muted"}, x.role === "admin" ? "  · quản trị" : "  · chỉ xem")),
    el("button", {onclick: () => { const f = $("#userForm"); f.name.value = x.name; f.role.value = x.role; f.password.focus(); }}, "Đổi mật khẩu"),
    el("button", {class: "danger", onclick: async () => {
      if (!confirm("Xóa tài khoản " + x.name + "?")) return;
      try { await api("/api/users/" + encodeURIComponent(x.name), "DELETE"); toast("Đã xóa tài khoản"); loadSettings(); } catch (e) { toast(e.message, true); }
    }}, "Xóa"))));
}
function editCam(i, cam) {
  editIdx = i; const f = $("#camForm");
  for (const k of ["name", "ip", "username", "stream", "port", "custom_url"]) f[k].value = cam[k] ?? "";
  f.password.value = ""; f.cloud_password.value = "";
  f.password.placeholder = cam.has_password ? "•••••• (giữ nguyên)" : "";
  f.cloud_password.placeholder = cam.has_cloud_password ? "•••••• (giữ nguyên)" : "";
  $("#camFormTitle").textContent = "Sửa camera: " + cam.name; $("#pwHint").hidden = false;
  f.scrollIntoView({behavior: "smooth"});
}
function resetCamForm() {
  editIdx = null; const f = $("#camForm"); f.reset(); f.port.value = "554";
  f.password.placeholder = f.cloud_password.placeholder = "";
  $("#camFormTitle").textContent = "Thêm camera"; $("#pwHint").hidden = true;
}
$("#camCancel").onclick = resetCamForm;
$("#camForm").onsubmit = async e => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(e.target));
  try {
    await api(editIdx === null ? "/api/cameras" : "/api/cameras/" + editIdx, "POST", body);
    toast("Đã lưu camera. Đang kết nối..."); resetCamForm(); loadSettings(); gridKey = ""; poll();
  } catch (err) { toast(err.message, true); }
};
$("#userForm").onsubmit = async e => {
  e.preventDefault();
  try { await api("/api/users", "POST", Object.fromEntries(new FormData(e.target))); toast("Đã lưu tài khoản"); e.target.reset(); loadSettings(); }
  catch (err) { toast(err.message, true); }
};

poll(); setInterval(poll, 2500);
</script>
"""
