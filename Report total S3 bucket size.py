Name: "Report total S3 bucket size"
description: "Identifies S3 buckets in AWS that are publicly accessible by inspecting their bucket policies using AWS CLI."
category: "Cloud Security"
platform: "AWS"
type: "Shell Script"
script_data: |
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

AWS_ACCESS_KEY_ID = ""  # Fill your access key
AWS_SECRET_ACCESS_KEY = ""  # Fill your secret key
AWS_REGION = "us-west-2"
BUCKET_NAME = "test-timescaledb-1"

# ----- Force use of explicit credentials only -----
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise NoCredentialsError("No AWS credentials provided explicitly!")

# Create a session using only the provided credentials
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
except PartialCredentialsError:
    print("Incomplete AWS credentials provided.")
except ClientError as e:
    print(f"AWS Client Error: {e}")
