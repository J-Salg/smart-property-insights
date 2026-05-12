"""
Resolve model artifact paths.

Priority:
    1. Local artifact
    2. S3 download + local cache
    3. FileNotFoundError

Predictors stay storage-agnostic.
"""
import os
import logging
from flask import current_app

logger = logging.getLogger(__name__)

_S3_PREFIX = "models/"


def resolve_artifact(filename: str) -> str:
    """Return a local filesystem path to *filename*, downloading from S3 if needed."""
    artifacts_dir = current_app.config["ARTIFACTS_DIR"]
    os.makedirs(artifacts_dir, exist_ok=True)
    local_path = os.path.join(artifacts_dir, filename)

    if os.path.exists(local_path):
        logger.debug("Artifact '%s' found in local cache.", filename)
        return local_path

    if current_app.config.get("MODEL_SOURCE") != "s3":
        raise FileNotFoundError(
            f"Artifact '{filename}' not found at '{local_path}'. "
            "Run the training scripts first, or set MODEL_SOURCE=s3 in .env."
        )

    return _download_from_s3(filename, local_path)


def _download_from_s3(filename: str, local_path: str) -> str:
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise RuntimeError("boto3 is required for S3 model loading. Install it with: pip install boto3")

    bucket = current_app.config["S3_BUCKET"]
    region = current_app.config["AWS_REGION"]
    s3_key = f"{_S3_PREFIX}{filename}"

    logger.info("Downloading s3://%s/%s → %s", bucket, s3_key, local_path)

    s3 = boto3.client("s3", region_name=region)
    try:
        s3.download_file(bucket, s3_key, local_path)
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            raise FileNotFoundError(
                f"Artifact '{s3_key}' does not exist in S3 bucket '{bucket}'. "
                "Upload models first with: python scripts/upload_models_to_s3.py"
            ) from exc
        raise RuntimeError(f"S3 download failed for '{s3_key}': {exc}") from exc

    logger.info("Download complete: %s", filename)
    return local_path
