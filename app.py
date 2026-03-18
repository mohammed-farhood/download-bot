from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import uuid
import ffmpeg

app = Flask(__name__)

DOWNLOAD_FOLDER = '/tmp/downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def get_video_info(url):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    download_type = data.get('type')  # 'video' or 'audio'
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    filename = f"{uuid.uuid4()}"
    
    if download_type == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/{filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'extractor_retries': 3,
            'fragment_retries': 3,
            'nocheckcertificate': True,
        }
    else:
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/{filename}.%(ext)s',
            'extractor_retries': 3,
            'fragment_retries': 3,
            'nocheckcertificate': True,
        }
    
    # Common options to bypass YouTube blocks
    ydl_opts.update({
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'no_warnings': True,
        'prefer_free_formats': True,
        'geo_bypass': True,
        'cookiefile': None,
    })
    
    # Use alternative YouTube extractor
    if 'youtube' in url.lower():
        ydl_opts['extractor'] = ['youtube:playlist', 'youtube:vide']
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file
        for f in os.listdir(DOWNLOAD_FOLDER):
            if f.startswith(filename):
                filepath = os.path.join(DOWNLOAD_FOLDER, f)
                return jsonify({'file': f, 'path': filepath})
        
        return jsonify({'error': 'Download failed'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-file/<filename>')
def get_file(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
