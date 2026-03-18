from flask import Flask, render_template, request, jsonify
import requests
import re
import os

app = Flask(__name__)

# RapidAPI credentials (optional)
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.environ.get("RAPIDAPI_HOST")
RAPIDAPI_BASE_URL = os.environ.get("RAPIDAPI_BASE_URL") or (f"https://{RAPIDAPI_HOST}" if RAPIDAPI_HOST else "")

def call_rapidapi(url, dtype):
    if not RAPIDAPI_KEY or not RAPIDAPI_HOST:
        return {"success": False, "error": "RapidAPI credentials not configured"}
    api_base = RAPIDAPI_BASE_URL or f"https://{RAPIDAPI_HOST}"
    endpoints = [
        f"{api_base}/download",
        f"{api_base}/v1/download",
        f"{api_base}/video",
    ]
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    payload = {"url": url}
    payload["format"] = "mp3" if dtype == "audio" else "mp4"
    # Try POST
    for ep in endpoints:
        try:
            resp = requests.post(ep, json=payload, headers=headers, timeout=15)
            if resp.ok:
                data = resp.json()
                for key in ("download_url", "url", "data"):
                    if isinstance(data, dict) and data.get(key):
                        return {"success": True, "download_url": data.get(key)}
        except Exception:
            pass
    # Try GET as fallback
    for ep in endpoints:
        try:
            resp = requests.get(ep, headers=headers, params=payload, timeout=15)
            if resp.ok:
                data = resp.json()
                for key in ("download_url", "url"):
                    if isinstance(data, dict) and data.get(key):
                        return {"success": True, "download_url": data.get(key)}
        except Exception:
            pass
    return {"success": False, "error": "RapidAPI request failed"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    download_type = data.get('type')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    # Try RapidAPI first (if credentials provided)
    rapid = call_rapidapi(url, download_type)
    if rapid.get('success'):
        return jsonify({'success': True, 'download_url': rapid['download_url']})

    # Fall back to platform-specific methods
    if 'instagram.com' in url:
        return download_instagram(url)
    elif 'youtube.com' in url or 'youtu.be' in url:
        return download_youtube(url)
    else:
        return jsonify({'error': 'Unsupported platform'}), 400

def download_youtube(url):
    # Try SnapTube API alternative
    try:
        video_id = extract_youtube_id(url)
        if video_id:
            # Return direct download page
            return jsonify({
                'success': True,
                'download_url': f"https://loader.to/en/youtube-video-downloader.php?v={video_id}",
                'type': 'redirect'
            })
    except:
        pass
    
    return jsonify({'error': 'YouTube: Service temporarily unavailable'}), 500

def download_instagram(url):
    # Try various free APIs
    api_list = [
        ("https://saveinsta.io/api/ajaxSearch", {"q": url}),
        ("https://api.pulltofetch.com/instagram", {"url": url}),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Accept': 'application/json'
    }
    
    for api_url, payload in api_list:
        try:
            response = requests.post(api_url, data=payload, headers=headers, timeout=20)
            if response.status_code == 200:
                data = response.json()
                # Look for media URL in response
                if 'media' in data:
                    return jsonify({'success': True, 'download_url': data['media']})
                if 'url' in data:
                    return jsonify({'success': True, 'download_url': data['url']})
                if 'result' in data and isinstance(data['result'], list) and len(data['result']) > 0:
                    return jsonify({'success': True, 'download_url': data['result'][0].get('url', '')})
        except Exception as e:
            continue
    
    # Fallback: return download page URL
    return jsonify({
        'success': True,
        'download_url': 'https://sssinstagram.com',
        'type': 'fallback',
        'message': 'Please copy URL and open on sssinstagram.com'
    })

def extract_youtube_id(url):
    patterns = [
        r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
