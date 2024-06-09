from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pytube import YouTube
import os
import tempfile

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = 'tmp'

def remove_file(file_path: str):
    os.remove(file_path)

def sanitize_filename(filename: str):
    return filename.replace('/', '-')

@app.get("/download")
async def download_video(url: str, background_tasks: BackgroundTasks):
    try:
        yt = YouTube(url)
        title = yt.title
        author = yt.author

        video = yt.streams.filter(only_audio=True).first()
        
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)

        with tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix='.mp3') as tmpfile:
            tmpfile_path = tmpfile.name  

        downloaded_file = video.download(output_path=TEMP_DIR, filename=os.path.basename(tmpfile_path))

        sanitized_title = sanitize_filename(title)
        sanitized_author = sanitize_filename(author)

        new_file_path = os.path.join(TEMP_DIR, f"{sanitized_title} - {sanitized_author}.mp3")

        os.rename(downloaded_file, new_file_path)

        background_tasks.add_task(remove_file, new_file_path)

        return FileResponse(new_file_path, filename=f"{sanitized_title} - {sanitized_author}.mp3")
        
    except KeyError:
        raise HTTPException(status_code=400, detail="Error: Video is not available or cannot be downloaded")
    except ValueError:
        raise HTTPException(status_code=400, detail="Error: Invalid URL")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error downloading video: " + str(e))
