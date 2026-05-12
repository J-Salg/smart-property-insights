import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

MODEL_SOURCE  = os.getenv("MODEL_SOURCE", "local")
S3_BUCKET     = os.getenv("S3_BUCKET", "smart-property-models")
AWS_REGION    = os.getenv("AWS_REGION", "us-east-1")
S3_PREFIX     = "static/models/"
MODELS_DIR    = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "app", "static", "models")
)

GLB_FILES = [
    "price_building.glb",
    "energy_building.glb",
]


def download() -> None:
    if MODEL_SOURCE != "s3":
        print("[models] MODEL_SOURCE != 's3' — skipping 3D model download.")
        return

    print(f"[models] Checking 3D models in s3://{S3_BUCKET}/{S3_PREFIX}")
    os.makedirs(MODELS_DIR, exist_ok=True)

    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
    except NoCredentialsError:
        print("[models] WARNING: No AWS credentials — skipping 3D model download.")
        return

    for filename in GLB_FILES:
        dest = os.path.join(MODELS_DIR, filename)
        if os.path.exists(dest):
            print(f"[models] {filename} already present — skipping.")
            continue

        s3_key = f"{S3_PREFIX}{filename}"
        print(f"[models] Downloading {filename} ...", end=" ", flush=True)
        try:
            s3.download_file(S3_BUCKET, s3_key, dest)
            print(f"{os.path.getsize(dest) / 1024:.1f} KB")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("404", "NoSuchKey"):
                print(f"not found in S3 — fallback geometry will be used.")
            else:
                print(f"failed ({e}) — fallback geometry will be used.")
        except NoCredentialsError:
            print("no credentials — fallback geometry will be used.")
            return


if __name__ == "__main__":
    download()
