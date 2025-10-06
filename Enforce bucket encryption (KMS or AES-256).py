import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

# ----- AWS Configuration -----
AWS_ACCESS_KEY_ID = ""  # Fill your access key
AWS_SECRET_ACCESS_KEY = ""  # Fill your secret key
AWS_REGION = "us-west-2"
BUCKET_NAME = "test-timescaledb-1"

ENCRYPTION_TYPE = "AES256"  # or "aws:kms"
KMS_KEY_ID = "arn:aws:kms:us-west-2:123456789012:key/your-kms-key-id"

# ----- Force explicit credentials -----
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise NoCredentialsError("No AWS credentials provided explicitly!")

# Create isolated session
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

s3_client = session.client("s3")

try:
    # ----- Get current encryption configuration -----
    try:
        current = s3_client.get_bucket_encryption(Bucket=BUCKET_NAME)
        rules = current["ServerSideEncryptionConfiguration"]["Rules"]
        print(f"Bucket '{BUCKET_NAME}' already has encryption configured: {rules}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
            print(f"Bucket '{BUCKET_NAME}' has no encryption. Applying now...")
        else:
            raise e

    # ----- Apply encryption -----
    if ENCRYPTION_TYPE == "AES256":
        s3_client.put_bucket_encryption(
            Bucket=BUCKET_NAME,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}
                ]
            }
        )
        print(f"AES-256 encryption enabled for bucket '{BUCKET_NAME}'.")
    elif ENCRYPTION_TYPE == "aws:kms":
        s3_client.put_bucket_encryption(
            Bucket=BUCKET_NAME,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'aws:kms',
                        'KMSMasterKeyID': KMS_KEY_ID
                    }}
                ]
            }
        )
        print(f"KMS encryption enabled for bucket '{BUCKET_NAME}' with key {KMS_KEY_ID}.")
    else:
        print("Invalid ENCRYPTION_TYPE. Use 'AES256' or 'aws:kms'.")

except NoCredentialsError:
    print("AWS credentials not found or invalid.")
except PartialCredentialsError:
    print("Incomplete AWS credentials provided.")
except ClientError as e:
    print(f"AWS Client Error: {e}")
