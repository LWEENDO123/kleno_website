from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

BASE_DIR = Path(__file__).parent.resolve()

app = FastAPI(title="Kleno Landing")

# --- Railway bucket config from env ---
RAILWAY_BUCKET_NAME = os.getenv("RAILWAY_BUCKET_NAME")
RAILWAY_BUCKET_REGION = os.getenv("RAILWAY_BUCKET_REGION")
RAILWAY_ACCESS_KEY = os.getenv("RAILWAY_ACCESS_KEY")
RAILWAY_SECRET_KEY = os.getenv("RAILWAY_SECRET_KEY")

# Debug print (remove in production)
print("Bucket:", RAILWAY_BUCKET_NAME)
print("Region:", RAILWAY_BUCKET_REGION)

# Serve images first
app.mount("/images", StaticFiles(directory=str(BASE_DIR / "images")), name="images")

# Serve videos
app.mount("/video", StaticFiles(directory=str(BASE_DIR / "video")), name="video")

# Finally serve HTML files from /website
app.mount("/", StaticFiles(directory=str(BASE_DIR / "website"), html=True), name="site")
