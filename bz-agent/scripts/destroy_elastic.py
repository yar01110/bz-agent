"""Tear down the elastic stack (ASG, ALB, target group, launch template, ALB SG,
second subnet) created by deploy_elastic.py — to stop incurring cost after the
experiments. Leaves the original single-instance VPC setup untouched.
"""
from __future__ import annotations

import time

import boto3

REGION = "eu-central-1"
ec2 = boto3.client("ec2", region_name=REGION)
elb = boto3.client("elbv2", region_name=REGION)
asg = boto3.client("autoscaling", region_name=REGION)


def _try(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        print("  skip:", type(e).__name__, str(e)[:90])


def main():
    # 1. ASG (force delete terminates instances)
    _try(asg.delete_auto_scaling_group, AutoScalingGroupName="bz-agent-asg", ForceDelete=True)
    print("deleting ASG (terminating instances)…")
    for _ in range(40):
        groups = asg.describe_auto_scaling_groups(
            AutoScalingGroupNames=["bz-agent-asg"])["AutoScalingGroups"]
        if not groups:
            break
        time.sleep(6)

    # 2. ALB + listeners
    lbs = [l for l in elb.describe_load_balancers()["LoadBalancers"]
           if l["LoadBalancerName"] == "bz-agent-alb"]
    if lbs:
        _try(elb.delete_load_balancer, LoadBalancerArn=lbs[0]["LoadBalancerArn"])
        print("deleting ALB…")
        time.sleep(20)

    # 3. Target group
    tgs = [t for t in elb.describe_target_groups()["TargetGroups"]
           if t["TargetGroupName"] == "bz-agent-tg"]
    if tgs:
        _try(elb.delete_target_group, TargetGroupArn=tgs[0]["TargetGroupArn"])

    # 4. Launch template
    _try(ec2.delete_launch_template, LaunchTemplateName="bz-agent-lt")

    # 5. ALB security group
    sgs = ec2.describe_security_groups(Filters=[
        {"Name": "tag:Name", "Values": ["bz-agent-alb-sg"]}])["SecurityGroups"]
    if sgs:
        _try(ec2.delete_security_group, GroupId=sgs[0]["GroupId"])

    # 6. Second subnet
    sns = ec2.describe_subnets(Filters=[
        {"Name": "tag:Name", "Values": ["bz-agent-public-subnet-b"]}])["Subnets"]
    if sns:
        _try(ec2.delete_subnet, SubnetId=sns[0]["SubnetId"])

    print("ELASTIC_TORN_DOWN (single-instance VPC setup left intact)")


if __name__ == "__main__":
    main()
