"""Elasticity: put the EC2 workload behind an Application Load Balancer + Auto
Scaling Group, demonstrating horizontal scaling and self-healing ("cattle").

Builds (idempotently, in the existing bz-agent VPC):
  - a second public subnet in a different AZ (an ALB needs >=2 AZs)
  - an ALB security group (inbound 80)
  - an internet-facing Application Load Balancer across both subnets
  - a target group (HTTP 8080, health check /health)
  - an HTTP :80 listener -> target group
  - a Launch Template (the server image via user-data)
  - an Auto Scaling Group (desired 2, min 1, max 4) attached to the target group,
    with ELB health checks so terminated/unhealthy instances are auto-replaced

Prints the ALB DNS name. Tear down with destroy_elastic.py.
Note: AmazonEC2FullAccess already grants elasticloadbalancing:* and autoscaling:*.
"""
from __future__ import annotations

import base64

import boto3

REGION = "eu-central-1"
ACCOUNT = boto3.client("sts").get_caller_identity()["Account"]
IMAGE = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/bz-agent:server"
REGISTRY = f"{ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com"
PROFILE = "bz-agent-ec2-profile"
TAG = [{"Key": "Project", "Value": "bz-agent"}]

ec2 = boto3.client("ec2", region_name=REGION)
elb = boto3.client("elbv2", region_name=REGION)
asg = boto3.client("autoscaling", region_name=REGION)


def _tagspec(kind, name):
    return [{"ResourceType": kind, "Tags": TAG + [{"Key": "Name", "Value": name}]}]


def find_vpc():
    r = ec2.describe_vpcs(Filters=[{"Name": "tag:Name", "Values": ["bz-agent-vpc"]}])["Vpcs"]
    return r[0]["VpcId"]


def find_first_subnet(vpc):
    r = ec2.describe_subnets(Filters=[
        {"Name": "tag:Name", "Values": ["bz-agent-public-subnet"]},
        {"Name": "vpc-id", "Values": [vpc]}])["Subnets"]
    return r[0]["SubnetId"], r[0]["AvailabilityZone"]


def find_rtb(vpc):
    r = ec2.describe_route_tables(Filters=[
        {"Name": "tag:Name", "Values": ["bz-agent-public-rtb"]},
        {"Name": "vpc-id", "Values": [vpc]}])["RouteTables"]
    return r[0]["RouteTableId"]


def find_instance_sg(vpc):
    r = ec2.describe_security_groups(Filters=[
        {"Name": "tag:Name", "Values": ["bz-agent-vpc-sg"]},
        {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
    return r[0]["GroupId"]


def ensure_second_subnet(vpc, first_az, rtb):
    existing = ec2.describe_subnets(Filters=[
        {"Name": "tag:Name", "Values": ["bz-agent-public-subnet-b"]},
        {"Name": "vpc-id", "Values": [vpc]}])["Subnets"]
    if existing:
        return existing[0]["SubnetId"]
    azs = [z["ZoneName"] for z in ec2.describe_availability_zones()["AvailabilityZones"]]
    second_az = next(a for a in azs if a != first_az)
    sn = ec2.create_subnet(VpcId=vpc, CidrBlock="10.0.2.0/24", AvailabilityZone=second_az,
                           TagSpecifications=_tagspec("subnet", "bz-agent-public-subnet-b"))["Subnet"]["SubnetId"]
    ec2.modify_subnet_attribute(SubnetId=sn, MapPublicIpOnLaunch={"Value": True})
    ec2.associate_route_table(RouteTableId=rtb, SubnetId=sn)
    return sn


def ensure_alb_sg(vpc):
    r = ec2.describe_security_groups(Filters=[
        {"Name": "tag:Name", "Values": ["bz-agent-alb-sg"]},
        {"Name": "vpc-id", "Values": [vpc]}])["SecurityGroups"]
    if r:
        return r[0]["GroupId"]
    sg = ec2.create_security_group(GroupName="bz-agent-alb-sg", Description="ALB :80",
        VpcId=vpc, TagSpecifications=_tagspec("security-group", "bz-agent-alb-sg"))["GroupId"]
    ec2.authorize_security_group_ingress(GroupId=sg, IpPermissions=[{
        "IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
        "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}])
    return sg


def ensure_alb(subnets, alb_sg):
    existing = [a for a in elb.describe_load_balancers()["LoadBalancers"]
                if a["LoadBalancerName"] == "bz-agent-alb"] if _safe_lbs() else []
    if existing:
        return existing[0]["LoadBalancerArn"], existing[0]["DNSName"]
    lb = elb.create_load_balancer(Name="bz-agent-alb", Subnets=subnets,
        SecurityGroups=[alb_sg], Scheme="internet-facing", Type="application",
        Tags=TAG)["LoadBalancers"][0]
    return lb["LoadBalancerArn"], lb["DNSName"]


def _safe_lbs():
    try:
        elb.describe_load_balancers()
        return True
    except Exception:
        return True


def ensure_target_group(vpc):
    existing = [t for t in elb.describe_target_groups()["TargetGroups"]
                if t["TargetGroupName"] == "bz-agent-tg"]
    if existing:
        return existing[0]["TargetGroupArn"]
    return elb.create_target_group(Name="bz-agent-tg", Protocol="HTTP", Port=8080,
        VpcId=vpc, HealthCheckProtocol="HTTP", HealthCheckPath="/health",
        HealthCheckIntervalSeconds=15, HealthyThresholdCount=2,
        UnhealthyThresholdCount=2, TargetType="instance")["TargetGroups"][0]["TargetGroupArn"]


def ensure_listener(alb_arn, tg_arn):
    for ls in elb.describe_listeners(LoadBalancerArn=alb_arn)["Listeners"]:
        if ls["Port"] == 80:
            return ls["ListenerArn"]
    return elb.create_listener(LoadBalancerArn=alb_arn, Protocol="HTTP", Port=80,
        DefaultActions=[{"Type": "forward", "TargetGroupArn": tg_arn}])["Listeners"][0]["ListenerArn"]


def al2023_ami():
    imgs = ec2.describe_images(Owners=["amazon"], Filters=[
        {"Name": "name", "Values": ["al2023-ami-2023.*-x86_64"]},
        {"Name": "state", "Values": ["available"]}])["Images"]
    imgs.sort(key=lambda i: i["CreationDate"], reverse=True)
    return imgs[0]["ImageId"]


def ensure_launch_template(instance_sg):
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
    ud = base64.b64encode(user_data.encode()).decode()
    try:
        return ec2.describe_launch_templates(
            LaunchTemplateNames=["bz-agent-lt"])["LaunchTemplates"][0]["LaunchTemplateId"]
    except ec2.exceptions.ClientError:
        return ec2.create_launch_template(LaunchTemplateName="bz-agent-lt",
            LaunchTemplateData={
                "ImageId": al2023_ami(), "InstanceType": "t3.small",
                "IamInstanceProfile": {"Name": PROFILE},
                "SecurityGroupIds": [instance_sg], "UserData": ud,
                "TagSpecifications": [{"ResourceType": "instance",
                    "Tags": TAG + [{"Key": "Name", "Value": "bz-agent-asg"}]}]},
            TagSpecifications=[{"ResourceType": "launch-template", "Tags": TAG}]
        )["LaunchTemplate"]["LaunchTemplateId"]


def ensure_asg(lt_id, subnets, tg_arn):
    names = [g["AutoScalingGroupName"] for g in
             asg.describe_auto_scaling_groups()["AutoScalingGroups"]]
    if "bz-agent-asg" in names:
        return
    asg.create_auto_scaling_group(AutoScalingGroupName="bz-agent-asg",
        LaunchTemplate={"LaunchTemplateId": lt_id, "Version": "$Latest"},
        MinSize=1, MaxSize=4, DesiredCapacity=2,
        VPCZoneIdentifier=",".join(subnets), TargetGroupARNs=[tg_arn],
        HealthCheckType="ELB", HealthCheckGracePeriod=180,
        Tags=[{"Key": "Project", "Value": "bz-agent", "PropagateAtLaunch": True}])


def main():
    vpc = find_vpc()
    sn1, az1 = find_first_subnet(vpc)
    rtb = find_rtb(vpc)
    sn2 = ensure_second_subnet(vpc, az1, rtb)
    instance_sg = find_instance_sg(vpc)
    alb_sg = ensure_alb_sg(vpc)
    alb_arn, dns = ensure_alb([sn1, sn2], alb_sg)
    tg_arn = ensure_target_group(vpc)
    ensure_listener(alb_arn, tg_arn)
    lt_id = ensure_launch_template(instance_sg)
    ensure_asg(lt_id, [sn1, sn2], tg_arn)
    print("ELASTIC_READY")
    print("ALB_DNS  =", dns)
    print("ENDPOINT = http://%s/plan-itinerary" % dns)
    print("(allow ~3-4 min for instances to boot + pass health checks)")


if __name__ == "__main__":
    main()
