from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YeZai Night Downloader API")

# 允許前端跨域請求 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    url: str

@app.post("/api/analyze")
def analyze_video(req: AnalyzeRequest):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none': # 過濾有效影片軌
                    formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext', 'mp4'),
                        'resolution': f.get('format_note') or f"{f.get('height', 'SD')}p",
                        'filesize_mb': round((f.get('filesize') or f.get('filesize_approx') or 0) / (1024 * 1024), 1),
                    })
            return {
                "status": "success",
                "title": info.get('title', '未知標題'),
                "thumbnail": info.get('thumbnail'),
                "duration_sec": info.get('duration', 0),
                "uploader": info.get('uploader', '網絡影音'),
                "formats": formats
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))