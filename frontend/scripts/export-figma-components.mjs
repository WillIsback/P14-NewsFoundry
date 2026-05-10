import fs from "node:fs";
import path from "node:path";

const FIGMA_TOKEN = process.env.FIGMA_TOKEN_SECRET;
const FIGMA_FILE_KEY = process.env.FIGMA_FILE_KEY;
const FIGMA_PAGE_NODE_ID = process.env.FIGMA_PAGE_NODE_ID;
const OUTPUT_PATH =
  process.env.FIGMA_PAGE_OUTPUT_PATH || "figma/components.snapshot.json";
const MAX_RETRIES = Number(process.env.FIGMA_MAX_RETRIES || "5");
const BASE_DELAY_MS = Number(process.env.FIGMA_RETRY_BASE_MS || "1200");
const MAX_DELAY_MS = Number(process.env.FIGMA_RETRY_MAX_DELAY_MS || "30000");

function requireEnv(name, value) {
  if (!value || String(value).trim() === "") {
    console.error(`[figma] Missing required env var: ${name}`);
    process.exit(1);
  }
}

function normalizeNodeId(nodeId) {
  return String(nodeId).trim().replace(/-/g, ":");
}

function normalizeFileKey(value) {
  const raw = String(value).trim();
  const match = raw.match(/\/file\/([^/?#]+)/);
  return match ? match[1] : raw;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getRetryAfterMs(retryAfterHeader) {
  if (!retryAfterHeader) return null;

  const asNumber = Number(retryAfterHeader);
  if (Number.isFinite(asNumber)) {
    // Heuristic: small numeric values are usually seconds, large ones often ms.
    const asMs = asNumber <= 600 ? asNumber * 1000 : asNumber;
    return Math.max(0, Math.min(asMs, MAX_DELAY_MS));
  }

  const asDate = Date.parse(retryAfterHeader);
  if (!Number.isNaN(asDate)) {
    return Math.max(0, Math.min(asDate - Date.now(), MAX_DELAY_MS));
  }

  return null;
}

function computeBackoffMs(attempt, retryAfterHeader) {
  const retryAfterMs = getRetryAfterMs(retryAfterHeader);
  if (retryAfterMs != null) {
    return retryAfterMs;
  }

  const exponential = BASE_DELAY_MS * 2 ** (attempt - 1);
  const jitter = Math.floor(Math.random() * 300);
  return Math.min(exponential + jitter, MAX_DELAY_MS);
}

async function fetchWithRetry(url, options) {
  let lastErrorPayload = null;
  let lastStatus = null;

  for (let attempt = 1; attempt <= MAX_RETRIES + 1; attempt += 1) {
    const response = await fetch(url, options);
    const payload = await response.json();

    if (response.ok) {
      return payload;
    }

    lastErrorPayload = payload;
    lastStatus = response.status;

    const retriable = response.status === 429 || response.status >= 500;
    const hasNextAttempt = attempt <= MAX_RETRIES;

    if (!retriable || !hasNextAttempt) {
      return {
        error: true,
        status: response.status,
        payload,
      };
    }

    const delayMs = computeBackoffMs(
      attempt,
      response.headers.get("retry-after"),
    );

    console.warn(
      `[figma] API temporary error (status ${response.status}), retry ${attempt}/${MAX_RETRIES} in ${delayMs}ms`,
    );

    await sleep(delayMs);
  }

  return {
    error: true,
    status: lastStatus,
    payload: lastErrorPayload,
  };
}

async function run() {
  requireEnv("FIGMA_TOKEN_SECRET", FIGMA_TOKEN);
  requireEnv("FIGMA_FILE_KEY", FIGMA_FILE_KEY);
  requireEnv("FIGMA_PAGE_NODE_ID", FIGMA_PAGE_NODE_ID);

  const fileKey = normalizeFileKey(FIGMA_FILE_KEY);
  const pageNodeId = normalizeNodeId(FIGMA_PAGE_NODE_ID);

  const url = new URL(`https://api.figma.com/v1/files/${fileKey}/nodes`);
  url.searchParams.set("ids", pageNodeId);
  url.searchParams.set("depth", "20");

  const result = await fetchWithRetry(url, {
    headers: {
      "X-Figma-Token": FIGMA_TOKEN,
    },
  });

  if (result?.error) {
    console.error("[figma] API error", {
      status: result.status,
      err: result.payload?.err,
      message: result.payload?.message,
    });
    process.exit(1);
  }

  const payload = result;
  const doc = payload?.nodes?.[pageNodeId]?.document;
  if (!doc) {
    console.error(
      `[figma] Node not found for FIGMA_PAGE_NODE_ID=${FIGMA_PAGE_NODE_ID}`,
    );
    process.exit(1);
  }

  const outputAbsolute = path.resolve(process.cwd(), OUTPUT_PATH);
  fs.mkdirSync(path.dirname(outputAbsolute), { recursive: true });

  const out = {
    generatedAt: new Date().toISOString(),
    fileKey,
    pageNodeId,
    nodeType: doc.type,
    nodeName: doc.name,
    data: doc,
  };

  fs.writeFileSync(outputAbsolute, JSON.stringify(out, null, 2), "utf8");

  console.log(
    `[figma] Saved ${OUTPUT_PATH} (node: ${doc.name}, type: ${doc.type})`,
  );
}

run().catch((error) => {
  console.error("[figma] Unexpected error:", error);
  process.exit(1);
});
