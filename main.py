from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import ffmpeg
import os
import uuid
import base64

app = FastAPI()

# Folder to store converted files
os.makedirs("converted", exist_ok=True)

class PCMData(BaseModel):
    pcm_base64: str  # base64-encoded PCM string

@app.post("/convert")
async def convert_pcm_to_mp3(data: PCMData):
    # decode base64 string to bytes
    pcm_bytes = base64.b64decode(data.pcm_base64)

    # generate unique filenames
    pcm_path = f"temp_{uuid.uuid4()}.pcm"
    mp3_path = f"converted/{uuid.uuid4()}.mp3"

    # save bytes to temporary PCM file
    with open(pcm_path, "wb") as f:
        f.write(pcm_bytes)

    # convert PCM -> MP3 using ffmpeg
    try:
        (
            ffmpeg
            .input(pcm_path, format='s16le', ar='24000', ac=1)
            .output(mp3_path)
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        return {"error": str(e)}

    # remove the temp PCM file
    os.remove(pcm_path)

    # return MP3 as downloadable file
    return FileResponse(mp3_path, media_type='audio/mpeg', filename=os.path.basename(mp3_path))
