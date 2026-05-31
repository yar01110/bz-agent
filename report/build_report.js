const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, PageNumber, PageBreak, TableOfContents, VerticalAlign,
} = require("docx");

const CW = 9360; // content width (US Letter, 1" margins)
const BLUE = "2563EB", NAVY = "0F172A", SLATE = "475569", HEADERFILL = "D5E8F0";

// ---------- helpers ----------
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const P = (t, opts = {}) => new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: t, ...opts })] });
const bullet = (t, bold) => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 60 },
  children: typeof t === "string" ? [new TextRun(t)] : t });
const runs = (...r) => new Paragraph({ spacing: { after: 120 }, children: r });

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border };

function cell(text, w, { head = false, bold = false } = {}) {
  const children = (Array.isArray(text) ? text : [text]).map((line, i) =>
    new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: line, bold: bold || head, color: head ? NAVY : undefined, size: head ? 20 : 20 })] }));
  return new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    shading: head ? { fill: HEADERFILL, type: ShadingType.CLEAR } : undefined,
    verticalAlign: VerticalAlign.CENTER, children,
  });
}
function table(widths, rows) {
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, ri) => new TableRow({
      tableHeader: ri === 0,
      children: r.map((c, ci) => cell(c, widths[ci], { head: ri === 0 })) })) });
}

// ---------- document ----------
const doc = new Document({
  creator: "BZ-Agent",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, color: NAVY }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, color: BLUE }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 600, hanging: 280 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [ new Paragraph({ alignment: AlignmentType.CENTER,
      children: [ new TextRun({ text: "BZ-Agent · Cloud Computing Project · ", size: 16, color: SLATE }),
        new TextRun({ text: "Page ", size: 16, color: SLATE }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: SLATE }) ] }) ] }) },
    children: [
      // ---- Title page ----
      new Paragraph({ spacing: { before: 1800, after: 0 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "BZ-Agent", bold: true, size: 72, color: NAVY })] }),
      new Paragraph({ spacing: { before: 120, after: 0 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Smart-City Mobility & Event Orchestrator", size: 32, color: BLUE })] }),
      new Paragraph({ spacing: { before: 80, after: 0 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "A Cloud-Native, Multi-Agent AI System for Bolzano", size: 24, color: SLATE, italics: true })] }),
      new Paragraph({ spacing: { before: 600 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Project Report & Technical Roadmap", size: 26, bold: true })] }),
      new Paragraph({ spacing: { before: 1400 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Architecture: AWS (eu-central-1) · Amazon Bedrock · Lambda · EC2 · DynamoDB · API Gateway", size: 18, color: SLATE })] }),
      new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Framework: LangChain / LangGraph · Data: NOI Techpark Open Data Hub", size: 18, color: SLATE })] }),
      new Paragraph({ children: [new PageBreak()] }),

      // ---- TOC ----
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Table of Contents")] }),
      new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
      new Paragraph({ children: [new PageBreak()] }),

      // ---- 1. Overview ----
      H1("1. Project Overview"),
      P("BZ-Agent is a cloud-native, multi-agent AI system that acts as an autonomous smart-city orchestrator for Bolzano. It uses an Agentic RAG (Retrieval-Augmented Generation) architecture to fetch and process real-time mobility, weather, and tourism data from the local Open Data Hub (ODH) and turn a natural-language request (for example, “I want to visit a museum and find parking nearby”) into a validated, grounded itinerary."),
      P("The system follows a microservices design in which distinct agents handle specific tasks — data retrieval, constraint reasoning, and itinerary generation — orchestrated as a state graph. It is deployed on Amazon Web Services in two different ways, AWS Lambda (serverless) and Amazon EC2 (server), so the two compute models can be directly compared. The reasoning engine is Anthropic Claude, accessed through Amazon Bedrock; session state lives in Amazon DynamoDB; and Amazon API Gateway provides the public front door."),
      H2("1.1 Objectives"),
      bullet("Demonstrate a complex, multi-agent backend workflow orchestrated and scaled on AWS."),
      bullet("Ground every recommendation in live open data to avoid LLM hallucination."),
      bullet("Compare two distributed compute architectures (serverless vs. server) for the same workload."),
      bullet("Apply cloud-native principles: managed services, least-privilege IAM, pay-per-use, containerisation."),

      // ---- 2. Architecture ----
      H1("2. System Architecture"),
      P("The diagram below shows the end-to-end architecture. A client request enters through one of two compute paths; both run the identical container image and the same LangGraph pipeline. The pipeline calls three backend services: the Open Data Hub for live data, Amazon Bedrock for reasoning, and DynamoDB for state."),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 }, children: [
        new ImageRun({ type: "png", data: fs.readFileSync(__dirname + "/architecture.png"),
          transformation: { width: 600, height: 446 },
          altText: { title: "Architecture", description: "BZ-Agent AWS architecture", name: "arch" } }) ] }),
      P("Data flow: live data in → constraint reasoning → grounded itinerary out. The compute layer (Lambda or EC2) only orchestrates; the intelligence is in Bedrock and the memory is in DynamoDB.", { italics: true, color: SLATE }),

      // ---- 3. Cloud Components ----
      H1("3. Cloud Components"),
      P("Each AWS service was chosen to satisfy a specific role, applying the principle of using managed services rather than self-managed infrastructure."),
      table([2400, 6960], [
        ["Service", "Role in BZ-Agent"],
        ["Amazon Bedrock", "Hosts the Claude Sonnet 4.5 model (reasoning engine). Accessed via IAM — no separate API key, billed through AWS."],
        ["AWS Lambda", "Serverless compute for Architecture A; runs the agent pipeline on demand behind API Gateway."],
        ["Amazon EC2", "Server compute for Architecture B; a t3.small instance running the same container 24/7."],
        ["Amazon DynamoDB", "Single-table NoSQL store for session state and the agent scratchpad (PK=USER#, SK=SESSION#)."],
        ["Amazon API Gateway", "Public HTTP front door (POST /plan-itinerary) that proxies to the Lambda."],
        ["Amazon ECR", "Container registry holding the two image tags (server, lambda) pulled by EC2 and Lambda."],
        ["AWS IAM", "Least-privilege roles for the Lambda and EC2 instance, granting only Bedrock + DynamoDB access."],
      ]),

      // ---- 4. Agentic pipeline ----
      H1("4. The Agentic RAG Pipeline"),
      P("The “brain” is a three-node LangGraph state machine. State flows strictly in one direction, and each node writes its output to the DynamoDB agent scratchpad, giving full traceability of how a plan was built."),
      H2("4.1 Retriever"),
      P("Maps the natural-language request to data needs, then calls the relevant ODH tools (points of interest, events, parking, bike stations) and always fetches today’s weather. A sanitisation layer strips the heavy raw JSON down to a few flat fields (name, coordinates, time, value) so the model context never overflows — the single most important safeguard against cost blow-up and hallucination."),
      H2("4.2 Reasoner"),
      P("Applies hard constraints to the sanitised data: geographic proximity, a ≥15-minute transit buffer, parking/bike availability, and weather (rain or thunderstorm → prefer indoor stops; warm and clear → outdoor routes are fine). It outputs a validated, ordered itinerary draft as structured JSON."),
      H2("4.3 Generator"),
      P("Renders the validated draft into a friendly, human-readable itinerary. It invents nothing — it only formats facts the Reasoner already validated — which keeps the final answer grounded in real data."),

      // ---- 5. Comparison ----
      H1("5. Architecture Comparison: Lambda vs. EC2"),
      P("The same code was deployed two ways. This is the core of the “when to use which service” and “compare distributed architectures” analysis. Measurements are from live calls in eu-central-1."),
      table([3120, 3120, 3120], [
        ["Dimension", "AWS Lambda (Arch A)", "Amazon EC2 (Arch B)"],
        ["Execution model", "Serverless, per-request", "Always-on server"],
        ["Latency (warm)", "~13–15 s", "~13 s"],
        ["Cold start", "~5–18 s first call", "None"],
        ["Cost when idle", "$0", "Billed hourly (always)"],
        ["Cost per request", "Pennies per invocation", "Included in hourly rate"],
        ["Max execution time", "15 minutes (hard limit)", "No limit"],
        ["Scaling", "Automatic, per-request", "Manual / Auto Scaling group"],
        ["Front door", "API Gateway", "Port 8080 (direct)"],
        ["Best for", "Spiky / occasional traffic", "Steady traffic, long jobs"],
      ]),
      P("Conclusion: for an interactive planner with bursty, unpredictable usage, Lambda + API Gateway is the cost-efficient default (zero idle cost). EC2 becomes preferable only if traffic is steady enough to keep the instance busy, or if an agent run could exceed Lambda’s 15-minute ceiling.", { bold: true }),

      // ---- 6. Pricing ----
      H1("6. Cloud Pricing Analysis"),
      P("AWS follows a pay-per-use philosophy: you pay for what you consume, with no upfront cost. BZ-Agent illustrates three different billing models in one system."),
      table([2600, 6760], [
        ["Service", "Pricing model & approximate cost"],
        ["AWS Lambda", "Per-request + per-GB-second. At 2048 MB and ~15 s/run, each itinerary costs well under one US cent; $0 when idle."],
        ["Amazon EC2 (t3.small)", "Per-hour while running (~$0.021/hr in eu-central-1, ~$15/month if left on 24/7) regardless of traffic."],
        ["Amazon DynamoDB", "On-demand (PAY_PER_REQUEST): pay per read/write. At this volume, effectively free."],
        ["Amazon Bedrock", "Per input/output token of Claude. The sanitisation layer keeps prompts small, so each run is a few cents at most."],
        ["API Gateway", "Per million requests; negligible at demo volume."],
      ]),
      P("Cost-control measures applied: DynamoDB on-demand (no idle capacity charge), small prompts via sanitisation, and a recommended AWS Budgets alarm. Development to date has consumed only a few cents of the account’s credit."),

      // ---- 7. Security ----
      H1("7. Security & Compliance"),
      P("Security measures implemented, illustrating defence-in-depth and least privilege:"),
      bullet("Least-privilege IAM: a dedicated bz-agent-dev user and separate execution roles for Lambda and EC2 grant only the permissions needed (Bedrock + DynamoDB), rather than AdministratorAccess."),
      bullet("No long-lived model API key: Bedrock is reached through IAM role credentials, so there is no Anthropic key to leak; the LLM bill stays inside AWS."),
      bullet("Secrets kept out of source control: a .gitignore excludes the .env file; only .env.example (no secrets) is committed."),
      bullet("Encryption at rest: DynamoDB encrypts table data by default; ECR image scanning is enabled on push."),
      bullet("Key rotation awareness: an access key accidentally exposed during setup was identified as a rotation risk (documented as a lesson in secure credential handling)."),
      H2("7.1 Network isolation — custom VPC"),
      P("The EC2 workload runs inside a purpose-built Virtual Private Cloud rather than the default VPC, demonstrating network-level control:"),
      bullet("VPC 10.0.0.0/16 with DNS support and hostnames enabled."),
      bullet("A public subnet (10.0.1.0/24) with an Internet Gateway and a 0.0.0.0/0 route, so the instance can reach the Open Data Hub and Bedrock."),
      bullet("A DynamoDB gateway VPC endpoint attached to the route table, so state traffic to DynamoDB stays on the AWS private network instead of the public internet (and incurs no extra cost)."),
      bullet("A security group that allows only inbound TCP 8080, acting as a stateful virtual firewall."),
      H2("7.2 Hardening still recommended"),
      bullet("Move the Lambda into private subnets with interface endpoints; serve EC2 over HTTPS behind a load balancer."),
      bullet("Enable MFA on the root account; store any future secret in AWS Secrets Manager."),

      // ---- 8. Deployment ----
      H1("8. Deployment Process"),
      P("Deployment is scripted and reproducible (a step toward Infrastructure as Code):"),
      bullet("Provision: ECR repository + IAM roles created via boto3 (deploy_setup.py); DynamoDB table via create_table.py."),
      bullet("Build: two Docker images from one codebase — a Lambda base image and a uvicorn/FastAPI server image — pushed to Amazon ECR."),
      bullet("Deploy A: Lambda created from the image (deploy_lambda.py), fronted by an HTTP API Gateway (deploy_apigw.py)."),
      bullet("Deploy B: an EC2 instance launched with an instance profile and user-data that pulls the image from ECR and runs it (deploy_ec2.py)."),

      // ---- 9. Verification ----
      H1("9. Verification & Results"),
      P("Both architectures were tested end-to-end against live AWS and live ODH data. Each returned HTTP 200 with a grounded itinerary referencing real Bolzano parking (e.g. “P07 - Mareccio, 144 spaces”) and real museums (e.g. Museum Eccel Kreuzer, Domschatzkammer Bozen)."),
      P("The weather feature was confirmed to influence reasoning: on a clear 32 °C day the Reasoner produced an outdoor plan (city squares, the Etsch river bike path, a rooftop terrace) and explicitly cited the good weather."),
      table([3120, 6240], [
        ["Endpoint", "Status"],
        ["EC2 (Architecture B, in custom VPC)", "Live, browser UI + POST API, HTTP 200, ~13 s warm"],
        ["Lambda via API Gateway (Architecture A)", "Live public POST endpoint, HTTP 200"],
        ["SSE progress streaming", "Live: emits 3 progress events, then the itinerary"],
        ["DynamoDB state", "Scratchpad written per node (retriever/reasoner/generator)"],
        ["Bedrock Claude Sonnet 4.5", "Reasoning + generation verified live"],
      ]),
      P("A Server-Sent Events endpoint (POST /plan-itinerary/stream) streams progress to the browser, so the UI shows a live checklist — “Fetched live data”, “Reasoned over constraints”, “Wrote your itinerary” — as each agent finishes. The whole stack is also codified as Terraform (infra/) for reproducible, one-command provisioning."),

      // ---- 10. Course objectives ----
      H1("10. Mapping to Course Objectives"),
      table([4200, 1400, 3760], [
        ["Course objective", "Status", "Where addressed"],
        ["Define the main cloud components", "Done", "Section 3"],
        ["Explain cloud architectural principles", "Done", "Sections 2, 4"],
        ["Explain the cloud pricing philosophy", "Done", "Section 6"],
        ["Describe security & compliance measures", "Done", "Section 7"],
        ["Create and manage a VPC", "Done", "Section 7.1"],
        ["Principles of cloud-native applications", "Done", "Sections 2, 8"],
        ["When to use EC2 vs Lambda vs Beanstalk", "Done", "Section 5"],
        ["Compare distributed systems architectures", "Done", "Section 5"],
      ]),

      // ---- 11. Future work ----
      H1("11. Future Work"),
      bullet("Live SASA bus / GTFS schedules so the Reasoner can suggest exact departures. (Not in the ODH public flat API; would require integrating SASA’s separate GTFS feed.)"),
      bullet("Place the Lambda inside private subnets. Designed but deferred on cost grounds: reaching the public Open Data Hub from a private subnet needs a NAT Gateway (~$38/month) plus a Bedrock interface endpoint (~$8/month); not justified for a demo. Documented as a deliberate cost-aware decision."),
      bullet("Multi-turn memory so follow-up questions reuse prior session context (history is already persisted in DynamoDB)."),

      // ---- Appendix ----
      H1("Appendix A. Project Structure & Endpoints"),
      P("Repository layout: shared/ (config, LLM factory, DynamoDB, JSON utils), odh/ (Open Data Hub clients + sanitisation + weather), agents/ (Retriever, Reasoner, Generator, LangGraph), api/ (Lambda handler, FastAPI server, web UI), scripts/ (setup and deploy automation)."),
      P("Region: eu-central-1 (Frankfurt). Model: Claude Sonnet 4.5 via Bedrock inference profile eu.anthropic.claude-sonnet-4-5-20250929-v1:0. DynamoDB table: bz-agent-state."),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(__dirname + "/BZ-Agent_Report.docx", buf); console.log("wrote BZ-Agent_Report.docx"); });
