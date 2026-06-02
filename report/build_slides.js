const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
p.author = "Nidhal Karchoud, Abdellah Derf";
p.title = "BZ-Agent";

// palette
const NAVY = "0F172A", NAVY2 = "16243B", BLUE = "2563EB", CYAN = "38BDF8",
      TEAL = "0891B2", GREEN = "10B981", AMBER = "F59E0B", RED = "EF4444",
      SLATE = "64748B", SLATEL = "94A3B8", LIGHT = "F1F5F9", CARD = "F8FAFC",
      WHITE = "FFFFFF";
const HEAD = "Georgia", BODY = "Calibri";
const DIR = __dirname;
const shadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12 });

function mark(s, n) {
  s.addText("BZ-Agent · Karchoud & Derf", { x: 0.6, y: 7.06, w: 5, h: 0.3, fontFace: BODY, fontSize: 9, color: SLATEL });
  s.addText(String(n), { x: 12.3, y: 7.06, w: 0.5, h: 0.3, fontFace: BODY, fontSize: 9, color: SLATEL, align: "right" });
}
function title(s, t) {
  s.addText(t, { x: 0.6, y: 0.38, w: 12.1, h: 0.85, fontFace: HEAD, fontSize: 28, bold: true, color: NAVY, valign: "middle", margin: 0 });
}
function card(s, x, y, w, h, fill) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill || WHITE }, line: { color: "E2E8F0", width: 1 }, rectRadius: 0.08, shadow: shadow() });
}

// ---------- Slide 1 — Title (dark) ----------
let s = p.addSlide(); s.background = { color: NAVY };
s.addShape(p.shapes.OVAL, { x: 10.7, y: -1.2, w: 3.6, h: 3.6, fill: { color: BLUE, transparency: 80 }, line: { type: "none" } });
s.addShape(p.shapes.OVAL, { x: 11.8, y: 5.0, w: 3.0, h: 3.0, fill: { color: TEAL, transparency: 82 }, line: { type: "none" } });
s.addText("BZ-Agent", { x: 0.9, y: 1.7, w: 10, h: 1.2, fontFace: HEAD, fontSize: 60, bold: true, color: WHITE, margin: 0 });
s.addText("Smart-City Mobility & Event Orchestrator", { x: 0.95, y: 2.95, w: 11, h: 0.6, fontFace: BODY, fontSize: 24, color: CYAN, margin: 0 });
s.addText("A cloud-native, multi-agent system on AWS — comparing Lambda vs EC2", { x: 0.95, y: 3.55, w: 11, h: 0.5, fontFace: BODY, fontSize: 16, italic: true, color: SLATEL, margin: 0 });
s.addText([
  { text: "Nidhal Karchoud", options: { bold: true } },
  { text: "    ·    ", options: { color: TEAL } },
  { text: "Abdellah Derf", options: { bold: true } },
], { x: 0.95, y: 4.7, w: 11, h: 0.5, fontFace: BODY, fontSize: 20, color: WHITE, margin: 0 });
s.addText("Cloud Computing and Distributed Systems", { x: 0.95, y: 5.25, w: 11, h: 0.4, fontFace: BODY, fontSize: 14, color: SLATEL, margin: 0 });
s.addText("github.com/yar01110/bz-agent", { x: 0.95, y: 5.7, w: 11, h: 0.4, fontFace: BODY, fontSize: 13, color: CYAN, margin: 0, hyperlink: { url: "https://github.com/yar01110/bz-agent" } });

// ---------- Slide 2 — The Question (light) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "The Question");
s.addText([
  { text: "BZ-Agent turns a natural-language request — ", options: { breakLine: false } },
  { text: "“visit a museum and find parking nearby”", options: { italic: true, color: BLUE, breakLine: true } },
  { text: "— into a validated itinerary, grounded in live Bolzano open data.", options: {} },
], { x: 0.6, y: 1.45, w: 6.0, h: 1.3, fontFace: BODY, fontSize: 17, color: "1E293B", lineSpacingMultiple: 1.15 });
s.addText([
  { text: "We deploy the same application two ways and ask:", options: { bold: true, breakLine: true, paraSpaceAfter: 6 } },
  { text: "How do serverless (Lambda) and server-based (EC2) deployments compare in performance, scalability, reliability, and cost — and where is the real bottleneck?", options: { italic: true } },
], { x: 0.6, y: 3.0, w: 6.0, h: 2.0, fontFace: BODY, fontSize: 16, color: "1E293B", lineSpacingMultiple: 1.15 });
// right: research-question callout card
card(s, 7.1, 1.6, 5.6, 4.2, NAVY);
s.addText("RESEARCH QUESTION", { x: 7.4, y: 1.9, w: 5.0, h: 0.4, fontFace: BODY, fontSize: 12, bold: true, color: CYAN, charSpacing: 2, margin: 0 });
s.addText("Serverless vs. server:\nwhich wins, and why?", { x: 7.4, y: 2.4, w: 5.0, h: 1.4, fontFace: HEAD, fontSize: 26, bold: true, color: WHITE, margin: 0 });
s.addText([
  { text: "Performance under load", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "Scalability & reliability", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "Cost transparency", options: { bullet: true, color: WHITE } },
], { x: 7.5, y: 4.0, w: 5.0, h: 1.6, fontFace: BODY, fontSize: 15, color: WHITE, paraSpaceAfter: 6 });
mark(s, 2);

// ---------- Slide 3 — Architecture (light) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "System Architecture");
s.addText([
  { text: "Compute is just the engine.", options: { bold: true, breakLine: true, paraSpaceAfter: 8 } },
  { text: "Lambda / EC2 only orchestrate the LangGraph pipeline.", options: { bullet: true, breakLine: true } },
  { text: "Amazon Bedrock (Claude) is the reasoning brain.", options: { bullet: true, breakLine: true } },
  { text: "DynamoDB holds session state & scratchpad.", options: { bullet: true, breakLine: true } },
  { text: "Open Data Hub provides live POIs, parking & weather.", options: { bullet: true } },
], { x: 0.6, y: 1.5, w: 4.5, h: 4.0, fontFace: BODY, fontSize: 15, color: "1E293B", paraSpaceAfter: 8, lineSpacingMultiple: 1.05 });
{ const h = 4.55, w = h * 1.346; s.addImage({ path: `${DIR}/architecture.png`, x: 13.33 - w - 0.5, y: 1.45, w, h }); }
mark(s, 3);

// ---------- Slide 4 — Pipeline (light) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "The Agentic RAG Pipeline");
const steps = [
  ["1  Retriever", BLUE, "Maps the request to ODH tools, fetches data, and SANITISES it to a few flat fields — the key guard against context overflow & hallucination."],
  ["2  Reasoner", TEAL, "Applies hard constraints: proximity, transit buffers, parking availability, and weather (rain → indoor). Outputs a validated draft."],
  ["3  Generator", GREEN, "Renders the validated draft into a friendly itinerary. Invents nothing — only formats facts the Reasoner approved."],
];
steps.forEach((st, i) => {
  const x = 0.6 + i * 4.15;
  card(s, x, 1.7, 3.8, 3.7, CARD);
  s.addShape(p.shapes.RECTANGLE, { x, y: 1.7, w: 3.8, h: 0.12, fill: { color: st[1] }, line: { type: "none" } });
  s.addText(st[0], { x: x + 0.3, y: 2.0, w: 3.3, h: 0.6, fontFace: HEAD, fontSize: 21, bold: true, color: st[1], margin: 0 });
  s.addText(st[2], { x: x + 0.3, y: 2.7, w: 3.3, h: 2.4, fontFace: BODY, fontSize: 14, color: "334155", margin: 0, lineSpacingMultiple: 1.1 });
  if (i < 2) s.addText("→", { x: x + 3.6, y: 3.2, w: 0.8, h: 0.6, fontFace: BODY, fontSize: 26, bold: true, color: SLATEL, align: "center", margin: 0 });
});
s.addText("State flows one way; each node writes its slice to the DynamoDB scratchpad (full traceability).", { x: 0.6, y: 5.6, w: 12, h: 0.5, fontFace: BODY, fontSize: 13, italic: true, color: SLATE });
mark(s, 4);

// ---------- Slide 5 — Two architectures (light) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "Two Deployment Architectures");
function archCard(x, name, tag, color, rows) {
  card(s, x, 1.6, 5.8, 4.4, WHITE);
  s.addShape(p.shapes.RECTANGLE, { x, y: 1.6, w: 5.8, h: 0.7, fill: { color }, line: { type: "none" } });
  s.addText(name, { x: x + 0.35, y: 1.62, w: 5.1, h: 0.66, fontFace: HEAD, fontSize: 20, bold: true, color: WHITE, valign: "middle", margin: 0 });
  s.addText(tag, { x: x + 0.35, y: 2.45, w: 5.1, h: 0.4, fontFace: BODY, fontSize: 13, italic: true, color: SLATE, margin: 0 });
  s.addText(rows.map((r, i) => ({ text: r, options: { bullet: true, breakLine: i < rows.length - 1 } })),
    { x: x + 0.4, y: 2.95, w: 5.1, h: 2.9, fontFace: BODY, fontSize: 14.5, color: "1E293B", paraSpaceAfter: 7 });
}
archCard(0.6, "AWS Lambda + API Gateway", "Architecture A — Serverless", BLUE, [
  "Scales automatically, per request", "Zero cost when idle", "Cold start ~5–18 s", "15-min execution limit", "Best for spiky / low-medium load"]);
archCard(6.9, "Amazon EC2 (in custom VPC)", "Architecture B — Server", TEAL, [
  "Always-on, fixed capacity", "Billed hourly even when idle", "No cold start", "No timeout limit", "Best for steady, high load"]);
s.addText("Same container image, two execution models — the basis of every experiment.", { x: 0.6, y: 6.15, w: 12, h: 0.4, fontFace: BODY, fontSize: 13, italic: true, color: SLATE });
mark(s, 5);

// ---------- Slide 6 — Method (light) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "Experimental Method");
const method = [
  ["Measure", BLUE, "Real single-request latency on both endpoints (avg ~16.9 s, Bedrock-bound)."],
  ["Sweep", TEAL, "Concurrency 25→400 on the cost-free /health endpoint (no Bedrock cost)."],
  ["Model", AMBER, "Extrapolate to 50 / 200 / 1000 users from real numbers + AWS service limits."],
  ["Experiment", GREEN, "Elasticity (ALB + Auto Scaling) and failure-recovery, run live."],
];
method.forEach((m, i) => {
  const y = 1.6 + i * 1.18;
  s.addShape(p.shapes.OVAL, { x: 0.7, y, w: 0.85, h: 0.85, fill: { color: m[1] }, line: { type: "none" } });
  s.addText(String(i + 1), { x: 0.7, y, w: 0.85, h: 0.85, fontFace: HEAD, fontSize: 24, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  s.addText(m[0], { x: 1.8, y: y - 0.02, w: 2.4, h: 0.5, fontFace: HEAD, fontSize: 19, bold: true, color: NAVY, margin: 0 });
  s.addText(m[2], { x: 1.8, y: y + 0.42, w: 10.6, h: 0.6, fontFace: BODY, fontSize: 14.5, color: "334155", margin: 0 });
});
s.addText("Repeated runs → descriptive statistics → charts. Why model 1000 users? A real run = tens of thousands of Bedrock calls (cost + quota throttling).",
  { x: 0.7, y: 6.45, w: 12, h: 0.5, fontFace: BODY, fontSize: 12.5, italic: true, color: SLATE });
mark(s, 6);

// ---------- Slide 7 — Finding 1: Saturation (light) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "Finding 1 — A Single Instance Saturates");
{ const h = 4.3, w = h * 1.825; s.addImage({ path: `${DIR}/loadchart.png`, x: 0.5, y: 1.5, w, h }); }
card(s, 8.5, 1.7, 4.3, 3.9, NAVY);
s.addText("THE BREAKING POINT", { x: 8.8, y: 1.95, w: 3.8, h: 0.4, fontFace: BODY, fontSize: 12, bold: true, color: CYAN, charSpacing: 1.5, margin: 0 });
s.addText("~150–200", { x: 8.8, y: 2.45, w: 3.8, h: 0.9, fontFace: HEAD, fontSize: 44, bold: true, color: WHITE, margin: 0 });
s.addText("concurrent connections", { x: 8.8, y: 3.4, w: 3.8, h: 0.4, fontFace: BODY, fontSize: 14, color: SLATEL, margin: 0 });
s.addText([
  { text: "Peak throughput at ~25 conc (322 req/s)", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "By 300+, p95 ≈ 15 s — effectively broken", options: { bullet: true, color: WHITE } },
], { x: 8.9, y: 4.0, w: 3.7, h: 1.4, fontFace: BODY, fontSize: 13.5, color: WHITE, paraSpaceAfter: 6 });
mark(s, 7);

// ---------- Slide 8 — Finding 2: Elasticity (native chart) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "Finding 2 — Elasticity Raises the Ceiling");
s.addChart(p.charts.BAR, [
  { name: "Single EC2", labels: ["50", "100", "200", "300"], values: [187, 115, 88, 78] },
  { name: "ALB + ASG (2 inst.)", labels: ["50", "100", "200", "300"], values: [248, 142, 125, 133] },
], {
  x: 0.5, y: 1.5, w: 7.6, h: 4.6, barDir: "col",
  chartColors: [SLATEL, BLUE], showLegend: true, legendPos: "b", legendColor: "334155",
  catAxisTitle: "Concurrent connections", showCatAxisTitle: true, catAxisTitleColor: SLATE,
  valAxisTitle: "Throughput (req/s)", showValAxisTitle: true, valAxisTitleColor: SLATE,
  catAxisLabelColor: "64748B", valAxisLabelColor: "64748B",
  valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
  showValue: true, dataLabelColor: "1E293B", dataLabelFontSize: 9, dataLabelPosition: "outEnd",
});
card(s, 8.5, 1.7, 4.3, 4.0, CARD);
s.addText("AT 300 CONCURRENCY", { x: 8.8, y: 1.95, w: 3.8, h: 0.4, fontFace: BODY, fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5, margin: 0 });
s.addText("+70%", { x: 8.8, y: 2.4, w: 3.8, h: 0.85, fontFace: HEAD, fontSize: 46, bold: true, color: GREEN, margin: 0 });
s.addText("throughput vs a single instance", { x: 8.8, y: 3.3, w: 3.8, h: 0.4, fontFace: BODY, fontSize: 14, color: "334155", margin: 0 });
s.addText([
  { text: "≈ half the median latency", options: { bullet: true, breakLine: true, color: "1E293B" } },
  { text: "0% errors throughout", options: { bullet: true, breakLine: true, color: "1E293B" } },
  { text: "Capacity follows demand", options: { bullet: true, color: "1E293B" } },
], { x: 8.9, y: 3.85, w: 3.7, h: 1.7, fontFace: BODY, fontSize: 14, color: "1E293B", paraSpaceAfter: 7 });
mark(s, 8);

// ---------- Slide 9 — Finding 3: Failure recovery (dark) ----------
s = p.addSlide(); s.background = { color: NAVY };
s.addText("Finding 3 — Self-Healing Under Failure", { x: 0.6, y: 0.45, w: 12, h: 0.8, fontFace: HEAD, fontSize: 28, bold: true, color: WHITE, margin: 0 });
s.addText("We killed one fleet instance mid-traffic and measured what the client saw.", { x: 0.6, y: 1.3, w: 12, h: 0.5, fontFace: BODY, fontSize: 15, italic: true, color: SLATEL, margin: 0 });
const stats = [
  ["0", "client-visible outage\n(0 / 454 health checks failed)", GREEN],
  ["~117 s", "self-heal recovery\n(ASG launched a replacement)", CYAN],
  ["100%", "outage for a single instance\n(until manual redeploy)", RED],
];
stats.forEach((st, i) => {
  const x = 0.6 + i * 4.15;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.2, w: 3.8, h: 3.0, fill: { color: NAVY2 }, line: { color: "1E3A5F", width: 1 }, rectRadius: 0.1 });
  s.addText(st[0], { x: x + 0.2, y: 2.55, w: 3.4, h: 1.3, fontFace: HEAD, fontSize: 52, bold: true, color: st[2], align: "center", margin: 0 });
  s.addText(st[1], { x: x + 0.25, y: 3.95, w: 3.3, h: 1.0, fontFace: BODY, fontSize: 14, color: WHITE, align: "center", margin: 0 });
});
s.addText("“Cattle, not pets”: the load balancer routed around the dead node instantly, and Auto Scaling replaced it automatically. Lambda is resilient the same way by design.",
  { x: 0.6, y: 5.5, w: 12.1, h: 0.8, fontFace: BODY, fontSize: 14, italic: true, color: SLATEL, align: "center" });
mark(s, 9);

// ---------- Slide 10 — Cost (native pie) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "Where the Money Goes");
s.addChart(p.charts.PIE, [{ name: "Cost share", labels: ["Bedrock (LLM)", "Compute + infra"], values: [95, 5] }], {
  x: 0.6, y: 1.5, w: 6.2, h: 4.6, chartColors: [BLUE, "CBD5E1"],
  showPercent: true, showLegend: true, legendPos: "b", legendColor: "334155",
  dataLabelColor: "FFFFFF", dataLabelFontSize: 14, dataLabelFontBold: true,
});
card(s, 7.3, 1.7, 5.4, 4.1, NAVY);
s.addText("KEY INSIGHT", { x: 7.6, y: 1.95, w: 4.8, h: 0.4, fontFace: BODY, fontSize: 12, bold: true, color: CYAN, charSpacing: 1.5, margin: 0 });
s.addText("The LLM is ~95% of cost — identical for both architectures.", { x: 7.6, y: 2.4, w: 4.8, h: 1.3, fontFace: HEAD, fontSize: 22, bold: true, color: WHITE, margin: 0 });
s.addText([
  { text: "The compute choice is a rounding error on the bill.", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "Lambda wins on idle (pay-per-use); EC2 only if ~100% utilised 24/7.", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "Sanitisation keeps prompts small to control token cost.", options: { bullet: true, color: WHITE } },
], { x: 7.7, y: 3.9, w: 4.7, h: 1.8, fontFace: BODY, fontSize: 13.5, color: WHITE, paraSpaceAfter: 7 });
mark(s, 10);

// ---------- Slide 11 — Security & VPC (light) ----------
s = p.addSlide(); s.background = { color: WHITE }; title(s, "Security & Network Isolation");
{ const h = 4.4, w = h * 1.380; s.addImage({ path: `${DIR}/vpc_diagram.png`, x: 0.5, y: 1.5, w, h }); }
s.addText([
  { text: "Custom VPC", options: { bold: true, breakLine: true, color: NAVY, paraSpaceAfter: 4 } },
  { text: "Own subnet, internet gateway & routing", options: { bullet: true, breakLine: true } },
  { text: "Private DynamoDB gateway endpoint (free) — state never leaves AWS", options: { bullet: true, breakLine: true } },
  { text: "Security group: only port 8080 inbound", options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
  { text: "Least privilege", options: { bold: true, breakLine: true, color: NAVY, paraSpaceAfter: 4 } },
  { text: "Scoped IAM roles (Bedrock + DynamoDB only)", options: { bullet: true, breakLine: true } },
  { text: "Bedrock via IAM — no long-lived API key", options: { bullet: true, breakLine: true } },
  { text: "Secrets excluded from git (.gitignore)", options: { bullet: true } },
], { x: 7.0, y: 1.55, w: 5.8, h: 4.6, fontFace: BODY, fontSize: 14, color: "334155", paraSpaceAfter: 6, lineSpacingMultiple: 1.05 });
mark(s, 11);

// ---------- Slide 12 — Conclusions (dark) ----------
s = p.addSlide(); s.background = { color: NAVY };
s.addText("Conclusions & Reflection", { x: 0.6, y: 0.45, w: 12, h: 0.8, fontFace: HEAD, fontSize: 28, bold: true, color: WHITE, margin: 0 });
s.addText([
  { text: "Lambda is the better default", options: { bold: true, color: CYAN, breakLine: true } },
  { text: "auto-scaling, no single point of failure, $0 idle — ideal for bursty traffic.", options: { breakLine: true, color: WHITE, paraSpaceAfter: 10 } },
  { text: "EC2 needs help to scale", options: { bold: true, color: CYAN, breakLine: true } },
  { text: "a single instance breaks at ~150–200 conc; an ALB + Auto Scaling Group fixes it.", options: { breakLine: true, color: WHITE, paraSpaceAfter: 10 } },
  { text: "Bedrock is the real bottleneck & cost", options: { bold: true, color: CYAN, breakLine: true } },
  { text: "~95% of spend and the shared limit at high load — compute choice barely matters.", options: { color: WHITE } },
], { x: 0.6, y: 1.5, w: 7.3, h: 4.2, fontFace: BODY, fontSize: 15.5, lineSpacingMultiple: 1.05 });
card(s, 8.3, 1.6, 4.5, 4.5, NAVY2);
s.addText("Limitations & next steps", { x: 8.6, y: 1.85, w: 3.9, h: 0.5, fontFace: HEAD, fontSize: 17, bold: true, color: AMBER, margin: 0 });
s.addText([
  { text: "1000 users modelled, not run (cost/quota)", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "Single region / single AZ baseline", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "Add target-tracking auto-scaling policy", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "Lambda in private subnets (NAT cost)", options: { bullet: true, breakLine: true, color: WHITE } },
  { text: "Live SASA bus / GTFS schedules", options: { bullet: true, color: WHITE } },
], { x: 8.7, y: 2.45, w: 3.9, h: 3.4, fontFace: BODY, fontSize: 13.5, color: WHITE, paraSpaceAfter: 8 });
mark(s, 12);

// ---------- Slide 13 — Thank you (dark) ----------
s = p.addSlide(); s.background = { color: NAVY };
s.addShape(p.shapes.OVAL, { x: -1.2, y: 5.2, w: 3.6, h: 3.6, fill: { color: TEAL, transparency: 80 }, line: { type: "none" } });
s.addShape(p.shapes.OVAL, { x: 11.4, y: -1.0, w: 3.2, h: 3.2, fill: { color: BLUE, transparency: 80 }, line: { type: "none" } });
s.addText("Thank you", { x: 0.9, y: 2.2, w: 11, h: 1.1, fontFace: HEAD, fontSize: 50, bold: true, color: WHITE, margin: 0 });
s.addText("Questions & demo welcome", { x: 0.95, y: 3.4, w: 11, h: 0.5, fontFace: BODY, fontSize: 20, color: CYAN, margin: 0 });
s.addText([
  { text: "Nidhal Karchoud  ·  Abdellah Derf", options: { breakLine: true, bold: true } },
  { text: "github.com/yar01110/bz-agent", options: { color: CYAN } },
], { x: 0.95, y: 4.5, w: 11, h: 1.0, fontFace: BODY, fontSize: 16, color: WHITE, paraSpaceAfter: 6 });

p.writeFile({ fileName: `${DIR}/BZ-Agent_Presentation.pptx` }).then(() => console.log("wrote BZ-Agent_Presentation.pptx"));
