import os
import uuid
import time
import random
import yt_dlp
from flask import Flask, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def cleanup_old_files():
    now = time.time()
    for f in os.listdir(DOWNLOAD_FOLDER):
        path = os.path.join(DOWNLOAD_FOLDER, f)
        if os.stat(path).st_mtime < now - 600:
            try: os.remove(path)
            except: pass

@app.route('/download', methods=['GET'])
def smart_download():
    cleanup_old_files()
    video_url = request.args.get('url')
    format_type = request.args.get('format', 'mp4')

    if not video_url:
        return "URL missing", 400

    unique_name = f"special_{str(uuid.uuid4())[:8]}"
    
    # ইউজার এজেন্ট লিস্ট
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    ]

    try:
        # ১. প্রথমেই ভিডিওর ইনফরমেশন চেক করা (ধারণক্ষমতা বুঝতে)
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(video_url, download=False)
            duration = info.get('duration', 0)
            print(f"Video duration: {duration} seconds")

        # ২. স্মার্ট কোয়ালিটি রাউটিং (আপনার শর্ত অনুযায়ী)
        if format_type == 'mp3':
            # অডিওর ক্ষেত্রে কোনো আপোষ নেই - সবসময় বেস্ট
            format_logic = 'bestaudio/best'
            postprocessor = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            postprocessor = []
            if duration < 300: # ৫ মিনিটের নিচে
                format_logic = 'bestvideo+bestaudio/best'
                print("Setting: 4K/1080p (Best)")
            elif duration < 1200: # ৫-২০ মিনিট
                format_logic = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
                print("Setting: 720p (HD)")
            else: # ২০ মিনিটের বেশি
                format_logic = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
                print("Setting: 480p (SD)")

        # ৩. ফাইনাল ডাউনলোড সেটিংস
        ydl_opts = {
            'format': format_logic,
            'outtmpl': f'{DOWNLOAD_FOLDER}/{unique_name}.%(ext)s',
            'user_agent': random.choice(user_agents),
            'geo_bypass': True,
            'nocheckcertificate': True,
            'merge_output_format': 'mp4' if format_type == 'mp4' else None,
            'postprocessors': postprocessor,
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            final_info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(final_info)
            
            # MP3 ফিক্স
            if format_type == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
