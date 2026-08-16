import os
import tempfile
import imageio_ffmpeg
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="夜載 YeZai API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str

def is_youtube_url(url: str) -> bool:
    """檢查是否為 YouTube 網址"""
    youtube_domains = ["youtube.com", "youtu.be"]
    return any(domain in url.lower() for domain in youtube_domains)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "夜載 YeZai 後端服務正常運作中"}

@app.post("/api/analyze")
def analyze_video(req: AnalyzeRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="請提供有效的影片網址")

    cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
    has_cookies = os.path.exists(cookie_path)
    url_is_youtube = is_youtube_url(req.url)

    if url_is_youtube and not has_cookies:
        raise HTTPException(
            status_code=400, 
            detail="YouTube 下載目前需要設定 cookies.txt。其他平台（Bilibili、TikTok 等）可直接下載！"
        )

    temp_dir = tempfile.mkdtemp()
    out_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

    # 取得 imageio-ffmpeg 提供的 FFmpeg 執行檔路徑
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': out_template,
        'ffmpeg_location': ffmpeg_exe,
        'merge_output_format': 'mp4',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    }

    if has_cookies:
        ydl_opts['cookiefile'] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([req.url])

            files = os.listdir(temp_dir)
            if not files:
                raise HTTPException(status_code=500, detail="影片下載失敗，無法找到輸出檔案")

            actual_filepath = os.path.join(temp_dir, files[0])
            download_name = os.path.basename(actual_filepath)
            
            ext = os.path.splitext(download_name)[1].lower()
            media_type = 'video/mp4' if ext == '.mp4' else 'video/webm'

            return FileResponse(
                path=actual_filepath,
                filename=download_name,
                media_type=media_type
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析或下載失敗: {str(e)}")
