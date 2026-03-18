from flask import Flask, render_template, request, jsonify, redirect
import requests
import os

app = Flask(__name__)

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
    
    try:
        if 'instagram.com' in url:
            return download_instagram(url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            return download_youtube(url)
        else:
            return jsonify({'error': 'Unsupported platform'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def download_youtube(url):
    # Try direct redirect to y2mate
    try:
        # Extract video ID
        video_id = extract_youtube_id(url)
        if video_id:
            # Direct download link via y2mate
            return jsonify({
                'success': True,
                'download_url': f"https://www.y2mate.com/youtube-mp3/{video_id}",
                'message': 'Click to download on y2mate'
            })
    except:
        pass
    
    # Try Invidious
    try:
        instances = ["https://invidious.fdn.fr", "https://invidious.kavin.rocks"]
        for instance in instances:
            video_id = extract_youtube_id(url)
            if video_id:
                return jsonify({
                    'success': True,
                    'download_url': f"{instance}/watch?v={video_id}",
                    'message': 'Click to download on Invidious'
                })
    except:
        pass
    
    return jsonify({'error': 'YouTube unavailable. Try downloading directly from browser.'}), 500

def download_instagram(url):
    # Try multiple Instagram download APIs
    apis = [
        ("https://api.bijinder.com/instagram", {"url": url}),
        ("https://backend.savefrom.net/savefrom.php", {"url": url}),
    ]
    
    for api_url, payload in apis:
        try:
            response = requests.post(api_url, json=payload, timeout=30, 
                                   headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                data = response.json()
                media_url = data.get('url') or data.get('video_url') or data.get('result')
                if media_url:
                    return jsonify({
                        'success': True,
                        'download_url': media_url
                    })
        except:
            continue
    
    return jsonify({'error': 'Instagram unavailable. Try downloading directly from browser.'}), 500

def extract_youtube_id(url):
    import re
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
