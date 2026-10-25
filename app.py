import json
import os
from urllib.parse import urlparse

import requests
import yt_dlp
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_CONFIG = {"color": "#ff2d55", "announcement": ""}

ALLOWED = (
    "tiktok.com", "instagram.com", "facebook.com", "fb.watch", "fb.com",
    "twitter.com", "x.com", "snapchat.com", "threads.net", "vimeo.com",
    "reddit.com", "pinterest.com", "dailymotion.com",
)
FRIENDLY = "Couldn't load this video. Make sure the link is public and copied in full, then try again."


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception:
        return dict(DEFAULT_CONFIG)


def host_of(url):
    return (urlparse(url or "").hostname or "").lower()


def check_url(url):
    host = host_of(url)
    if not any(host == d or host.endswith("." + d) for d in ALLOWED):
        raise ValueError("This site is not supported. Try TikTok, Instagram, Facebook, X, Snapchat, Vimeo, Reddit or Pinterest.")


def fix(u):
    return "https://www.tikwm.com" + u if u and u.startswith("/") else u


def tiktok_api(url):
    r = requests.get("https://www.tikwm.com/api/", params={"url": url, "hd": 1},
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
    j = r.json()
    if j.get("code") != 0:
        raise ValueError(j.get("msg") or "Video not found")
    d = j["data"]
    video = fix(d.get("hdplay") or d.get("play"))
    if not video:
        raise ValueError("No video found")
    return {"url": video, "title": d.get("title", ""), "uploader": (d.get("author") or {}).get("nickname", ""),
            "thumbnail": fix(d.get("cover")), "http_headers": {}}


def ytdlp(url):
    opts = {"format": "best[ext=mp4]/best", "quiet": True, "noplaylist": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("entries"):
        info = info["entries"][0]
    if not info.get("url") or str(info.get("protocol", "")).startswith("m3u8"):
        raise ValueError("This video can't be downloaded directly.")
    return info


def extract(url):
    check_url(url)
    host = host_of(url)
    if host == "tiktok.com" or host.endswith(".tiktok.com"):
        try:
            return tiktok_api(url)
        except Exception as e:
            print("tiktok api failed:", e)
    return ytdlp(url)


def error_text(e):
    print("error:", e)
    return str(e) if isinstance(e, ValueError) else FRIENDLY


@app.route("/api/info")
def api_info():
    try:
        i = extract(request.args.get("url", ""))
        return jsonify(title=i.get("title", ""), author=i.get("uploader", ""), thumbnail=i.get("thumbnail", ""))
    except Exception as e:
        return jsonify(error=error_text(e)), 400


@app.route("/api/download")
def api_download():
    try:
        i = extract(request.args.get("url", ""))
        r = requests.get(i["url"], headers=i.get("http_headers") or {}, stream=True, timeout=30)
        r.raise_for_status()
        headers = {"Content-Disposition": 'attachment; filename="FK_Multimedia_video.mp4"'}
        if r.headers.get("Content-Length"):
            headers["Content-Length"] = r.headers["Content-Length"]
        return Response(r.iter_content(65536), content_type="video/mp4", headers=headers)
    except Exception as e:
        return error_text(e), 400


@app.route("/api/config")
def api_config():
    return jsonify(load_config())


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nAllow: /\nSitemap: " + request.host_url + "sitemap.xml\n", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    xml = ('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           "<url><loc>" + request.host_url + "</loc></url></urlset>")
    return Response(xml, mimetype="application/xml")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multimedia Video Downloader | FK Multimedia - Download Social Media Videos</title>
<meta name="description" content="FK Multimedia is a free multimedia video downloader by Florence K. Paste a link from TikTok, Instagram, Facebook, X, Snapchat and more, and download the video in the best quality available.">
<meta name="keywords" content="multimedia video downloader, FK Multimedia, social media video downloader, TikTok video downloader, Instagram video downloader, Facebook video downloader, X video downloader, Snapchat video downloader, Florence K">
<meta property="og:title" content="Multimedia Video Downloader | FK Multimedia">
<meta property="og:description" content="Paste a social media video link and download the video in the best quality available.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⬇️</text></svg>">
<style>
  :root { --accent:#ff2d55; --bg1:#0b0b12; --bg2:#1b1030; --card:rgba(255,255,255,.07); --line:rgba(255,255,255,.14); --text:#fff; --muted:#aab0c6; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,-apple-system,"Segoe UI",sans-serif; color:var(--text); min-height:100vh;
    background:radial-gradient(900px 500px at 10% -10%, #3b1d6e55, transparent), radial-gradient(800px 500px at 100% 0%, #ff2d5533, transparent), linear-gradient(160deg,var(--bg1),var(--bg2)); background-attachment:fixed; }
  .wrap { max-width:760px; margin:0 auto; padding:32px 18px 24px; }
  .brand { text-align:center; font-weight:700; letter-spacing:.5px; color:var(--muted); font-size:.9rem; }
  .brand b { color:var(--accent); }
  h1 { font-size:clamp(1.9rem,6vw,3rem); line-height:1.1; text-align:center; margin:14px 0 10px; }
  h1 span { background:linear-gradient(90deg,var(--accent),#ffb347); -webkit-background-clip:text; background-clip:text; color:transparent; }
  .lead { text-align:center; color:var(--muted); margin:0 auto 26px; max-width:520px; line-height:1.5; }
  #note { background:linear-gradient(90deg,#ffd54a,#ffb347); color:#222; padding:11px 15px; border-radius:12px; margin-bottom:18px; display:none; font-weight:600; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:22px; padding:18px; backdrop-filter:blur(14px); box-shadow:0 20px 60px #0008; }
  .row { display:flex; gap:10px; flex-wrap:wrap; }
  input { flex:1 1 220px; padding:16px; border-radius:14px; border:1px solid var(--line); background:#0006; color:#fff; font-size:1rem; outline:none; }
  input:focus { border-color:var(--accent); }
  button { padding:16px 22px; border:0; border-radius:14px; background:var(--accent); color:#fff; font-size:1rem; font-weight:700; cursor:pointer; flex:0 0 auto; }
  button:disabled { opacity:.6; }
  button.full { width:100%; margin-top:14px; }
  #msg { margin-top:14px; color:var(--muted); min-height:1.2em; display:flex; align-items:center; gap:10px; }
  .spin { width:18px; height:18px; border:3px solid #fff4; border-top-color:var(--accent); border-radius:50%; animation:s 1s linear infinite; display:none; }
  @keyframes s { to { transform:rotate(360deg); } }
  #result { display:none; margin-top:16px; border-top:1px solid var(--line); padding-top:16px; }
  #result img { width:100%; max-height:340px; object-fit:cover; border-radius:14px; }
  #title { margin:12px 0 0; line-height:1.4; }
  .chips { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:22px 0 6px; }
  .chip { padding:7px 14px; border:1px solid var(--line); border-radius:99px; font-size:.85rem; color:var(--muted); background:var(--card); }
  h2 { text-align:center; margin:38px 0 14px; font-size:1.3rem; }
  .steps { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; }
  .step { background:var(--card); border:1px solid var(--line); border-radius:16px; padding:16px; }
  .step i { display:inline-flex; width:30px; height:30px; border-radius:50%; background:var(--accent); align-items:center; justify-content:center; font-style:normal; font-weight:700; margin-bottom:8px; }
  .step p { margin:0; color:var(--muted); line-height:1.45; }
  details { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:14px 16px; margin-bottom:10px; }
  summary { cursor:pointer; font-weight:600; }
  details p { color:var(--muted); line-height:1.5; margin:10px 0 0; }
  footer { text-align:center; color:var(--muted); font-size:.85rem; margin-top:40px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand"><b>FK</b> Multimedia · Florence K</div>
  <h1>Multimedia <span>Video Downloader</span></h1>
  <p class="lead">Paste a video link from TikTok, Instagram, Facebook, X, Snapchat and more. Get the video in the best quality available.</p>
  <div id="note"></div>
  <div class="card">
    <div class="row">
      <input id="url" type="url" placeholder="Paste the video link here" autocomplete="off">
      <button id="go">Load video</button>
    </div>
    <div id="msg"><span class="spin" id="spin"></span><span id="msgtext"></span></div>
    <div id="result">
      <img id="thumb" alt="Video preview">
      <p id="title"></p>
      <button class="full" id="dl">Download video</button>
    </div>
  </div>
  <div class="chips"><span class="chip">TikTok</span><span class="chip">Instagram</span><span class="chip">Facebook</span><span class="chip">X (Twitter)</span><span class="chip">Snapchat</span><span class="chip">Vimeo</span><span class="chip">Reddit</span><span class="chip">Pinterest</span></div>
  <h2>How it works</h2>
  <div class="steps">
    <div class="step"><i>1</i><p>Open the app or site and tap Share on the video, then Copy link.</p></div>
    <div class="step"><i>2</i><p>Paste the link above and tap Load video.</p></div>
    <div class="step"><i>3</i><p>Tap Download video. It saves to your phone.</p></div>
  </div>
  <h2>Questions</h2>
  <details><summary>Is FK Multimedia free?</summary><p>Yes. Paste a link, load the video and download it. No account needed.</p></details>
  <details><summary>Which sites can I download from?</summary><p>TikTok, Instagram, Facebook, X, Snapchat, Vimeo, Reddit and Pinterest.</p></details>
  <details><summary>Where does the video go?</summary><p>On Android it goes to your Downloads or gallery. On iPhone, open it from Files and choose Save Video.</p></details>
  <details><summary>Is there an Android app?</summary><p>Yes, FK Multimedia has an Android app with the same features.</p></details>
  <footer>Created by Florence K · Website &amp; App<br>Only download videos you own or have permission to save.</footer>
</div>
<script>
const $ = (id) => document.getElementById(id);
let current = "";
const say = (t, busy) => { $("msgtext").textContent = t; $("spin").style.display = busy ? "inline-block" : "none"; };
fetch("/api/config").then(r => r.json()).then(c => {
  document.documentElement.style.setProperty("--accent", c.color);
  if (c.announcement) { $("note").textContent = c.announcement; $("note").style.display = "block"; }
}).catch(() => {});
$("url").addEventListener("keydown", e => { if (e.key === "Enter") $("go").click(); });
$("go").onclick = async () => {
  const url = $("url").value.trim();
  $("result").style.display = "none";
  if (!url) { say("Please paste a video link.", false); return; }
  say("Loading video... the first load can take up to a minute.", true);
  $("go").disabled = true;
  try {
    const r = await fetch("/api/info?url=" + encodeURIComponent(url));
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "Video not found");
    current = url;
    $("thumb").src = j.thumbnail || "";
    $("thumb").style.display = j.thumbnail ? "block" : "none";
    $("title").textContent = (j.author ? j.author + ": " : "") + j.title;
    $("result").style.display = "block";
    say("", false);
  } catch (e) { say("Failed: " + e.message, false); }
  $("go").disabled = false;
};
$("dl").onclick = () => { window.location.href = "/api/download?url=" + encodeURIComponent(current); };
</script>
</body>
</html>"""


@app.route("/")
def home():
    return PAGE


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
