from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import boto3

BASE_DIR = Path(__file__).parent.resolve()

app = FastAPI(title="Kleno Landing")

# --- Railway bucket config from env ---
RAILWAY_BUCKET_NAME = os.getenv("RAILWAY_BUCKET_NAME")
RAILWAY_BUCKET_REGION = os.getenv("RAILWAY_BUCKET_REGION")
RAILWAY_ACCESS_KEY = os.getenv("RAILWAY_ACCESS_KEY")
RAILWAY_SECRET_KEY = os.getenv("RAILWAY_SECRET_KEY")

# Initialize S3 client (Railway buckets are S3-compatible)
s3 = boto3.client(
    "s3",
    aws_access_key_id=RAILWAY_ACCESS_KEY,
    aws_secret_access_key=RAILWAY_SECRET_KEY,
    endpoint_url=f"https://{RAILWAY_BUCKET_REGION}.railway.app"
)

@app.get("/download-apk")
def download_apk():
    """Generate a temporary download link for the APK."""
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": RAILWAY_BUCKET_NAME, "Key": "kleno.apk"},
        ExpiresIn=3600  # link valid for 1 hour
    )
    return JSONResponse({"download_url": url})

# Serve images
app.mount("/images", StaticFiles(directory=str(BASE_DIR / "images")), name="images")

# Serve videos
app.mount("/video", StaticFiles(directory=str(BASE_DIR / "video")), name="video")

# Serve HTML
app.mount("/", StaticFiles(directory=str(BASE_DIR / "website"), html=True), name="site")
