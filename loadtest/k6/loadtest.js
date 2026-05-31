// k6 load test for BZ-Agent — compares Architecture A (Lambda+API Gateway)
// vs Architecture B (EC2) under load. Select a scenario at run time.
//
//   k6 run -e BASE_URL=http://3.126.251.241:8080 -e SCENARIO=load50 loadtest.js
//   k6 run -e BASE_URL=https://<api-id>.execute-api.eu-central-1.amazonaws.com -e SCENARIO=load200 loadtest.js
//   k6 run -e BASE_URL=... -e SCENARIO=stress1000 loadtest.js
//
// WARNING: every iteration triggers ~3 Amazon Bedrock calls. Running stress1000
// against a live deployment incurs real Bedrock cost and will hit Bedrock's
// per-minute quota. Use a mock/echo build or a sandbox account for the heavy runs.

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate = new Trend("itinerary_ok", true);
const planDuration = new Trend("plan_duration_ms", true);

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";
const PATH = __ENV.PATH || "/plan-itinerary";
const SCENARIO = __ENV.SCENARIO || "smoke";

const REQUESTS = [
  "I want to visit a museum in the centre and find parking nearby",
  "Show me places to see near the centre",
  "Plan my afternoon in Bolzano based on the weather",
  "Where can I park downtown and what museums are close?",
];

const SCENARIOS = {
  // 1 user, 1 request — sanity check
  smoke: { executor: "shared-iterations", vus: 1, iterations: 1, maxDuration: "2m" },

  // ~50 users generating sustained load
  load50: {
    executor: "ramping-vus", startVUs: 0,
    stages: [
      { duration: "1m", target: 50 },
      { duration: "3m", target: 50 },
      { duration: "30s", target: 0 },
    ],
  },

  // ~200 users — heavier sustained load
  load200: {
    executor: "ramping-vus", startVUs: 0,
    stages: [
      { duration: "2m", target: 200 },
      { duration: "5m", target: 200 },
      { duration: "1m", target: 0 },
    ],
  },

  // ~1000 users — aggressive stress / spike test
  stress1000: {
    executor: "ramping-vus", startVUs: 0,
    stages: [
      { duration: "1m", target: 200 },
      { duration: "2m", target: 1000 },
      { duration: "3m", target: 1000 },
      { duration: "1m", target: 0 },
    ],
  },
};

export const options = {
  scenarios: { [SCENARIO]: SCENARIOS[SCENARIO] },
  thresholds: {
    http_req_failed: ["rate<0.05"],      // <5% errors
    http_req_duration: ["p(95)<30000"],   // p95 under 30s
  },
};

export default function () {
  const body = JSON.stringify({
    user_id: `lt-${__VU}`,
    session_id: `lt-${__VU}-${__ITER}`,
    request: REQUESTS[Math.floor(Math.random() * REQUESTS.length)],
  });
  const res = http.post(`${BASE_URL}${PATH}`, body, {
    headers: { "Content-Type": "application/json" },
    timeout: "90s",
  });
  const ok = check(res, {
    "status 200": (r) => r.status === 200,
    "has itinerary": (r) => r.body && r.body.includes("itinerary"),
  });
  errorRate.add(ok ? 1 : 0);
  planDuration.add(res.timings.duration);
  sleep(1); // brief think-time between iterations
}
