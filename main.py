from fastapi import FastAPI
from pydantic import BaseModel
import ffmpeg
import os
import uuid

app = FastAPI()

# Folder to store converted files (will be publicly served)
os.makedirs("converted", exist_ok=True)

class PCMData(BaseModel):
    pcm_base64: str  # base64 PCM string

@app.post("/convert")
async def convert_pcm_to_mp3(data: PCMData):
    import base64

    # decode base64 string to bytes
    pcm_bytes = base64.b64decode(data.pcm_base64)

    # generate unique filenames
    mp3_filename = f"{uuid.uuid4()}.mp3"
    pcm_path = f"temp_{uuid.uuid4()}.pcm"
    mp3_path = f"converted/{mp3_filename}"

    # save PCM bytes to temp file
    with open(pcm_path, "wb") as f:
        f.write(pcm_bytes)

    # convert PCM -> MP3
    ffmpeg.input(pcm_path, format='s16le', ar='24000', ac=1).output(mp3_path).run(overwrite_output=True)

    # remove temp PCM
    os.remove(pcm_path)

    # return public URL to MP3
    base_url = "https://your-render-url"  # replace with your Render URL
    mp3_url = f"{base_url}/converted/{mp3_filename}"
    return {"mp3_url": mp3_url}

# Serve the converted folder as static files
from fastapi.staticfiles import StaticFiles
app.mount("/converted", StaticFiles(directory="converted"), name="converted")
