"""Create and manage a custom VPC, then move the EC2 workload into it.

Builds (idempotently, all tagged Project=bz-agent):
  - VPC 10.0.0.0/16 (DNS support + hostnames enabled)
  - Internet Gateway, attached
  - Public subnet 10.0.1.0/24 (auto-assign public IP)
  - Route table: 0.0.0.0/0 -> IGW, associated with the subnet
  - DynamoDB *gateway* VPC endpoint (free) on that route table -> private,
    in-VPC access to DynamoDB without traversing the public internet
  - Security group allowing inbound TCP 8080

Then terminates any bz-agent-ec2 instances in the default VPC and launches a
fresh one inside this VPC's public subnet. Prints the new public endpoint.

This directly demonstrates the course objective "Create and manage a Virtual
Private Cloud", including subnetting, routing, an internet gateway, a VPC
endpoint, and security-group network controls.
"""
from __future__ import annotations

import boto3

REGION = "eu-central-1"
ACCOUNT = boto3.client("sts").get_caller_identity()["Account"]
IMAGE = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/bz-agent:server"
REGISTRY = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com"
PROFILE = "bz-agent-ec2-profile"
TAG = [{"Key": "Project", "Value": "bz-agent"}]

ec2 = boto3.client("ec2", region_name=REGION)


def _tagspec(kind: str, name: str):
    return [{"ResourceType": kind, "Tags": TAG + [{"Key": "Name", "Value": name}]}]


def _first(items, key):
    return items[0][key] if items else None


def find_by_tag(resource: str, name: str):
    filt = [{"Name": "tag:Name", "Values": [name]},
            {"Name": "tag:Project", "Values": ["bz-agent"]}]
    if resource == "vpc":
        return _first(ec2.describe_vpcs(Filters=filt)["Vpcs"], "VpcId")
    if resource == "subnet":
        return _first(ec2.describe_subnets(Filters=filt)["Subnets"], "SubnetId")
    if resource == "igw":
        return _first(ec2.describe_internet_gateways(Filters=filt)["InternetGateways"], "InternetGatewayId")
    if resource == "rtb":
        return _first(ec2.describe_route_tables(Filters=filt)["RouteTables"], "RouteTableId")
    if resource == "sg":
        return _first(ec2.describe_security_groups(Filters=filt)["SecurityGroups"], "GroupId")
    return None


def ensure_vpc() -> str:
    vpc_id = find_by_tag("vpc", "bz-agent-vpc")
    if vpc_id:
        return vpc_id
    vpc_id = ec2.create_vpc(CidrBlock="10.0.0.0/16",
                            TagSpecifications=_tagspec("vpc", "bz-agent-vpc"))["Vpc"]["VpcId"]
    ec2.get_waiter("vpc_available").wait(VpcIds=[vpc_id])
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})
    return vpc_id


def ensure_igw(vpc_id: str) -> str:
    igw_id = find_by_tag("igw", "bz-agent-igw")
    if not igw_id:
        igw_id = ec2.create_internet_gateway(
            TagSpecifications=_tagspec("internet-gateway", "bz-agent-igw"))["InternetGateway"]["InternetGatewayId"]
    # attach if not attached
    igw = ec2.describe_internet_gateways(InternetGatewayIds=[igw_id])["InternetGateways"][0]
    if not igw["Attachments"]:
        ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    return igw_id


def ensure_subnet(vpc_id: str) -> str:
    subnet_id = find_by_tag("subnet", "bz-agent-public-subnet")
    if subnet_id:
        return subnet_id
    az = ec2.describe_availability_zones()["AvailabilityZones"][0]["ZoneName"]
    subnet_id = ec2.create_subnet(
        VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=az,
        TagSpecifications=_tagspec("subnet", "bz-agent-public-subnet"))["Subnet"]["SubnetId"]
    ec2.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={"Value": True})
    return subnet_id


def ensure_routing(vpc_id: str, subnet_id: str, igw_id: str) -> str:
    rtb_id = find_by_tag("rtb", "bz-agent-public-rtb")
    if not rtb_id:
        rtb_id = ec2.create_route_table(
            VpcId=vpc_id, TagSpecifications=_tagspec("route-table", "bz-agent-public-rtb"))["RouteTable"]["RouteTableId"]
    # default route to IGW
    try:
        ec2.create_route(RouteTableId=rtb_id, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_id)
    except ec2.exceptions.ClientError:
        pass  # route already exists
    # associate subnet
    assoc = ec2.describe_route_tables(RouteTableIds=[rtb_id])["RouteTables"][0]["Associations"]
    if not any(a.get("SubnetId") == subnet_id for a in assoc):
        ec2.associate_route_table(RouteTableId=rtb_id, SubnetId=subnet_id)
    # free DynamoDB gateway endpoint on this route table
    eps = ec2.describe_vpc_endpoints(Filters=[{"Name": "vpc-id", "Values": [vpc_id]},
        {"Name": "service-name", "Values": [f"com.amazonaws.{REGION}.dynamodb"]}])["VpcEndpoints"]
    if not eps:
        ec2.create_vpc_endpoint(
            VpcId=vpc_id, ServiceName=f"com.amazonaws.{REGION}.dynamodb",
            VpcEndpointType="Gateway", RouteTableIds=[rtb_id],
            TagSpecifications=_tagspec("vpc-endpoint", "bz-agent-dynamodb-endpoint"))
    return rtb_id


def ensure_sg(vpc_id: str) -> str:
    sg_id = find_by_tag("sg", "bz-agent-vpc-sg")
    if sg_id:
        return sg_id
    sg_id = ec2.create_security_group(
        GroupName="bz-agent-vpc-sg", Description="bz-agent http 8080 (custom VPC)",
        VpcId=vpc_id, TagSpecifications=_tagspec("security-group", "bz-agent-vpc-sg"))["GroupId"]
    ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=[{
        "IpProtocol": "tcp", "FromPort": 8080, "ToPort": 8080,
        "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "demo http"}]}])
    return sg_id


def al2023_ami() -> str:
    imgs = ec2.describe_images(Owners=["amazon"], Filters=[
        {"Name": "name", "Values": ["al2023-ami-2023.*-x86_64"]},
        {"Name": "state", "Values": ["available"]},
        {"Name": "architecture", "Values": ["x86_64"]}])["Images"]
    imgs.sort(key=lambda i: i["CreationDate"], reverse=True)
    return imgs[0]["ImageId"]


def terminate_default_vpc_instances() -> None:
    res = ec2.describe_instances(Filters=[
        {"Name": "tag:Name", "Values": ["bz-agent-ec2"]},
        {"Name": "instance-state-name", "Values": ["running", "pending"]}])["Reservations"]
    ids = [i["InstanceId"] for r in res for i in r["Instances"]]
    if ids:
        ec2.terminate_instances(InstanceIds=ids)
        print("terminated old instances:", ids)


def launch(subnet_id: str, sg_id: str) -> None:
    user_data = f"""#!/bin/bash
set -xe
dnf install -y docker
systemctl enable --now docker
aws ecr get-login-password --region {REGION} | docker login --username AWS --password-stdin {REGISTRY}
docker pull {IMAGE}
docker run -d --restart always -p 8080:8080 \\
  -e LLM_PROVIDER=bedrock -e AWS_REGION={REGION} \\
  -e BEDROCK_MODEL_ID=eu.anthropic.claude-sonnet-4-5-20250929-v1:0 \\
  -e DDB_TABLE_NAME=bz-agent-state {IMAGE}
"""
    run = ec2.run_instances(
        ImageId=al2023_ami(), InstanceType="t3.small", MinCount=1, MaxCount=1,
        SubnetId=subnet_id, SecurityGroupIds=[sg_id],
        IamInstanceProfile={"Name": PROFILE}, UserData=user_data,
        TagSpecifications=_tagspec("instance", "bz-agent-ec2"))
    iid = run["Instances"][0]["InstanceId"]
    print("INSTANCE_ID =", iid)
    ec2.get_waiter("instance_running").wait(InstanceIds=[iid])
    ip = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0].get("PublicIpAddress")
    print("EC2_IN_VPC_READY")
    print("PUBLIC_IP =", ip)
    print("ENDPOINT  = http://%s:8080" % ip)


def main() -> None:
    vpc_id = ensure_vpc()
    igw_id = ensure_igw(vpc_id)
    subnet_id = ensure_subnet(vpc_id)
    ensure_routing(vpc_id, subnet_id, igw_id)
    sg_id = ensure_sg(vpc_id)
    print("VPC_ID    =", vpc_id)
    print("SUBNET_ID =", subnet_id)
    print("SG_ID     =", sg_id)
    terminate_default_vpc_instances()
    launch(subnet_id, sg_id)


if __name__ == "__main__":
    main()
