from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import threading

app = Flask(__name__)
DEFAULT_DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DEFAULT_DOWNLOAD_FOLDER):
    os.makedirs(DEFAULT_DOWNLOAD_FOLDER)

def convert_to_mp3(url, download_path=None):
    # Use provided path or default
    folder = download_path if download_path else DEFAULT_DOWNLOAD_FOLDER
    
    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except Exception as e:
            return {"status": "error", "message": f"Cannot create folder: {str(e)}"}
    
    # Check if path is writable
    if not os.access(folder, os.W_OK):
        return {"status": "error", "message": "No write permission for the specified path"}
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(folder, '%(title)s'),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        return {"status": "success", "message": f"Conversion complete! File saved to: {folder}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.json
        url = data.get('url') if data else None
        download_path = data.get('download_path') if data else None
        
        if not url:
            return jsonify({"status": "error", "message": "No URL provided"}), 400
        
        # Validate path if provided
        if download_path and not os.path.isabs(download_path):
            return jsonify({"status": "error", "message": "Please provide an absolute path"}), 400
        
        # Run conversion in background thread
        thread = threading.Thread(target=convert_to_mp3, args=(url, download_path))
        thread.start()
        
        return jsonify({"status": "processing", "message": "Conversion started"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)