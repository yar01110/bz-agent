const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, TableOfContents, VerticalAlign,
} = require("docx");

const CW = 9360;
const BLUE = "2563EB", NAVY = "0F172A", SLATE = "475569", HEADERFILL = "D5E8F0";

const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const P = (t, o = {}) => new Paragraph({ spacing: { after: 120 }, children: [new TextRun({ text: t, ...o })] });
const bullet = (t) => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 60 }, children: [new TextRun(t)] });

const bd = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: bd, bottom: bd, left: bd, right: bd, insideHorizontal: bd, insideVertical: bd };
function cell(text, w, head) {
  return new TableCell({ width: { size: w, type: WidthType.DXA }, borders,
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    shading: head ? { fill: HEADERFILL, type: ShadingType.CLEAR } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: text, bold: head, color: head ? NAVY : undefined, size: 20 })] })] });
}
function table(widths, rows) {
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, ri) => new TableRow({ tableHeader: ri === 0, children: r.map((c, ci) => cell(c, widths[ci], ri === 0)) })) });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: NAVY }, paragraph: { spacing: { before: 260, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: BLUE }, paragraph: { spacing: { before: 180, after: 90 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 600, hanging: 280 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "BZ-Agent · Setup Roadmap · Page ", size: 16, color: SLATE }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: SLATE })] })] }) },
    children: [
      new Paragraph({ spacing: { before: 1600 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: "BZ-Agent", bold: true, size: 64, color: NAVY })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80 }, children: [new TextRun({ text: "Setup Roadmap", size: 34, color: BLUE })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60 }, children: [new TextRun({ text: "How the whole system was built — from an empty AWS account to two live, load-tested deployments", size: 20, color: SLATE, italics: true })] }),
      new Paragraph({ children: [new PageBreak()] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }),
      new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
      new Paragraph({ children: [new PageBreak()] }),

      H1("Build order at a glance"),
      P("accounts/keys → scaffold → ODH + sanitize → agents + LangGraph → local verify → ECR + IAM → two images → Lambda + API Gateway → EC2 → custom VPC → features (weather / streaming / UI) → load test → report + Terraform.", { italics: true }),

      H1("Phase 0 — Accounts, access & local tools"),
      P("AWS Free-plan account (~$120 credits). Enabled Amazon Bedrock model access for Anthropic Claude Sonnet 4.5 in eu-central-1 (a one-time console setting). Created IAM user bz-agent-dev with an access key, stored in ~/.aws/credentials so boto3 can authenticate."),
      P("Key fact: a Claude Pro subscription does NOT include API access — we use Bedrock (Claude via AWS/IAM), so there is one bill and no separate API key."),
      P("Local tools: Python, Docker Desktop, Node.js, Git. IAM permissions were attached reactively, per phase (least privilege):"),
      table([3000, 6360], [
        ["Phase", "Policies attached to bz-agent-dev"],
        ["Run the agent", "AmazonBedrockFullAccess, AmazonDynamoDBFullAccess"],
        ["Deploy", "ECR + Lambda + EC2 + IAM full access"],
        ["API Gateway", "AmazonAPIGatewayAdministrator"],
      ]),

      H1("Phase 1 — Project scaffolding"),
      P("A monorepo with a microservices boundary: shared/ (config, LLM factory, DynamoDB, JSON utils), odh/ (Open Data Hub clients + sanitization + weather), agents/ (Retriever, Reasoner, Generator, LangGraph), api/ (Lambda handler, FastAPI server, web UI), scripts/ (setup + deploy). The LLM provider is a one-line switch (Bedrock or Anthropic)."),

      H1("Phase 2 — Open Data Hub integration + sanitization"),
      P("Built clients for Content (POIs, events), Mobility (parking, bike stations) and Weather (Bolzano district forecast). A sanitization layer strips raw ODH JSON to a few flat fields — the key defense against context overflow, cost blow-up, and hallucination."),
      P("Gotchas found by probing the live API: POI names live in Shortname / Detail.<lang>.Title; museum filtering needs tagfilter (not categorycodes); the old bike-availability dataset is dead (2016 data), so we switched to live ParkingStation + BikesharingStation."),

      H1("Phase 3 — Agentic core"),
      P("Retriever → Reasoner → Generator wired as a LangGraph state machine; state flows one way and each node writes its slice to the DynamoDB scratchpad. DynamoDB uses single-table design: PK = USER#<id>, SK = SESSION#<id>, on-demand billing."),

      H1("Phase 4 — Local verification (against real AWS)"),
      P("Created the table, then ran the pipeline end-to-end. Four real bugs were found and fixed:"),
      table([4680, 4680], [
        ["Symptom", "Fix"],
        ["ODH ReadTimeout", "30s timeout + per-fetch resilience"],
        ["DynamoDB rejects floats", "convert floats → Decimal"],
        ["Scratchpad document-path invalid", "create skeleton + defensive init"],
        ["Generator hallucinated (empty draft)", "robust JSON extraction (Claude wrapped JSON in code fences)"],
      ]),

      H1("Phase 5 — Containerize & deploy (two architectures)"),
      P("Created ECR + IAM roles, built two images from one codebase (a uvicorn/FastAPI server image for EC2 and an AWS Lambda base image), and pushed them to ECR. Deployed Architecture A (Lambda from image, fronted by an HTTP API Gateway) and Architecture B (EC2 pulls the image and runs it)."),
      P("Gotchas: Docker Desktop builds OCI manifests, which Lambda rejects → rebuilt with Docker v2 media types; the SSM AMI lookup was denied → switched to describe_images; the Lambda Function URL returned 403 (newer accounts block public Function URLs) → used API Gateway instead."),

      H1("Phase 6 — Custom VPC (network isolation)"),
      P("Built a custom VPC and migrated the EC2 workload into it: VPC 10.0.0.0/16, a public subnet 10.0.1.0/24, an internet gateway with a 0.0.0.0/0 route, a free DynamoDB gateway endpoint (state traffic stays on AWS's private network), and a security group allowing only inbound TCP 8080."),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 }, children: [
        new ImageRun({ type: "png", data: fs.readFileSync(__dirname + "/vpc_diagram.png"),
          transformation: { width: 560, height: 396 }, altText: { title: "VPC", description: "Custom VPC", name: "vpc" } })] }),

      H1("Phase 7 — Feature enhancements"),
      bullet("Weather-aware reasoning: rain/storm → indoor stops, clear → outdoor (verified)."),
      bullet("Geo-filtering: mobility data bounded to a Bolzano box (drops outliers)."),
      bullet("SSE progress streaming + a browser UI showing a live checklist as each agent finishes."),

      H1("Phase 8 — Load testing & comparison"),
      P("Measured per-request latency (~16.9 s) and ran an EC2 saturation sweep on the cost-free /health endpoint (25 → 400 concurrency): throughput peaks at ~25 (322 req/s), latency spikes at 150–200, and the instance is effectively broken by 300+ (p95 ≈ 15 s). Modelled the 50/200/1000-user case and analysed reliability, scalability, resource usage, and billing. Conclusion: Bedrock (the LLM) is ~95% of cost and identical for both architectures; at ~1000 users the Bedrock quota is the shared bottleneck."),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 120 }, children: [
        new ImageRun({ type: "png", data: fs.readFileSync(__dirname + "/loadchart.png"),
          transformation: { width: 520, height: 289 }, altText: { title: "Saturation", description: "Saturation curve", name: "load" } })] }),

      H1("Phase 9 — Deliverables"),
      bullet("report/BZ-Agent_Report.docx — full project report with diagrams, comparison, and analysis."),
      bullet("infra/ — Terraform codifying the whole stack (Infrastructure as Code)."),
      bullet("loadtest/ — k6 scripts, infra probe, methodology, results."),
      bullet("All committed to Git; .env and secrets excluded via .gitignore."),
    ],
  }],
});

Packer.toBuffer(doc).then((b) => { fs.writeFileSync(__dirname + "/BZ-Agent_Setup_Roadmap.docx", b); console.log("wrote BZ-Agent_Setup_Roadmap.docx"); });
