
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from datetime import datetime, timezone, timedelta

# ----- AWS Configuration -----
AWS_ACCESS_KEY_ID = ""  # Replace with your access key
AWS_SECRET_ACCESS_KEY = ""  # Replace with your secret key
AWS_REGION = "us-west-2"
BUCKET_NAME = "test-timescaledb-2"  # Replace with your bucket name

# Delete settings
OLDER_THAN_DAYS = 30  # Delete objects older than X days

# ----- Force explicit credentials -----
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise NoCredentialsError("No AWS credentials provided explicitly!")

# Create isolated session (ignores EC2/EKS roles)
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
s3_client = session.client("s3")

# Calculate cutoff datetime
cutoff_date = datetime.now(timezone.utc) - timedelta(days=OLDER_THAN_DAYS)

try:
    paginator = s3_client.get_paginator("list_objects_v2")
    deleted_count = 0

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            last_modified = obj["LastModified"]
            key = obj["Key"]

            if last_modified < cutoff_date:
                try:
                    s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
                    deleted_count += 1
                    print(f"Deleted: {key} (LastModified: {last_modified})")
                except ClientError as e:
                    print(f"Failed to delete {key}: {e}")

    print(f"\nTotal objects deleted: {deleted_count}")

except NoCredentialsError:
    print("AWS credentials not found or invalid.")
except PartialCredentialsError:
    print("Incomplete AWS credentials provided.")
except ClientError as e:
    print(f"AWS Client Error: {e}")
