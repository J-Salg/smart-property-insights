"""
Upload trained artifacts to S3.
Run once after training (before EC2 deploy).

Auth methods:
    - .env (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)
    - ~/.aws/credentials
    - EC2 IAM role (recommended)
"""
import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

ARTIFACTS_DIR = os.getenv("ARTIFACTS_DIR", "artifacts/")
S3_BUCKET = os.getenv("S3_BUCKET", "smart-property-models")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_PREFIX = "models/"

ARTIFACTS = [
    "price_model.keras",
    "price_scaler.joblib",
    "energy_model.keras",
    "energy_scaler.joblib",
]


def _ensure_bucket(s3, bucket: str, region: str) -> None:
    # Create bucket if missing
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"  Bucket '{bucket}' already exists.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "404":
            print(f"  Creating bucket '{bucket}' in {region}...")
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket)
            else:
                s3.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )

            s3.put_public_access_block(
                Bucket=bucket,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
            )
            print(f"  Bucket created (public access blocked).")
        elif code in ("403", "AccessDenied"):
            print(
                f"\nERROR: Bucket name '{bucket}' already exists in another AWS account.\n"
                f"S3 bucket names are globally unique across all accounts.\n"
                f"\nTo fix: set a unique S3_BUCKET name in your .env file, e.g.:\n"
                f"  S3_BUCKET=smart-property-insights-yourname\n"
                f"\nThen re-run this script."
            )
            sys.exit(1)
        else:
            raise


def upload() -> None:
    print(f"\nUploading s3://{S3_BUCKET}/{S3_PREFIX}")
    print(f"Region : {AWS_REGION}")
    print(f"Source : {ARTIFACTS_DIR}\n")

    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        _ensure_bucket(s3, S3_BUCKET, AWS_REGION)
    except NoCredentialsError:
        print("ERROR: AWS credentials not found.")
        print("Set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in .env, or configure ~/.aws/credentials.")
        sys.exit(1)

    uploaded = 0
    for filename in ARTIFACTS:
        local_path = os.path.join(ARTIFACTS_DIR, filename)
        s3_key = f"{S3_PREFIX}{filename}"

        if not os.path.exists(local_path):
            print(f"  SKIP  {filename}  (not found locally — run training scripts first)")
            continue

        size_kb = os.path.getsize(local_path) / 1024
        print(f"  Uploading  {filename}  ({size_kb:.1f} KB)  →  s3://{S3_BUCKET}/{s3_key}")
        s3.upload_file(local_path, S3_BUCKET, s3_key)
        print(f"             Done.")
        uploaded += 1

    print(f"\n{uploaded}/{len(ARTIFACTS)} artifacts uploaded.")
    if uploaded == len(ARTIFACTS):
        print("\nNext: set MODEL_SOURCE=s3 on EC2.")

if __name__ == "__main__":
    upload()
