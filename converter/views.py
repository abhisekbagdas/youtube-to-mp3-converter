from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotAllowed
from django.conf import settings
import yt_dlp
import os
import threading
import json
import logging

logger = logging.getLogger(__name__)


def index(request):
    """Render the main page."""
    return render(request, 'converter/index.html')


def convert_to_mp3(url, download_path=None):
    """Convert YouTube video to MP3."""
    # Use provided path or default
    folder = download_path if download_path else settings.DOWNLOAD_FOLDER
    
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
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        return {"status": "success", "message": f"Conversion complete! File saved to: {folder}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def convert(request):
    """Handle conversion request."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    try:
        body = request.body.decode('utf-8')
        logger.info(f"Request body: {body}")
        data = json.loads(body)
        url = data.get('url')
        download_path = data.get('download_path')
        
        if not url:
            return JsonResponse({"status": "error", "message": "No URL provided"}, status=400)
        
        # Validate path if provided
        if download_path and not os.path.isabs(download_path):
            return JsonResponse({"status": "error", "message": "Please provide an absolute path"}, status=400)
        
        # Run conversion in background thread
        thread = threading.Thread(target=convert_to_mp3, args=(url, download_path))
        thread.start()
        
        return JsonResponse({"status": "processing", "message": "Conversion started"})
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({"status": "error", "message": f"Invalid JSON: {str(e)}"}, status=400)
    except Exception as e:
        logger.error(f"Server error: {e}")
        return JsonResponse({"status": "error", "message": f"Server error: {str(e)}"}, status=500)

