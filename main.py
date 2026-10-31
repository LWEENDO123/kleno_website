from botocore.client import Config
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pathlib import Path
import os
import boto3

BASE_DIR = Path(__file__).parent.resolve()

app = FastAPI(title="Kleno Landing")

# --- Railway bucket config from env ---
# Prefer Railway's bucket references / AWS-compatible names. Keep the
# RAILWAY_* aliases so existing deployments continue to work during migration.
RAILWAY_BUCKET_NAME = (
    os.getenv("BUCKET")
    or os.getenv("AWS_S3_BUCKET_NAME")
    or os.getenv("RAILWAY_BUCKET_NAME")
)
RAILWAY_ACCESS_KEY = (
    os.getenv("ACCESS_KEY_ID")
    or os.getenv("AWS_ACCESS_KEY_ID")
    or os.getenv("RAILWAY_ACCESS_KEY")
)
RAILWAY_SECRET_KEY = (
    os.getenv("SECRET_ACCESS_KEY")
    or os.getenv("AWS_SECRET_ACCESS_KEY")
    or os.getenv("RAILWAY_SECRET_KEY")
)
RAILWAY_ENDPOINT = (
    os.getenv("ENDPOINT")
    or os.getenv("AWS_ENDPOINT_URL")
    or os.getenv("RAILWAY_ENDPOINT")
    or "https://t3.storageapi.dev"
)
#lll
# Railway's bucket credentials use region "auto". The SDK's default region
# (us-east-1) can produce a URL that looks valid but fails signature checks.
RAILWAY_REGION = (
    os.getenv("REGION")
    or os.getenv("AWS_DEFAULT_REGION")
    or os.getenv("RAILWAY_REGION")
    or "auto"
)
# Current Railway buckets use virtual-hosted URLs; older buckets may require
# path style. Set AWS_S3_URL_STYLE to the value shown on the bucket's Credentials tab.
RAILWAY_URL_STYLE = (
    os.getenv("AWS_S3_URL_STYLE")
    or os.getenv("RAILWAY_URL_STYLE")
    or "virtual"
).strip().lower()
if RAILWAY_URL_STYLE not in {"virtual", "path"}:
    raise RuntimeError("AWS_S3_URL_STYLE must be either 'virtual' or 'path'")

def get_s3():
    """Create S3 client."""
    return boto3.client(
        "s3",
        aws_access_key_id=RAILWAY_ACCESS_KEY,
        aws_secret_access_key=RAILWAY_SECRET_KEY,
        endpoint_url=RAILWAY_ENDPOINT,
        region_name=RAILWAY_REGION,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": RAILWAY_URL_STYLE},
        ),
    )

@app.get("/health")
def health_check():
    """Simple health check route to confirm app is running."""
    return {"status": "ok"}

@app.get("/download-apk")
def download_apk():
    """Generate a fresh presigned URL every request."""
    try:
        s3 = get_s3()

        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": RAILWAY_BUCKET_NAME,
                "Key": "kleno.apk"
            },
            ExpiresIn=604800
        )

        return RedirectResponse(url)

    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )

# --- Serve static assets ---
app.mount("/images", StaticFiles(directory=str(BASE_DIR / "images")), name="images")
app.mount("/video", StaticFiles(directory=str(BASE_DIR / "video")), name="video")
# Mount the website folder so index.html, features.html, favicon.ico, etc. are served automatically
app.mount("/", StaticFiles(directory=str(BASE_DIR / "website"), html=True), name="website")

# Explicit routes for homepage and features
@app.get("/")
def homepage():
    """Serve index.html as the homepage."""
    return FileResponse(BASE_DIR / "website" / "index.html")

@app.get("/features.html")
def features_page():
    """Serve features.html explicitly."""
    return FileResponse(BASE_DIR / "website" / "features.html")

@app.get("/favicon.ico")
def favicon():
    """Serve favicon.ico explicitly."""
    return FileResponse(BASE_DIR / "website" / "favicon.ico")
