import boto3

# ===========================
# AWS Configuration
# ===========================
AWS_ACCESS_KEY = ""       # <-- Your AWS Access Key
AWS_SECRET_KEY = ""  # <-- Your AWS Secret Key
REGION = "ap-south-1"
CLUSTER_NAME = "testing-eks-cluster"
NODEGROUP_NAME = "testing-nodegroup"
MIN_NODES = 1
MAX_NODES = 3
DESIRED_NODES = 1

# ===========================
# Step 1: Create boto3 session and EKS client
# ===========================
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

eks_client = session.client("eks")

# ===========================
# Step 2: Update Node Group Scaling
# ===========================
response = eks_client.update_nodegroup_config(
    clusterName=CLUSTER_NAME,
    nodegroupName=NODEGROUP_NAME,
    scalingConfig={
        'minSize': MIN_NODES,
        'maxSize': MAX_NODES,
        'desiredSize': DESIRED_NODES
    }
)

print("[INFO] Node group scaling update initiated.")
print(f"Status: {response['update']['status']}")
print(f"Update ID: {response['update']['id']}")

# ===========================
# Step 3: Optional - Wait for Update Completion
# ===========================
import time

while True:
    status = eks_client.describe_update(
        name=CLUSTER_NAME,
        nodegroupName=NODEGROUP_NAME,
        updateId=response['update']['id']
    )['update']['status']

    print(f"[INFO] Current update status: {status}")
    if status in ['Successful', 'Failed', 'Cancelled']:
        break
    time.sleep(10)

print(f"[INFO] Final node group update status: {status}")
