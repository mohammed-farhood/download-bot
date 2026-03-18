from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

DOWNLOAD_FOLDER = '/tmp/downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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
    
    filename = f"{uuid.uuid4()}"
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_FOLDER}/{filename}.%(ext)s',
        'nocheckcertificate': True,
        'no_warnings': True,
        'quiet': True,
        'nocolor': True,
        'check_formats': False,
        'allow_multiple_video_streams': True,
        'allow_multiple_audio_streams': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        },
    }
    
    if download_type == 'audio':
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best'
    else:
        ydl_opts['format'] = 'best[ext=webm]/bestvideo[ext=webm]+bestaudio[ext=webm]/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        for f in os.listdir(DOWNLOAD_FOLDER):
            if f.startswith(filename):
                return jsonify({
                    'success': True,
                    'file': f,
                    'path': f'/get-file/{f}'
                })
        
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
