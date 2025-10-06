
#!/usr/bin/env python3
"""
Safe S3 Bucket Sync
Copies all objects from a source bucket to a destination bucket.
Throws exceptions if credentials are missing, buckets are missing, or AWS API errors occur.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# --- AWS credentials and inputs ---
AWS_ACCESS_KEY = ""    # Replace with valid key
AWS_SECRET_KEY = ""    # Replace with valid secret
SRC_BUCKET = "test-timescaledb-1"
DEST_BUCKET = "test-timescaledb-2"
REGION = "us-west-2"

if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
    raise ValueError("AWS credentials are missing! Set AWS_ACCESS_KEY and AWS_SECRET_KEY.")

# --- Create S3 client ---
try:
    s3 = boto3.client(
        's3',
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )
except Exception as e:
    raise RuntimeError(f"Failed to create S3 client: {e}")

try:
    # List objects in source bucket
    src_objects = s3.list_objects_v2(Bucket=SRC_BUCKET)
    if 'Contents' not in src_objects:
        raise RuntimeError(f"No objects found in source bucket {SRC_BUCKET}")

    src_keys = [obj['Key'] for obj in src_objects['Contents']]
    print(f"Found {len(src_keys)} objects in source bucket '{SRC_BUCKET}'.")

    # Copy objects to destination bucket
    for key in src_keys:
        copy_source = {'Bucket': SRC_BUCKET, 'Key': key}
        try:
            s3.copy_object(CopySource=copy_source, Bucket=DEST_BUCKET, Key=key)
            print(f"Copied {key} to {DEST_BUCKET}")
        except ClientError as e:
            raise RuntimeError(f"Failed to copy object {key}: {e}")

    # Verify sync by comparing object counts
    dest_objects = s3.list_objects_v2(Bucket=DEST_BUCKET)
    dest_keys = [obj['Key'] for obj in dest_objects.get('Contents', [])]
    print(f"{len(dest_keys)} objects in destination bucket '{DEST_BUCKET}'.")

    if set(src_keys) == set(dest_keys):
        print("Sync successful: All objects copied.")
    else:
        raise RuntimeError("Object count mismatch: Some objects may not have copied correctly.")

except NoCredentialsError:
    raise RuntimeError("AWS credentials not found or invalid.")

except ClientError as e:
    raise RuntimeError(f"AWS API error: {e}")

except Exception as e:
    raise RuntimeError(f"Unexpected error: {e}")
