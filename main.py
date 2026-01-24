from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import ffmpeg
import os
import uuid
import base64

# Initialize app
app = FastAPI()

# Folder to store converted files (publicly served)
os.makedirs("converted", exist_ok=True)

# Serve static files from "converted"
app.mount("/converted", StaticFiles(directory="converted"), name="converted")

# Pydantic model for incoming JSON
class PCMData(BaseModel):
    pcm_base64: str  # base64-encoded PCM string

# Warmup endpoint
@app.get("/warmup")
def warmup():
    return {"status": "ok", "message": "Server is warm"}

# PCM → MP3 conversion endpoint
@app.post("/convert")
async def convert_pcm_to_mp3(data: PCMData):
    # Decode base64 PCM string
    try:
        pcm_bytes = base64.b64decode(data.pcm_base64)
    except Exception as e:
        return {"error": f"Invalid base64 PCM: {str(e)}"}

    # Generate unique filenames
    pcm_path = f"temp_{uuid.uuid4()}.pcm"
    mp3_filename = f"{uuid.uuid4()}.mp3"
    mp3_path = f"converted/{mp3_filename}"

    # Save PCM bytes to temp file
    with open(pcm_path, "wb") as f:
        f.write(pcm_bytes)

    # Convert PCM → high-quality MP3
    try:
        (
            ffmpeg
            .input(
                pcm_path,
                format="s16le",  # 16-bit PCM
                ar=24000,        # sample rate of input
                ac=1             # mono
            )
            .output(
                mp3_path,
                format="mp3",
                acodec="libmp3lame",
                audio_bitrate="192k",  # high-quality MP3
                ar=48000               # upsample to 48kHz for cleaner playback
            )
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        # Remove temp PCM file
        os.remove(pcm_path)
        return {"error": f"FFmpeg error: {e.stderr.decode()}"}

    # Remove temp PCM file
    os.remove(pcm_path)

    # Determine Render URL dynamically (works locally too)
    base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")
    mp3_url = f"{base_url}/converted/{mp3_filename}"

    return {"mp3_url": mp3_url}
