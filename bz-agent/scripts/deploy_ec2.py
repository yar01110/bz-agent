"""Deploy Architecture B: a single EC2 instance running the server container.

Uses the default VPC, a security group opening port 8080, the bz-agent-ec2
instance profile, and user-data that logs into ECR, pulls bz-agent:server, and
runs it. Prints the public endpoint. SSM is enabled (no SSH key needed).
"""
from __future__ import annotations

import base64

import boto3

REGION = "eu-central-1"
ACCOUNT = boto3.client("sts").get_caller_identity()["Account"]
IMAGE = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/bz-agent:server"
REGISTRY = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com"
SG_NAME = "bz-agent-sg"
PROFILE = "bz-agent-ec2-profile"

ec2 = boto3.client("ec2", region_name=REGION)

USER_DATA = f"""#!/bin/bash
set -xe
dnf install -y docker
systemctl enable --now docker
aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {REGISTRY}
docker pull {IMAGE}
docker run -d --restart always -p 8080:8080 \\
  -e LLM_PROVIDER=bedrock \\
  -e AWS_REGION={REGION} \\
  -e BEDROCK_MODEL_ID=eu.anthropic.claude-sonnet-4-5-20250929-v1:0 \\
  -e DDB_TABLE_NAME=bz-agent-state \\
  {IMAGE}
"""


def default_vpc() -> str:
    vpcs = ec2.describe_vpcs(Filters=[{"Name": "isDefault", "Values": ["true"]}])["Vpcs"]
    return vpcs[0]["VpcId"]


def ensure_sg(vpc_id: str) -> str:
    existing = ec2.describe_security_groups(
        Filters=[{"Name": "group-name", "Values": [SG_NAME]},
                 {"Name": "vpc-id", "Values": [vpc_id]}]
    )["SecurityGroups"]
    if existing:
        return existing[0]["GroupId"]
    sg = ec2.create_security_group(
        GroupName=SG_NAME, Description="bz-agent http 8080", VpcId=vpc_id
    )
    sg_id = sg["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[{
            "IpProtocol": "tcp", "FromPort": 8080, "ToPort": 8080,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "demo http"}],
        }],
    )
    return sg_id


def al2023_ami() -> str:
    """Latest Amazon Linux 2023 x86_64 AMI via describe_images (no SSM needed)."""
    images = ec2.describe_images(
        Owners=["amazon"],
        Filters=[
            {"Name": "name", "Values": ["al2023-ami-2023.*-x86_64"]},
            {"Name": "state", "Values": ["available"]},
            {"Name": "architecture", "Values": ["x86_64"]},
        ],
    )["Images"]
    images.sort(key=lambda i: i["CreationDate"], reverse=True)
    return images[0]["ImageId"]


def main() -> None:
    vpc = default_vpc()
    sg = ensure_sg(vpc)
    ami = al2023_ami()

    run = ec2.run_instances(
        ImageId=ami,
        InstanceType="t3.small",
        MinCount=1, MaxCount=1,
        SecurityGroupIds=[sg],
        IamInstanceProfile={"Name": PROFILE},
        UserData=USER_DATA,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "bz-agent-ec2"}],
        }],
    )
    iid = run["Instances"][0]["InstanceId"]
    print("INSTANCE_ID =", iid)
    ec2.get_waiter("instance_running").wait(InstanceIds=[iid])
    desc = ec2.describe_instances(InstanceIds=[iid])
    ip = desc["Reservations"][0]["Instances"][0].get("PublicIpAddress")
    print("EC2_READY")
    print("PUBLIC_IP   =", ip)
    print("ENDPOINT    = http://%s:8080/plan-itinerary" % ip)
    print("(give it ~2-3 min for user-data to install docker + pull image)")


if __name__ == "__main__":
    main()
