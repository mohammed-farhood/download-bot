from flask import Flask, render_template, request, jsonify, redirect
import requests
import os

app = Flask(__name__)

INVIDIOUS_INSTANCES = [
    "https://invidious.fdn.fr",
    "https://invidious.jingl.xyz", 
    "https://invidious.kavin.rocks",
    "https://youtube.privacydev.net",
]

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
            return download_youtube(url, download_type)
        else:
            return jsonify({'error': 'Unsupported platform'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def download_youtube(url, download_type):
    video_id = extract_youtube_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    # Try each Invidious instance
    for instance in INVIDIOUS_INSTANCES:
        try:
            # Get video info
            api_url = f"{instance}/api/v1/videos/{video_id}"
            response = requests.get(api_url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if download_type == 'audio':
                    # Find audio-only format
                    for fmt in data.get('adaptiveFormats', []):
                        if 'audio' in fmt.get('type', ''):
                            return jsonify({
                                'success': True,
                                'download_url': f"{instance}/api/v1/videos/{video_id}/signature?format=140",
                            })
                else:
                    # Return video page for download
                    return jsonify({
                        'success': True,
                        'download_url': f"{instance}/watch?v={video_id}",
                    })
        except Exception as e:
            continue
    
    return jsonify({'error': 'All servers failed. Try Instagram instead.'}), 500

def download_instagram(url):
    # Use a simple approach - return redirect
    try:
        api_url = "https://api.bijinder.com/instagram"
        response = requests.post(api_url, json={'url': url}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'download_url': data.get('url', data.get('video_url', ''))
            })
    except:
        pass
    
    return jsonify({'error': 'Instagram download unavailable'}), 500

def extract_youtube_id(url):
    # Extract video ID from various YouTube URL formats
    import re
    patterns = [
        r'(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
