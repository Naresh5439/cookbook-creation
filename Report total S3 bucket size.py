import boto3
from botocore.exceptions import ClientError, NoCredentialsError

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = "us-west-2"
BUCKET_NAME = "test-timescaledb-1"

# Create an isolated session (ignores EC2/EKS role)
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

s3_client = session.client("s3")

try:
    paginator = s3_client.get_paginator("list_objects_v2")
    total_files = total_size = 0

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            total_files += 1
            total_size += obj["Size"]

    print(f"Bucket: {BUCKET_NAME}")
    print(f"Total Files: {total_files}")
    print(f"Total Size: {total_size / (1024**2):.2f} MB")

except NoCredentialsError:
    print("AWS credentials not found or invalid.")
except ClientError as e:
    print(f"AWS Client Error: {e}")
