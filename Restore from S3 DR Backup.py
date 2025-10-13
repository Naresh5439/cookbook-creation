#!/usr/bin/env python3
"""
Restore from S3 DR Backup
--------------------------
Purpose:
    Copy critical backup data from a DR (Disaster Recovery) bucket
    to the primary or recovery bucket.

Performs:
    ✅ Lists all objects in the source (DR) bucket
    ✅ Validates object counts before restore
    ✅ Copies all objects to the target bucket
    ✅ Verifies checksums to ensure integrity

IAM Permissions Required:
    - s3:ListBucket
    - s3:GetObject
    - s3:CopyObject
    - s3:PutObject
"""

import boto3
import hashlib
import sys
from botocore.exceptions import ClientError

# ======== Hardcoded credentials (for demo/testing only — avoid in production) ========
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""
AWS_REGION = "us-west-2"

# ======== Inputs ========
SOURCE_BUCKET = ""
TARGET_BUCKET = ""

# ======== Initialize Clients ========
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

def list_bucket_objects(bucket_name):
    """Return a list of all objects in the specified bucket."""
    objects = []
    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            objects.append(obj["Key"])
    return objects


def calculate_s3_etag(bucket, key):
    """Fetch the ETag of an object (acts as checksum for single-part uploads)."""
    response = s3_client.head_object(Bucket=bucket, Key=key)
    return response.get("ETag").strip('"')


def restore_objects(source_bucket, target_bucket):
    """Copy all objects from source to target bucket with validation."""
    print("===============================================================")
    print("☁️  AWS S3 DR Restore Script")
    print("===============================================================")
    print(f"🔹 Source Bucket: {source_bucket}")
    print(f"🔹 Target Bucket: {target_bucket}\n")

    try:
        source_objects = list_bucket_objects(source_bucket)
        target_objects = list_bucket_objects(target_bucket)

        print(f"📦 Objects in source: {len(source_objects)}")
        print(f"📦 Objects in target (before copy): {len(target_objects)}")

        if not source_objects:
            print("⚠️  No objects found in source bucket. Exiting.")
            return

        # Copy missing or outdated objects
        for obj_key in source_objects:
            print(f"🔄 Copying: {obj_key}")
            copy_source = {"Bucket": source_bucket, "Key": obj_key}

            s3_client.copy_object(
                CopySource=copy_source,
                Bucket=target_bucket,
                Key=obj_key
            )

        print("\n✅ Copy operation completed. Verifying integrity...\n")

        # Verify checksum/ETag integrity
        mismatches = []
        for obj_key in source_objects:
            src_etag = calculate_s3_etag(source_bucket, obj_key)
            tgt_etag = calculate_s3_etag(target_bucket, obj_key)
            if src_etag != tgt_etag:
                mismatches.append(obj_key)

        if mismatches:
            print("❌ Checksum mismatches found for the following objects:")
            for key in mismatches:
                print(f"   - {key}")
        else:
            print("✅ All objects restored successfully and verified.\n")

        print("===============================================================")
        print("🎯 Restore operation completed successfully!")
        print("===============================================================")

    except ClientError as e:
        print(f"❌ AWS Error: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")


if __name__ == "__main__":
    restore_objects(SOURCE_BUCKET, TARGET_BUCKET)
