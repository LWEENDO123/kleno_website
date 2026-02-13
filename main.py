from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import os
import boto3

BASE_DIR = Path(__file__).parent.resolve()

app = FastAPI(title="Kleno Landing")

# --- Railway bucket config from env ---
RAILWAY_BUCKET_NAME = os.getenv("RAILWAY_BUCKET_NAME")
RAILWAY_ACCESS_KEY = os.getenv("RAILWAY_ACCESS_KEY")
RAILWAY_SECRET_KEY = os.getenv("RAILWAY_SECRET_KEY")

# IMPORTANT: use the full endpoint from Railway dashboard, not region
RAILWAY_ENDPOINT = os.getenv("RAILWAY_ENDPOINT", "https://allocated-organizer-y95frn.railway.app")

def get_s3():
    """Create an S3 client only when needed."""
    return boto3.client(
        "s3",
        aws_access_key_id=RAILWAY_ACCESS_KEY,
        aws_secret_access_key=RAILWAY_SECRET_KEY,
        endpoint_url=RAILWAY_ENDPOINT
    )

@app.get("/health")
def health_check():
    """Simple health check route to confirm app is running."""
    return {"status": "ok"}

@app.get("/download-apk")
def download_apk():
    """Generate a temporary download link for the APK."""
    try:
        s3 = get_s3()
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": RAILWAY_BUCKET_NAME, "Key": "kleno.apk"},
            ExpiresIn=3600  # link valid for 1 hour
        )
        return JSONResponse({"download_url": url})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# --- Serve static assets ---
app.mount("/images", StaticFiles(directory=str(BASE_DIR / "images")), name="images")
app.mount("/video", StaticFiles(directory=str(BASE_DIR / "video")), name="video")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "website")), name="static")



@app.get("/")
def homepage():
    """Serve index.html as the homepage."""
    return FileResponse(BASE_DIR / "website" / "index.html")






