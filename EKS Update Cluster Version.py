import boto3
import time

# ===========================
# AWS Configuration
# ===========================
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""
REGION = "ap-south-1"
CLUSTER_NAME = "testing-eks-cluster"
NEW_VERSION = "1.30"  # Kubernetes version to upgrade to

# ===========================
# Create EKS client
# ===========================
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

eks_client = session.client("eks")

# ===========================
# Update Cluster Version
# ===========================
response = eks_client.update_cluster_version(
    name=CLUSTER_NAME,
    version=NEW_VERSION
)

update_id = response['update']['id']
print(f"[INFO] Cluster version update initiated. Update ID: {update_id}")

# ===========================
# Wait for Update Completion
# ===========================
while True:
    update_status = eks_client.describe_update(
        name=CLUSTER_NAME,
        updateId=update_id
    )['update']['status']
    
    print(f"[INFO] Current cluster update status: {update_status}")
    
    if update_status in ['Successful', 'Failed', 'Cancelled']:
        break
    time.sleep(15)

print(f"[INFO] Final cluster update status: {update_status}")
