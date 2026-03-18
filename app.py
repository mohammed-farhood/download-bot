from flask import Flask, render_template, request, jsonify
import requests
import re

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
