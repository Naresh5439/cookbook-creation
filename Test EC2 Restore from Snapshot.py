import boto3
import time

# -----------------------------
# AWS Credentials (hardcoded)
# -----------------------------
aws_access_key = ""
aws_secret_key = ""
region = "us-west-2"

# -----------------------------
# Inputs
# -----------------------------
vpc_id = ""
subnet_id = ""
snapshot_id = ""
ami_id = ""        # Bootable AMI
instance_type = "t3.micro"
security_group_ids = [""]
key_name = ""
mount_point = "/mnt/snapshot"
device_name = "/dev/sdf"

# -----------------------------
# Boto3 clients
# -----------------------------
ec2_client = boto3.client(
    "ec2",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region
)
ec2_resource = boto3.resource(
    "ec2",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region
)

try:
    # Step 1: Create EBS volume from snapshot
    print(f"Creating EBS volume from snapshot {snapshot_id} in VPC {vpc_id}...")
    subnet_info = ec2_client.describe_subnets(SubnetIds=[subnet_id])['Subnets'][0]
    az = subnet_info['AvailabilityZone']

    volume_response = ec2_client.create_volume(
        SnapshotId=snapshot_id,
        AvailabilityZone=az,
        VolumeType="gp2",
        TagSpecifications=[{
            'ResourceType': 'volume',
            'Tags': [
                {'Key': 'Name', 'Value': 'Snapshot-Volume'},
                {'Key': 'VPC', 'Value': vpc_id}
            ]
        }]
    )
    volume_id = volume_response['VolumeId']
    print(f"Volume {volume_id} created. Waiting for it to become available...")
    waiter = ec2_client.get_waiter('volume_available')
    waiter.wait(VolumeIds=[volume_id])
    print(f"Volume {volume_id} is ready.")

    # Step 2: Launch EC2 instance from AMI with User Data to mount volume
    user_data_script = f"""#!/bin/bash
mkdir -p {mount_point}
mount {device_name} {mount_point}
chmod 777 {mount_point}
"""

    print(f"Launching EC2 instance in VPC {vpc_id}...")
    instances = ec2_resource.create_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        MaxCount=1,
        MinCount=1,
        NetworkInterfaces=[{
            'SubnetId': subnet_id,
            'DeviceIndex': 0,
            'AssociatePublicIpAddress': True,
            'Groups': security_group_ids
        }],
        UserData=user_data_script,
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': 'Test-Instance-Snapshot'}]
        }]
    )

    instance = instances[0]
    instance.wait_until_running()
    instance.reload()
    print(f"Instance {instance.id} running at IP: {instance.public_ip_address}")

    # Step 3: Attach snapshot volume as secondary
    print(f"Attaching volume {volume_id} to instance {instance.id} as {device_name}...")
    ec2_client.attach_volume(
        VolumeId=volume_id,
        InstanceId=instance.id,
        Device=device_name
    )

    print("✅ Volume attached successfully and will mount automatically at boot.")
    print(f"SSH: ssh -i {key_name} ec2-user@{instance.public_ip_address}")

except Exception as e:
    print("❌ Error occurred:", e)
