# BZ-Agent — Smart-City Mobility & Event Orchestrator

Cloud-native, multi-agent (Agentic RAG) orchestrator for Bolzano. Pulls live
data from the NOI Techpark **Open Data Hub** (tourism + mobility), reasons over
constraints, and generates an itinerary. Built to be deployed two ways for the
course comparison: **AWS Lambda** (serverless) and **EC2** (long-running server).

## Architecture

```
          ┌──────────────┐
 client → │ API Gateway  │ → Lambda handler  (Architecture A)
          └──────────────┘        │
                                   ▼
                       LangGraph pipeline
        Retriever ──► Reasoner ──► Generator
            │            │            │
            └─── ODH ────┘            │
       (sanitized data)              │
                                      ▼
                        DynamoDB single-table state
                        PK=USER#<id>  SK=SESSION#<id>

 client → EC2 / ECS (uvicorn FastAPI, api/server.py)  (Architecture B)
```

## Layout
| Folder | Purpose |
|---|---|
| `shared/` | config, LLM factory (Bedrock/Anthropic switch), DynamoDB state |
| `odh/` | Open Data Hub clients + **sanitization** (slim the raw JSON) |
| `agents/` | Retriever, Reasoner, Generator + LangGraph orchestration |
| `api/` | `lambda_handler.py` (Arch A) and `server.py` (Arch B) |
| `scripts/` | local DynamoDB table creation |

## LLM access — read this first
Your **Claude Pro subscription does not include API access.** Pick one:
- **Bedrock (recommended):** set `LLM_PROVIDER=bedrock`, enable "Anthropic Claude"
  in the Bedrock console → Model access. Auth is your AWS IAM role/creds.
- **Anthropic API:** create a key at `console.anthropic.com` (separate billing),
  set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...`.

## Quick start (local)
```bash
python -m venv .venv && . .venv/Scripts/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                                   # then edit it

# local DynamoDB (optional, else point at real AWS)
docker run -d -p 8000:8000 amazon/dynamodb-local
python scripts/create_table.py

python run_local.py "I want to visit a museum and get around by bike"
```

## Deploy — Architecture A (Lambda)
1. Package deps + code (container image via `public.ecr.aws/lambda/python` base).
2. Push image to ECR, create the Lambda from it, handler = `api.lambda_handler.handler`.
3. Attach an IAM role with DynamoDB + Bedrock permissions.
4. Front it with API Gateway `POST /plan-itinerary`.

## Deploy — Architecture B (EC2)
1. `docker build -t bz-agent .`
2. Run on EC2 (or push to ECR + ECS): `docker run -p 8080:8080 --env-file .env bz-agent`
3. Instance profile / role provides DynamoDB + Bedrock access.

## Status / next steps
- [x] ODH integration + sanitization
- [x] Retriever / Reasoner / Generator + LangGraph
- [x] DynamoDB single-table state
- [x] Lambda + EC2 entrypoints
- [ ] VPC, IAM roles, Secrets Manager (infra phase — later)
- [ ] Weather constraint + GTFS live schedules
- [ ] WebSocket streaming for progress updates
- [ ] Cost comparison Lambda vs EC2 (course deliverable)
```
