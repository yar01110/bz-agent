# Load Test Results & Architecture Comparison

Two data classes below: **Measured** (real calls to the live deployment) and
**Modelled** (analytical estimates for loads too costly/throttled to run fully,
derived from the measured numbers + documented AWS limits).

## A. Measured (real)

### A1. Single-request latency — EC2 `t3.small`, warm, `/plan-itinerary`
6 sequential requests: 17.5, 17.4, 18.4, 16.4, 14.7, 17.3 s
- **avg ≈ 16.9 s, min 14.7 s, max 18.4 s** (each request = ~3 Bedrock calls + ODH fetches)
- Lambda via API Gateway: ~17.8 s cold, ~13–15 s warm (comparable; Bedrock dominates latency)

### A2. Infra concurrency — cost-free `/health`, EC2 `t3.small`
| Concurrency | Throughput | p50 | p95 | p99 | Errors |
|---|---|---|---|---|---|
| 50  | **252 req/s** | 76 ms  | 733 ms  | 1153 ms | 0.07% |
| 200 | **90 req/s**  | 1673 ms | 5879 ms | 6547 ms | 0.55% |

**Key finding:** going 50 → 200 concurrent, throughput *fell* (252 → 90 req/s)
and latency rose ~20×. The single small instance is already saturating at 200
concurrent connections even on a trivial endpoint.

## B. Modelled (estimated) — full `/plan-itinerary` workload

Assumptions: per-request ≈ 17 s; user issues a new request roughly every 20 s
(response + think-time) ⇒ demand ≈ users / 20 req/s. One `t3.small` serves the
async workload at ~40 in-flight requests ⇒ ceiling ≈ 40 / 17 ≈ **2.4 req/s**.

| Users | Demand | EC2 `t3.small` (1 instance) | Lambda (auto-scale) |
|---|---|---|---|
| 50   | ~2.5 req/s | At capacity; minor queueing; p95 rises | ~50 concurrent execs; fine; some cold starts on ramp |
| 200  | ~10 req/s  | **4× over capacity → queue blowup, timeouts, errors** | ~200 concurrent; fine if account limit ≥200; Bedrock RPM may begin throttling |
| 1000 | ~50 req/s  | **~20× over → fails; needs ~21 instances + load balancer** | ~1000 concurrent (at default account limit); **Bedrock per-minute quota becomes the binding bottleneck for both** |

## C. Reliability
| | EC2 (single instance) | Lambda |
|---|---|---|
| Redundancy | None — single point of failure | Multi-AZ by default |
| Instance/AZ failure | Full outage until manual restart | Transparent, handled by AWS |
| Burst absorption | Poor (fixed capacity) | Automatic per-request scaling |
| To match Lambda | Needs Auto Scaling Group + ALB across AZs | Built-in |

## D. Scalability
- **EC2:** vertical (bigger instance) or manual horizontal (ASG); capacity must
  be provisioned ahead of demand; slow to react.
- **Lambda:** automatic, near-instant, per-request horizontal scaling up to the
  account concurrency limit (default ~1000; a new account may need a quota
  increase). No idle capacity to manage.
- **Shared ceiling:** at ~1000 users the dominant limit is **Amazon Bedrock’s
  per-minute request/token quota**, identical for both architectures. Beyond a
  point, scaling compute does not help — you must raise the Bedrock quota.

## E. Resource usage
- **EC2 `t3.small`** (2 vCPU, 2 GB): workload is I/O-bound (waiting on Bedrock),
  so CPU stays low; the limit is connection/threadpool concurrency (saturated at
  ~200 conns in A2). Burstable CPU credits can also throttle sustained load.
- **Lambda**: 2048 MB per concurrent execution (≈1.2 vCPU each), isolated; at
  1000 concurrency that is ~2 TB aggregate transient memory, managed by AWS.

## F. Billing (estimated, per 1,000 itineraries)
| Component | EC2 path | Lambda path |
|---|---|---|
| Amazon Bedrock (Claude) | ~$40 (dominant, identical) | ~$40 (dominant, identical) |
| Compute | Fixed $15.6/mo per t3.small (cheap only if ~100% utilised 24/7; needs a fleet+ALB for ≥200 users) | ~$0.56 per 1,000 (2 GB × 17 s) + ~$0 idle |
| API Gateway / DynamoDB | n/a / pennies | ~$1/million requests / pennies |

**Billing conclusion:** the LLM (Bedrock) is ~95%+ of cost and is the same for
both — the compute choice is a rounding error on the bill. Lambda wins on
**variable/spiky/low-to-medium** load (zero idle cost, no capacity planning);
EC2 only competes if a single instance is kept near 100% utilised around the
clock, and it needs an Auto Scaling Group + load balancer to survive 200+ users.

## Overall recommendation
For an interactive, bursty planner, **Lambda + API Gateway** is the better
default: it scales automatically, has no single point of failure, and costs
nothing when idle. EC2 is justified only for steady, high, predictable load (or
agent runs exceeding Lambda’s 15-min limit), and then as an Auto Scaling fleet,
not one instance. At extreme load both converge on the **Bedrock quota** as the
real constraint.
