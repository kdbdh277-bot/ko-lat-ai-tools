
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import tempfile
import os
import glob
import re

app = Flask(__name__)
CORS(app)

ALLOWED_DOMAINS = [
    "youtube.com", "youtu.be",
    "tiktok.com",
    "facebook.com", "fb.watch"
]

def valid_url(url):
    return any(domain in url.lower() for domain in ALLOWED_DOMAINS)

def clean_vtt(text):
    text = re.sub(r'<[^>]+>', '', text)
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line or "-->" in line:
            continue

        if line.startswith(("WEBVTT", "NOTE", "Kind:", "Language:")):
            continue

        line = re.sub(r'\d+$', '', line)

        if not lines or lines[-1] != line:
            lines.append(line)

    return "\n".join(lines)

@app.route("/")
def home():
    return jsonify({"status": "Ko Lat AI Backend is running"})

@app.route("/api/extract", methods=["POST"])
def extract():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not valid_url(url):
        return jsonify({"error": "Video Link မမှန်ပါ။"}), 400

    try:
        with tempfile.TemporaryDirectory() as temp:
            options = {
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitlesformat": "vtt/best",
                "subtitleslangs": ["my", "en"],
                "outtmpl": os.path.join(temp, "video"),
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "ios", "web_safari"]
                    }
                }
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

            files = glob.glob(os.path.join(temp, "*.vtt"))

            if not files:
                return jsonify({
                    "error": "ဒီဗီဒီယိုမှာ ထုတ်ယူနိုင်တဲ့ Subtitle မတွေ့ပါ။"
                }), 404

            with open(files[0], "r", encoding="utf-8") as f:
                transcript = clean_vtt(f.read())

            if not transcript:
                return jsonify({"error": "စာသားမရရှိပါ။"}), 404

            return jsonify({"transcript": transcript})

    except Exception as e:
        app.logger.exception("Video extraction failed")
        return jsonify({
            "error": "YouTube က Server ဝင်ရောက်မှုကို ကန့်သတ်ထားနိုင်ပါတယ်။"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
