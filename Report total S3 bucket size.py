#!/usr/bin/env python3
"""
s3_bucket_size_venv.py
- Creates a virtual environment automatically if needed
- Installs boto3 inside the virtual environment
- Configure AWS credentials programmatically
- Calculate total size of an S3 bucket (handles pagination)
- Print summary report
"""

import os
import subprocess
import sys

VENV_DIR = "venv_s3_script"

# ----- Step 1: Create virtual environment if it doesn't exist -----
if not os.path.exists(VENV_DIR):
    print(f"Creating virtual environment in {VENV_DIR}...")
    subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])

venv_python = os.path.join(VENV_DIR, "bin", "python")
if os.path.abspath(sys.executable) != os.path.abspath(venv_python):
    # Re-run the script using the venv's Python
    os.execv(venv_python, [venv_python] + sys.argv)

# ----- Step 2: Ensure boto3 is installed in venv -----
try:
    import boto3
except ImportError:
    print("boto3 not found in virtual environment. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "boto3"])
    import boto3

from botocore.exceptions import NoCredentialsError, ClientError

# ----- CONFIG: AWS credentials -----
AWS_ACCESS_KEY_ID = ""      # Replace with your access key
AWS_SECRET_ACCESS_KEY = ""  # Replace with your secret key
AWS_REGION = "us-west-2"                   # Replace with your preferred region
BUCKET_NAME = "test-timescaledb-1"           # Replace with your bucket name

# ----- INITIALIZE S3 CLIENT -----
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# ----- CALCULATE BUCKET SIZE -----
total_size = 0
total_files = 0

print(f"Starting size calculation for bucket: {BUCKET_NAME}")

try:
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=BUCKET_NAME)

    for page in page_iterator:
        if "Contents" in page:
            for obj in page["Contents"]:
                total_files += 1
                total_size += obj["Size"]
                print(f"Counting: {obj['Key']} ({obj['Size']} bytes)")

    # ----- SUMMARY -----
    print("\n===== SUMMARY =====")
    print(f"Bucket Name : {BUCKET_NAME}")
    print(f"Total Files : {total_files}")
    print(f"Total Size  : {total_size / (1024**2):.2f} MB")  # Bytes to MB

except NoCredentialsError:
    print("AWS credentials not found or invalid.")
except ClientError as e:
    print(f"An error occurred: {e}")
