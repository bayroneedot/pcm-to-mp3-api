from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import ffmpeg
import os
import uuid

app = FastAPI()

# Folder to store converted files
os.makedirs("converted", exist_ok=True)

@app.post("/convert")
async def convert_pcm_to_mp3(file: UploadFile = File(...)):
    # Generate unique filenames
    pcm_path = f"temp_{uuid.uuid4()}.pcm"
    mp3_path = f"converted/{uuid.uuid4()}.mp3"

    # Save uploaded PCM file
    with open(pcm_path, "wb") as f:
        f.write(await file.read())

    # Convert PCM -> MP3 using ffmpeg
    try:
        (
            ffmpeg
            .input(pcm_path, format='s16le', ar='24000', ac=1)  # 16-bit PCM, mono
            .output(mp3_path)
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        return {"error": str(e)}

    # Remove the temporary PCM file
    os.remove(pcm_path)

    # Return MP3 as downloadable file
    return FileResponse(mp3_path, media_type='audio/mpeg', filename=os.path.basename(mp3_path))
