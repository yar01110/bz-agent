# BZ-Agent — Setup Roadmap (how everything was built)

A chronological, reproducible guide to how the whole system was set up, from an
empty AWS account to two live, load-tested deployments. Each phase lists what was
done, the key commands/scripts, and the decisions or gotchas encountered.

---

## Phase 0 — Accounts, access & local tools

**AWS account (Free plan, ~$120 credits).**
1. Enabled **Amazon Bedrock model access** for *Anthropic Claude Sonnet 4.5* in
   the Bedrock console (region **eu-central-1 / Frankfurt**). One-time account
   setting — not code.
2. Created an IAM user **`bz-agent-dev`** (programmatic access only) and an
   access key.
3. Saved credentials locally so `boto3` can read them:
   ```
   ~/.aws/credentials  →  [default] aws_access_key_id / aws_secret_access_key / region=eu-central-1
   ```

> 💡 Key fact: a **Claude Pro subscription does NOT include API access.** We use
> **Bedrock** (Claude via AWS/IAM) instead — one bill, no separate API key.

**Local tools:** Python 3.x, Docker Desktop, Node.js (for the report), Git.

**IAM permissions were added reactively, as each phase needed them** (good
least-privilege practice):
| Phase | Policy attached to `bz-agent-dev` |
|---|---|
| Run the agent | `AmazonBedrockFullAccess`, `AmazonDynamoDBFullAccess` |
| Deploy | `AmazonEC2ContainerRegistryFullAccess`, `AWSLambda_FullAccess`, `AmazonEC2FullAccess`, `IAMFullAccess` |
| API Gateway | `AmazonAPIGatewayAdministrator` |

---

## Phase 1 — Project scaffolding

Monorepo with a microservices boundary:
```
bz-agent/
  shared/   config, LLM factory (Bedrock⇄Anthropic), DynamoDB, JSON utils
  odh/      Open Data Hub clients + sanitization + weather
  agents/   Retriever, Reasoner, Generator, LangGraph orchestration
  api/      Lambda handler, FastAPI server, browser UI
  scripts/  setup + deploy automation
```
- `shared/llm.py` makes the LLM provider a one-line switch (`LLM_PROVIDER=bedrock`).
- `requirements.txt`: langgraph, langchain-core, langchain-aws, boto3, httpx, pydantic.

---

## Phase 2 — Open Data Hub integration + sanitization

- Built clients for **Content** (POIs, events), **Mobility** (parking, bike
  stations) and **Weather** (Bolzano district forecast).
- **Sanitization layer (`odh/sanitize.py`)** strips raw ODH JSON down to a few
  flat fields (name, coords, time, value) — the key defense against context
  overflow, cost blow-up, and hallucination.
- **Gotchas discovered by probing the live API:**
  - POI names live in `Shortname` / `Detail.<lang>.Title`; coords in `GpsPoints.position`.
  - Museum filtering needs `tagfilter`, not `categorycodes`.
  - The old bike-availability dataset is **dead** (2016 data) → switched to live
    `ParkingStation` + `BikesharingStation` (which have coordinates).

---

## Phase 3 — Agentic core

- **Retriever → Reasoner → Generator**, wired as a **LangGraph** state machine
  (`agents/graph.py`). State flows one way; each node writes its slice to the
  DynamoDB scratchpad.
- **DynamoDB single-table design** (`shared/dynamo.py`):
  `PK = USER#<id>`, `SK = SESSION#<id>`, on-demand billing.

---

## Phase 4 — Local verification (against real AWS)

```bash
python scripts/create_table.py            # create bz-agent-state table
python run_local.py "I want to visit a museum and find parking"
```
**Bugs found and fixed during real runs** (each a good lesson for the report):
| Symptom | Cause | Fix |
|---|---|---|
| ReadTimeout | ODH endpoint slow | 30s timeout + per-fetch resilience |
| `Float types not supported` | DynamoDB rejects floats | convert floats → `Decimal` |
| `document path invalid` | scratchpad map didn't exist | create skeleton + defensive init |
| Generator **hallucinated** | Claude wrapped JSON in ```` ```json ```` fences → empty draft | robust `extract_json()` |

After these, the pipeline produced **grounded** itineraries (real parking + museums).

---

## Phase 5 — Containerize & deploy (two architectures)

```bash
python scripts/deploy_setup.py     # ECR repo + IAM roles (lambda, ec2)
# build TWO images from one codebase, push to ECR:
#   Dockerfile         → :server  (uvicorn/FastAPI, for EC2)
#   Dockerfile.lambda  → :lambda  (AWS Lambda base image)
python scripts/deploy_lambda.py    # Architecture A: Lambda from image
python scripts/deploy_apigw.py     # public POST /plan-itinerary via API Gateway
python scripts/deploy_ec2.py       # Architecture B: EC2 pulls image + runs it
```
**Gotchas:**
- Lambda rejected the image: Docker Desktop builds **OCI** manifests → rebuilt
  with `buildx --provenance=false ... oci-mediatypes=false` (Docker v2 manifest).
- `ssm:GetParameter` denied for the AMI lookup → switched to `describe_images`.
- Lambda **Function URL returned 403** (newer accounts block public Function URLs)
  → used **API Gateway** instead (also the proper roadmap front door).

---

## Phase 6 — Custom VPC (network isolation)

```bash
python scripts/deploy_vpc.py
```
Creates and wires, then migrates EC2 into it:
- **VPC** `10.0.0.0/16` (DNS enabled)
- **Public subnet** `10.0.1.0/24` (auto-assign public IP)
- **Internet Gateway** + route `0.0.0.0/0 → IGW`
- **DynamoDB gateway endpoint** (free; keeps state traffic on AWS's private network)
- **Security group**: inbound TCP **8080** only
- Old default-VPC instance terminated; new instance launched inside the VPC.

---

## Phase 7 — Feature enhancements

- **Weather-aware reasoning**: rain/storm → indoor, clear → outdoor (verified).
- **Geo-filtering**: mobility data bounded to a Bolzano box (drops outliers).
- **SSE progress streaming** (`/plan-itinerary/stream`) + a **browser UI** showing
  a live checklist (Retriever → Reasoner → Generator).
- Redeployed via rebuild → push → relaunch EC2-in-VPC + update Lambda.

---

## Phase 8 — Load testing & comparison

```bash
# k6 scenarios (load50 / load200 / stress1000)
k6 run -e BASE_URL=... -e SCENARIO=load200 loadtest/k6/loadtest.js
# cheap, real infra sweep on the cost-free /health endpoint
python loadtest/infra_probe.py http://<ec2-ip>:8080/health --concurrency 200 --seconds 12
```
- Measured per-request latency (~16.9 s) and an EC2 **saturation sweep** (25→400):
  peak ~25 conc (322 req/s), **spike at 150–200**, broken by 300+ (p95 ≈ 15 s).
- Modelled 50/200/1000 users; analysed reliability, scalability, resource usage,
  and billing. **Key conclusion:** Bedrock (the LLM) is ~95% of cost and the same
  for both; at ~1000 users the **Bedrock quota** is the shared bottleneck.

---

## Phase 9 — Deliverables

- **`report/BZ-Agent_Report.docx`** — full project report (architecture diagram,
  comparison, load-test chart, pricing, security, course-objective map).
- **`infra/`** — **Terraform** codifying the whole stack (Infrastructure as Code).
- **`loadtest/`** — k6 scripts, infra probe, methodology, results.
- All committed to Git; `.env` and secrets excluded via `.gitignore`.

---

## One-command mental model (build order)
```
accounts/keys → scaffold → ODH+sanitize → agents+LangGraph → local verify
   → ECR+IAM → 2 images → Lambda+API Gateway → EC2 → custom VPC
   → features (weather/stream/UI) → load test → report + Terraform
```

## Live endpoints
- EC2 (Arch B, in VPC): `http://<ec2-public-ip>:8080`
- Lambda (Arch A): `https://<api-id>.execute-api.eu-central-1.amazonaws.com/plan-itinerary`
- Region: **eu-central-1** · Model: **Claude Sonnet 4.5** via Bedrock · State: **DynamoDB `bz-agent-state`**
