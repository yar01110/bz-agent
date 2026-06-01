# BZ-Agent — Smart-City Mobility & Event Orchestrator

A cloud-native, **multi-agent (Agentic RAG)** system for Bolzano that turns a
natural-language request (e.g. *"I want to visit a museum and find parking
nearby"*) into a validated, grounded itinerary — built on AWS and deployed two
ways (**AWS Lambda** and **Amazon EC2**) for a performance/cost/scalability
comparison.

**Authors:** Nidhal Karchoud · Abdellah Derf
**Repository:** https://github.com/yar01110/bz-agent
**Course:** Cloud Computing and Distributed Systems

---

## What it does
Three AI agents, orchestrated as a LangGraph state machine, collaborate to plan:
**Retriever → Reasoner → Generator**. Live data comes from the NOI Techpark
**Open Data Hub** (tourism, mobility, weather); reasoning runs on **Amazon
Bedrock** (Claude Sonnet 4.5); session state lives in **DynamoDB**.

```
client → API Gateway / EC2 → LangGraph (Retriever→Reasoner→Generator)
                                     │
                ┌────────────────────┼────────────────────┐
             ODH APIs            Amazon Bedrock         DynamoDB
          (live data)         (reasoning engine)     (session state)
```

## Two deployment architectures (the research question)
> *How do a serverless (Lambda + API Gateway) and a server-based (EC2)
> deployment of the same application compare in performance, scalability,
> reliability, and cost — and where is the bottleneck?*

| | AWS Lambda (serverless) | Amazon EC2 (server) |
|---|---|---|
| Scaling | Automatic, per request | Manual / Auto Scaling Group |
| Cost when idle | $0 | Billed hourly |
| Cold start | ~5–18 s | None |
| Best for | spiky / low-medium load | steady, high load |

## Key experimental results
- **Saturation:** a single `t3.small` peaks at ~25 concurrent connections and breaks down at ~150–200.
- **Elasticity:** an ALB + Auto Scaling Group (2 instances) gave **+70% throughput and ½ the latency at 300 concurrency** (0% errors).
- **Failure recovery:** killing one fleet instance caused **0 client-visible outage**; the ASG **self-healed in ~117 s**.
- **Cost:** the LLM (Bedrock) is **~95% of total cost** and identical for both — the compute choice is a rounding error.

## Repository structure
| Path | Contents |
|---|---|
| `bz-agent/` | Application code (agents, ODH clients, API) + deploy scripts |
| `infra/` | **Terraform** — the whole stack as Infrastructure as Code |
| `loadtest/` | k6 scripts, infra probe, experiments, `RESULTS.md` |
| `report/` | `BZ-Agent_Report.docx`, `Setup_Roadmap.docx`, diagrams & charts |
| `SETUP_ROADMAP.md` | How the system was built, end to end |

## Cloud services used
AWS Bedrock · Lambda · API Gateway · EC2 · Auto Scaling + ELB · DynamoDB ·
VPC (custom subnet, IGW, route table, gateway endpoint, security group) · ECR · IAM.

## Running it
See [`bz-agent/README.md`](bz-agent/README.md) for local setup and
[`SETUP_ROADMAP.md`](SETUP_ROADMAP.md) for the full build/deploy process.
The full report (architecture, experiments, analysis) is in
[`report/BZ-Agent_Report.docx`](report/BZ-Agent_Report.docx).

---
*Built with LangChain / LangGraph on AWS (eu-central-1).*
