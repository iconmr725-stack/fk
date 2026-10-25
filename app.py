import json
import os
from urllib.parse import urlparse

import requests
import yt_dlp
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_CONFIG = {"color": "#ff2d55", "announcement": ""}

# Only these sites are accepted (keeps the server from being misused).
ALLOWED = (
    "tiktok.com", "instagram.com", "facebook.com", "fb.watch", "fb.com",
    "twitter.com", "x.com", "snapchat.com", "threads.net", "vimeo.com",
    "reddit.com", "pinterest.com", "dailymotion.com",
)


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception:
        return dict(DEFAULT_CONFIG)


def check_url(url):
    host = (urlparse(url or "").hostname or "").lower()
    if not any(host == d or host.endswith("." + d) for d in ALLOWED):
        raise ValueError("This site is not supported. Try TikTok, Instagram, Facebook, X, Snapchat, Vimeo, Reddit or Pinterest.")


def extract(url):
    check_url(url)
    opts = {"format": "best[ext=mp4]/best", "quiet": True, "noplaylist": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("entries"):
        info = info["entries"][0]
    if not info.get("url") or str(info.get("protocol", "")).startswith("m3u8"):
        raise ValueError("This video can't be downloaded directly.")
    return info


@app.route("/api/info")
def api_info():
    try:
        i = extract(request.args.get("url", ""))
        return jsonify(title=i.get("title", ""), author=i.get("uploader", ""), thumbnail=i.get("thumbnail", ""))
    except Exception as e:
        return jsonify(error=str(e)[:200]), 400


@app.route("/api/download")
def api_download():
    try:
        i = extract(request.args.get("url", ""))
        r = requests.get(i["url"], headers=i.get("http_headers") or {}, stream=True, timeout=30)
        r.raise_for_status()
        headers = {"Content-Disposition": 'attachment; filename="FK_video.mp4"'}
        if r.headers.get("Content-Length"):
            headers["Content-Length"] = r.headers["Content-Length"]
        return Response(r.iter_content(65536), content_type="video/mp4", headers=headers)
    except Exception as e:
        return str(e)[:200], 400


@app.route("/api/config")
def api_config():
    return jsonify(load_config())


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FK Multimedia Video Downloader | Download TikTok, Instagram, Facebook &amp; X Videos</title>
<meta name="description" content="FK Multimedia Video Downloader by Florence K. Paste a video link from TikTok, Instagram, Facebook, X, Snapchat and more, and download the video in the best quality available.">
<meta name="keywords" content="FK Multimedia, FK Video, Florence K, video downloader, TikTok downloader, Instagram video downloader, Facebook video downloader, X video downloader, download without watermark">
<style>
  :root { --bg:#0f0f14; --card:#1a1b24; --text:#fff; --muted:#9aa0b4; --accent:#ff2d55; }
  @media (prefers-color-scheme: light) { :root { --bg:#f4f5f9; --card:#fff; --text:#15161c; --muted:#5b6075; } }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); min-height:100vh; display:flex; flex-direction:column; align-items:center; padding:24px 16px; }
  h1 { margin:16px 0 4px; font-size:1.5rem; text-align:center; }
  .sub { color:var(--muted); margin:0 0 20px; text-align:center; }
  .card { background:var(--card); border-radius:16px; padding:20px; width:100%; max-width:520px; }
  input { width:100%; padding:14px; border-radius:10px; border:1px solid #555; background:transparent; color:var(--text); font-size:1rem; }
  button { width:100%; margin-top:12px; padding:14px; border:0; border-radius:10px; background:var(--accent); color:#fff; font-size:1rem; font-weight:600; }
  button:disabled { opacity:.6; }
  #result { margin-top:16px; display:none; }
  #result img { width:100%; border-radius:10px; }
  #msg { margin-top:12px; color:var(--muted); }
  #note { background:#ffd54a; color:#222; padding:10px 14px; border-radius:10px; margin-bottom:16px; max-width:520px; width:100%; display:none; }
  footer { margin-top:auto; padding-top:32px; color:var(--muted); font-size:.85rem; text-align:center; }
</style>
</head>
<body>
  <h1>FK Multimedia Video Downloader</h1>
  <p class="sub">Florence K · TikTok, Instagram, Facebook, X, Snapchat and more</p>
  <div id="note"></div>
  <div class="card">
    <input id="url" type="url" placeholder="Paste the video link here">
    <button id="go">Load video</button>
    <div id="msg"></div>
    <div id="result">
      <img id="thumb" alt="">
      <p id="title"></p>
      <button id="dl">Download video</button>
    </div>
  </div>
  <footer>Created by Florence K · Website &amp; App</footer>
<script>
const $ = (id) => document.getElementById(id);
let current = "";
fetch("/api/config").then(r => r.json()).then(c => {
  document.documentElement.style.setProperty("--accent", c.color);
  if (c.announcement) { $("note").textContent = c.announcement; $("note").style.display = "block"; }
}).catch(() => {});
$("go").onclick = async () => {
  const url = $("url").value.trim();
  $("result").style.display = "none";
  if (!url) { $("msg").textContent = "Please paste a video link."; return; }
  $("msg").textContent = "Loading video... (the first load can take up to a minute)";
  $("go").disabled = true;
  try {
    const r = await fetch("/api/info?url=" + encodeURIComponent(url));
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || "Video not found");
    current = url;
    $("thumb").src = j.thumbnail || "";
    $("title").textContent = (j.author ? j.author + ": " : "") + j.title;
    $("result").style.display = "block";
    $("msg").textContent = "";
  } catch (e) { $("msg").textContent = "Failed: " + e.message; }
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
