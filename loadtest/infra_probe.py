"""Cheap, real concurrency probe for the EC2 server's infra layer.

Hammers a cost-free endpoint (default /health — no Bedrock, no DynamoDB writes)
at a given concurrency for a fixed duration, and reports throughput, latency
percentiles, and error rate. This measures how the t3.small instance + uvicorn
handle many simultaneous connections, isolated from the Bedrock bottleneck.

    python infra_probe.py http://3.126.251.241:8080/health --concurrency 50 --seconds 15

Note: results also reflect this client's network round-trip to eu-central-1, so
treat them as a relative comparison, not an absolute server ceiling.
"""
from __future__ import annotations

import argparse
import asyncio
import time

import httpx


async def worker(client, url, stop_at, lats, errors):
    while time.monotonic() < stop_at:
        t0 = time.monotonic()
        try:
            r = await client.get(url, timeout=10)
            lats.append((time.monotonic() - t0) * 1000)
            if r.status_code != 200:
                errors[0] += 1
        except Exception:
            errors[0] += 1


def pct(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, int(len(s) * p / 100))]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--concurrency", type=int, default=50)
    ap.add_argument("--seconds", type=int, default=15)
    args = ap.parse_args()

    lats: list[float] = []
    errors = [0]
    limits = httpx.Limits(max_connections=args.concurrency + 20,
                          max_keepalive_connections=args.concurrency + 20)
    async with httpx.AsyncClient(limits=limits) as client:
        stop_at = time.monotonic() + args.seconds
        tasks = [asyncio.create_task(worker(client, args.url, stop_at, lats, errors))
                 for _ in range(args.concurrency)]
        await asyncio.gather(*tasks)

    total = len(lats) + errors[0]
    rps = len(lats) / args.seconds
    print(f"url            : {args.url}")
    print(f"concurrency    : {args.concurrency}")
    print(f"duration       : {args.seconds}s")
    print(f"completed      : {len(lats)}  (errors: {errors[0]})")
    print(f"throughput     : {rps:.0f} req/s")
    print(f"error rate     : {100 * errors[0] / total if total else 0:.2f}%")
    print(f"latency p50    : {pct(lats, 50):.0f} ms")
    print(f"latency p95    : {pct(lats, 95):.0f} ms")
    print(f"latency p99    : {pct(lats, 99):.0f} ms")


if __name__ == "__main__":
    asyncio.run(main())
