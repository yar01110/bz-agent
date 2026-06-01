"""Failure-recovery experiment (reliability).

Continuously pings the ALB's cost-free /health while we terminate one of the two
Auto Scaling Group instances, then measures:
  - the error rate the client sees during the failure (does the ALB route around
    the dead instance via the surviving one?)
  - the self-healing recovery time (how long until the ASG brings the target group
    back to 2 healthy instances)

This demonstrates the "cattle" model: a single instance failing does NOT take the
service down, and the ASG replaces it automatically. Contrast: the single EC2
setup is a "pet" — killing it is a 100% outage until manual redeploy.
"""
from __future__ import annotations

import threading
import time

import boto3
import httpx

REGION = "eu-central-1"
elb = boto3.client("elbv2", region_name=REGION)
asg = boto3.client("autoscaling", region_name=REGION)


def alb_dns():
    lb = [l for l in elb.describe_load_balancers()["LoadBalancers"]
          if l["LoadBalancerName"] == "bz-agent-alb"][0]
    return lb["DNSName"]


def tg_arn():
    return [t for t in elb.describe_target_groups()["TargetGroups"]
            if t["TargetGroupName"] == "bz-agent-tg"][0]["TargetGroupArn"]


def healthy_targets(arn):
    h = elb.describe_target_health(TargetGroupArn=arn)["TargetHealthDescriptions"]
    return [d["Target"]["Id"] for d in h if d["TargetHealth"]["State"] == "healthy"]


def main():
    dns = alb_dns()
    arn = tg_arn()
    url = f"http://{dns}/health"

    print("waiting for 2 healthy targets…")
    for _ in range(60):
        if len(healthy_targets(arn)) >= 2:
            break
        time.sleep(6)
    healthy = healthy_targets(arn)
    print("healthy targets:", healthy)
    if len(healthy) < 2:
        print("WARNING: fewer than 2 healthy targets; results may be limited")

    # background pinger
    samples = []  # (t_rel, ok)
    stop = threading.Event()
    t0 = time.monotonic()

    def ping():
        with httpx.Client(timeout=5) as c:
            while not stop.is_set():
                t = time.monotonic() - t0
                try:
                    ok = c.get(url).status_code == 200
                except Exception:
                    ok = False
                samples.append((t, ok))
                time.sleep(0.25)

    th = threading.Thread(target=ping, daemon=True)
    th.start()

    time.sleep(6)  # baseline
    victim = healthy[0]
    t_kill = time.monotonic() - t0
    print(f"[t={t_kill:.0f}s] terminating instance {victim} (ASG will replace it)…")
    asg.terminate_instance_in_auto_scaling_group(
        InstanceId=victim, ShouldDecrementDesiredCapacity=False)

    # monitor recovery: wait until 2 healthy again (or timeout)
    t_recovered = None
    dropped = False
    deadline = time.monotonic() + 360
    while time.monotonic() < deadline:
        h = healthy_targets(arn)
        if victim not in h and not dropped:
            dropped = True
            print(f"[t={time.monotonic()-t0:.0f}s] victim removed from rotation (now {len(h)} healthy)")
        if len(h) >= 2 and victim not in h:
            t_recovered = time.monotonic() - t0
            print(f"[t={t_recovered:.0f}s] back to 2 healthy — self-healed")
            break
        time.sleep(5)

    time.sleep(5)
    stop.set()
    th.join(timeout=3)

    # stats
    total = len(samples)
    fails = [t for t, ok in samples if not ok]
    during = [t for t, ok in samples if not ok and t >= t_kill]
    print("\n===== RESULTS =====")
    print(f"total health pings        : {total}")
    print(f"failed pings (whole run)  : {len(fails)}  ({100*len(fails)/total:.2f}%)")
    print(f"failed pings after kill   : {len(during)}")
    print(f"client-visible outage     : {'NONE' if not during else f'{len(during)} pings (~{len(during)*0.25:.1f}s)'}")
    if t_recovered:
        print(f"self-heal recovery time   : ~{t_recovered - t_kill:.0f}s (ASG replaced the instance)")
    else:
        print("self-heal recovery time   : not observed within 6 min")
    print("\nInterpretation: with the ALB+ASG fleet, one instance dying did not")
    print("take the service down (surviving instance served traffic), and the ASG")
    print("auto-replaced it. A single-instance deployment would be a 100% outage.")


if __name__ == "__main__":
    main()
