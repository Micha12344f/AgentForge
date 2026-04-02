import { createHmac, timingSafeEqual } from "node:crypto";

const RESEND_BASE_URL = "https://api.resend.com";
const NOTION_BASE_URL = "https://api.notion.com/v1";
const NOTION_VERSION = "2022-06-28";
const LEADS_CRM_DB_ID = process.env.NOTION_LEADS_CRM_DB_ID || "30b652ea-6c6d-81e5-838b-c71135e14982";
const DEFAULT_UNSUBSCRIBE_BASE_URL = "https://hedgedge.info/api/handle-unsubscribe";
const WEBHOOK_TOLERANCE_SECONDS = 5 * 60;

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is not configured`);
  }
  return value;
}

function notionHeaders(): HeadersInit {
  const token = process.env.NOTION_API_KEY || process.env.NOTION_TOKEN;
  if (!token) {
    throw new Error("NOTION_API_KEY is not configured");
  }
  return {
    Authorization: `Bearer ${token}`,
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
  };
}

function resendHeaders(): HeadersInit {
  return {
    Authorization: `Bearer ${requireEnv("RESEND_API_KEY")}`,
    "Content-Type": "application/json",
  };
}

function unsubscribeSecret(): string {
  return requireEnv("UNSUBSCRIBE_SECRET");
}

function unsubscribeBaseUrl(): string {
  return (process.env.UNSUBSCRIBE_BASE_URL || DEFAULT_UNSUBSCRIBE_BASE_URL).replace(/\/$/, "");
}

export function buildUnsubscribeToken(email: string): string {
  return createHmac("sha256", unsubscribeSecret())
    .update(normalizeEmail(email), "utf8")
    .digest("hex");
}

export function verifySignedUnsubscribe(email: string, token: string): boolean {
  if (!token) {
    return false;
  }
  const expected = buildUnsubscribeToken(email);
  const receivedBytes = Buffer.from(token, "utf8");
  const expectedBytes = Buffer.from(expected, "utf8");
  if (receivedBytes.length !== expectedBytes.length) {
    return false;
  }
  return timingSafeEqual(receivedBytes, expectedBytes);
}

export function buildUnsubscribeUrl(email: string): string {
  const normalized = normalizeEmail(email);
  const token = buildUnsubscribeToken(normalized);
  return `${unsubscribeBaseUrl()}?email=${encodeURIComponent(normalized)}&token=${token}`;
}

export function buildUnsubscribeHeaders(email: string): Record<string, string> {
  const url = buildUnsubscribeUrl(email);
  return {
    "List-Unsubscribe": `<${url}>`,
    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
  };
}

export function appendUnsubscribeHtml(html: string, email: string): string {
  if (/unsubscribe/i.test(html)) {
    return html;
  }
  const url = buildUnsubscribeUrl(email);
  const footer = `<div style="margin-top:24px;padding-top:16px;border-top:1px solid #e5e7eb;font-size:12px;color:#6b7280;line-height:1.6;">If you no longer want these emails, <a href="${url}" style="color:#6b7280;text-decoration:underline;">unsubscribe here</a>.</div>`;

  if (/<\/body>/i.test(html)) {
    return html.replace(/<\/body>/i, `${footer}</body>`);
  }
  if (/<\/html>/i.test(html)) {
    return html.replace(/<\/html>/i, `${footer}</html>`);
  }
  return `${html}${footer}`;
}

type NotionQueryResponse = {
  results?: Array<{ id: string }>;
};

async function notionQueryByEmail(email: string): Promise<Array<{ id: string }>> {
  const response = await fetch(`${NOTION_BASE_URL}/databases/${LEADS_CRM_DB_ID}/query`, {
    method: "POST",
    headers: notionHeaders(),
    body: JSON.stringify({
      page_size: 100,
      filter: {
        property: "Email",
        email: { equals: normalizeEmail(email) },
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Notion query failed: ${response.status} ${await response.text()}`);
  }

  const data = (await response.json()) as NotionQueryResponse;
  return data.results || [];
}

export async function syncNotionUnsubscribe(email: string, unsubscribed: boolean): Promise<number> {
  const matches = await notionQueryByEmail(email);
  await Promise.all(
    matches.map(async (row) => {
      const response = await fetch(`${NOTION_BASE_URL}/pages/${row.id}`, {
        method: "PATCH",
        headers: notionHeaders(),
        body: JSON.stringify({
          properties: {
            Unsubscribed: { checkbox: unsubscribed },
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`Notion update failed: ${response.status} ${await response.text()}`);
      }
    }),
  );
  return matches.length;
}

type ResendContact = {
  id: string;
  email: string;
  unsubscribed?: boolean;
};

async function getResendContact(email: string): Promise<ResendContact | null> {
  const normalized = normalizeEmail(email);
  const response = await fetch(`${RESEND_BASE_URL}/contacts/${encodeURIComponent(normalized)}`, {
    method: "GET",
    headers: resendHeaders(),
  });

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Resend get contact failed: ${response.status} ${await response.text()}`);
  }
  return (await response.json()) as ResendContact;
}

export async function syncResendUnsubscribe(email: string, unsubscribed: boolean): Promise<void> {
  const normalized = normalizeEmail(email);
  const existing = await getResendContact(normalized);

  if (!existing) {
    const createResponse = await fetch(`${RESEND_BASE_URL}/contacts`, {
      method: "POST",
      headers: resendHeaders(),
      body: JSON.stringify({ email: normalized, unsubscribed }),
    });

    if (createResponse.status === 409) {
      const resolved = await getResendContact(normalized);
      if (!resolved) {
        throw new Error("Resend contact already exists but could not be reloaded");
      }
      const patchResponse = await fetch(`${RESEND_BASE_URL}/contacts/${resolved.id}`, {
        method: "PATCH",
        headers: resendHeaders(),
        body: JSON.stringify({ unsubscribed }),
      });
      if (!patchResponse.ok) {
        throw new Error(`Resend update contact failed: ${patchResponse.status} ${await patchResponse.text()}`);
      }
      return;
    }

    if (!createResponse.ok) {
      throw new Error(`Resend create contact failed: ${createResponse.status} ${await createResponse.text()}`);
    }
    return;
  }

  const updateResponse = await fetch(`${RESEND_BASE_URL}/contacts/${existing.id}`, {
    method: "PATCH",
    headers: resendHeaders(),
    body: JSON.stringify({ unsubscribed }),
  });

  if (!updateResponse.ok) {
    throw new Error(`Resend update contact failed: ${updateResponse.status} ${await updateResponse.text()}`);
  }
}

export async function syncUnsubscribeState(email: string, unsubscribed: boolean): Promise<{ notionUpdates: number }> {
  await syncResendUnsubscribe(email, unsubscribed);
  const notionUpdates = await syncNotionUnsubscribe(email, unsubscribed);
  return { notionUpdates };
}

function extractHeader(headers: Record<string, string | string[] | undefined>, primary: string, fallback: string): string {
  const raw = headers[primary] ?? headers[fallback];
  if (Array.isArray(raw)) {
    return raw[0] || "";
  }
  return raw || "";
}

function safeCompare(a: string, b: string): boolean {
  const aBytes = Buffer.from(a, "utf8");
  const bBytes = Buffer.from(b, "utf8");
  if (aBytes.length !== bBytes.length) {
    return false;
  }
  return timingSafeEqual(aBytes, bBytes);
}

export function verifyResendWebhookSignature(
  payload: string,
  headers: Record<string, string | string[] | undefined>,
  secret: string,
): boolean {
  const msgId = extractHeader(headers, "svix-id", "webhook-id");
  const timestamp = extractHeader(headers, "svix-timestamp", "webhook-timestamp");
  const signatureHeader = extractHeader(headers, "svix-signature", "webhook-signature");

  if (!msgId || !timestamp || !signatureHeader) {
    return false;
  }

  const timestampInt = Number.parseInt(timestamp, 10);
  if (!Number.isFinite(timestampInt)) {
    return false;
  }

  const now = Math.floor(Date.now() / 1000);
  if (timestampInt < now - WEBHOOK_TOLERANCE_SECONDS || timestampInt > now + WEBHOOK_TOLERANCE_SECONDS) {
    return false;
  }

  const rawSecret = secret.startsWith("whsec_") ? secret.slice("whsec_".length) : secret;
  const decodedSecret = Buffer.from(rawSecret, "base64");
  const expectedSignature = createHmac("sha256", decodedSecret)
    .update(`${msgId}.${timestamp}.${payload}`, "utf8")
    .digest("base64");

  return signatureHeader
    .split(" ")
    .map((value) => value.trim())
    .filter(Boolean)
    .some((value) => {
      const [version, signature] = value.split(",", 2);
      return version === "v1" && !!signature && safeCompare(signature, expectedSignature);
    });
}