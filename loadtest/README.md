# BZ-Agent — Load Testing & Architecture Comparison

This folder contains the load-testing methodology used to compare the two
deployment architectures under increasing concurrency (≈50, 200, and 1000
simulated users) and to assess **reliability, scalability, billing, and
resource usage**.

## Test targets
| Architecture | Endpoint |
|---|---|
| A — Lambda + API Gateway (serverless) | `https://<api-id>.execute-api.eu-central-1.amazonaws.com/plan-itinerary` |
| B — EC2 `t3.small` (server, in custom VPC) | `http://<ec2-ip>:8080/plan-itinerary` |

## Tools
- **k6** (`k6/loadtest.js`) — the primary load generator, with `load50`,
  `load200`, and `stress1000` scenarios (ramping virtual users). This is the
  aggressive, k6-style test the 1000-user comparison refers to.
- **infra_probe.py** — a lightweight async probe against the cost-free `/health`
  endpoint, used to measure raw infra concurrency **without** incurring Bedrock
  cost.

## Why the 1000-user run is modelled, not blindly executed
Every `/plan-itinerary` iteration triggers ~3 Amazon Bedrock (Claude) calls.
A sustained 1000-VU run therefore means **tens of thousands of Bedrock calls**,
which (a) costs real money and (b) hits Bedrock’s per-minute request/token quota
— which becomes the dominant bottleneck for *both* architectures. So we:
1. Measure **real** single-request latency (calibration).
2. Measure **real** infra concurrency on `/health` at 50 / 200.
3. **Model** the 50 / 200 / 1000-user full-workload behaviour from those real
   numbers plus documented AWS service limits.

Run the heavy k6 scenarios only against a sandbox account or a mock/echo build
where Bedrock is stubbed out, to avoid cost and quota throttling.

## How to run
```bash
# k6 full-workload scenarios (mind the Bedrock cost!)
k6 run -e BASE_URL=http://<ec2-ip>:8080      -e SCENARIO=load50    k6/loadtest.js
k6 run -e BASE_URL=https://<api-id>...        -e SCENARIO=load200   k6/loadtest.js
k6 run -e BASE_URL=http://<ec2-ip>:8080      -e SCENARIO=stress1000 k6/loadtest.js

# cheap infra concurrency probe (no Bedrock)
python infra_probe.py http://<ec2-ip>:8080/health --concurrency 50  --seconds 15
python infra_probe.py http://<ec2-ip>:8080/health --concurrency 200 --seconds 15
```

See `../report/BZ-Agent_Report.docx` (Load Testing section) for the full
results, model, and the reliability / scalability / billing / resource analysis.
