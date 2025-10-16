#!/usr/bin/env python3
"""
Route53 DNS Failover Script

✅ Checks the primary record health using HealthCheckId
✅ If primary health check fails, promotes secondary record
✅ Uses hardcoded AWS credentials and environment configs
"""

import boto3
import logging
import sys
from botocore.exceptions import ClientError, NoCredentialsError

# =============================
# 🔧 Hardcoded Configuration
# =============================
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""
AWS_SESSION_TOKEN = None  # Optional, leave None for IAM user
AWS_REGION = ""

HOSTED_ZONE_ID = ""
RECORD_NAME = ""       # Common DNS record name
RECORD_TYPE = "A"                     # A or CNAME
PRIMARY_IP = "52.66.201.244"               # Primary record IP
SECONDARY_IP = "15.207.109.242"             # Secondary record IP
PRIMARY_HEALTH_CHECK_ID = "c136e72f-472e-4b71-890c-b95b57583097"

TTL = 60
LOG_FILE = "./route53_failover.log"

# =============================
# 🪵 Logging Setup
# =============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# =============================
# 🧠 AWS Client
# =============================
try:
    route53 = boto3.client(
        "route53",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )
except (NoCredentialsError, ClientError) as e:
    logging.error(f"Failed to create Route53 client: {e}")
    sys.exit(1)

# =============================
# ⚙️ Helper: Get Health Check Status
# =============================
def is_primary_healthy(health_check_id):
    try:
        response = route53.get_health_check_status(HealthCheckId=health_check_id)
        unhealthy = 0
        total = 0

        for obs in response.get("HealthCheckObservations", []):
            region = obs.get("Region", "Unknown")
            status = obs["StatusReport"]["Status"]
            total += 1
            if "failure" in status.lower():
                unhealthy += 1
                logging.warning(f"[{region}] reported FAILURE for health check {health_check_id}")
            else:
                logging.info(f"[{region}] reported SUCCESS for health check {health_check_id}")

        if unhealthy >= total / 2:
            logging.error("Primary health check failed in majority of regions.")
            return False
        else:
            logging.info("Primary health check passed.")
            return True

    except ClientError as e:
        logging.error(f"Failed to get health check status: {e}")
        return False

# =============================
# 🔄 Perform Failover Switch
# =============================
def switch_to_secondary():
    logging.warning("⚠️ Primary DNS is unhealthy. Switching to secondary IP...")

    try:
        route53.change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={
                "Comment": "Failover triggered: switching to secondary",
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": RECORD_NAME,
                            "Type": RECORD_TYPE,
                            "SetIdentifier": "primary",
                            "Failover": "PRIMARY",
                            "TTL": TTL,
                            "ResourceRecords": [{"Value": PRIMARY_IP}],
                            "HealthCheckId": PRIMARY_HEALTH_CHECK_ID
                        }
                    },
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": RECORD_NAME,
                            "Type": RECORD_TYPE,
                            "SetIdentifier": "secondary",
                            "Failover": "SECONDARY",
                            "TTL": TTL,
                            "ResourceRecords": [{"Value": SECONDARY_IP}]
                        }
                    }
                ]
            }
        )

        logging.info("✅ Failover update submitted successfully to Route53.")
        logging.info(f"DNS traffic will now resolve to secondary IP: {SECONDARY_IP}")

    except ClientError as e:
        logging.error(f"❌ Failed to update DNS records: {e}")
        sys.exit(1)

# =============================
# 🚀 Main Logic
# =============================
def main():
    logging.info("🔍 Checking primary DNS health...")
    if is_primary_healthy(PRIMARY_HEALTH_CHECK_ID):
        logging.info("✅ Primary is healthy. No action required.")
    else:
        switch_to_secondary()

if __name__ == "__main__":
    main()
