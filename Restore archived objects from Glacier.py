import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

# ----- AWS Configuration -----
AWS_ACCESS_KEY_ID = ""  # Replace with your access key
AWS_SECRET_ACCESS_KEY = ""  # Replace with your secret key
AWS_REGION = "us-west-2"
BUCKET_NAME = "test-timescaledb-1"  # Replace with your bucket name

# Restore settings
RESTORE_DAYS = 7  # Number of days the restored object will be temporarily available
RESTORE_TIER = "Standard"  # Options: Standard | Bulk | Expedited

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

try:
    # ----- Paginate through bucket objects -----
    paginator = s3_client.get_paginator("list_objects_v2")
    glacier_objects = []

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            if obj.get("StorageClass") in ["GLACIER", "DEEP_ARCHIVE", "GLACIER_IR"]:
                glacier_objects.append(obj["Key"])

    if not glacier_objects:
        print(f"No archived objects found in bucket '{BUCKET_NAME}'.")
    else:
        print(f"Found {len(glacier_objects)} archived objects. Submitting restore requests...")

        for key in glacier_objects:
            try:
                s3_client.restore_object(
                    Bucket=BUCKET_NAME,
                    Key=key,
                    RestoreRequest={
                        "Days": RESTORE_DAYS,
                        "GlacierJobParameters": {"Tier": RESTORE_TIER}
                    }
                )
                print(f"Restore request submitted for: {key}")
            except ClientError as e:
                print(f"Failed to submit restore for {key}: {e}")

except NoCredentialsError:
    print("AWS credentials not found or invalid.")
except PartialCredentialsError:
    print("Incomplete AWS credentials provided.")
except ClientError as e:
    print(f"AWS Client Error: {e}")
