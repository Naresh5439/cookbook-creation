import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# ----- AWS Configuration -----
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = "us-west-2"
BUCKET_NAME = "test-timescaledb-1"

# Create isolated session (ignores EC2/EKS role)
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

s3_client = session.client("s3")

try:
    # ----- Check versioning status -----
    versioning = s3_client.get_bucket_versioning(Bucket=BUCKET_NAME)
    status = versioning.get("Status")

    if status == "Enabled":
        print(f"Bucket '{BUCKET_NAME}' versioning is already ENABLED.")
    else:
        print(f"Bucket '{BUCKET_NAME}' versioning is not enabled. Enabling now...")
        s3_client.put_bucket_versioning(
            Bucket=BUCKET_NAME,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"Versioning has been ENABLED for bucket '{BUCKET_NAME}'.")

except NoCredentialsError:
    print("AWS credentials not found or invalid.")
except ClientError as e:
    print(f"AWS Client Error: {e}")
