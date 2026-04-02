import type { VercelRequest, VercelResponse } from "@vercel/node";
import { syncNotionUnsubscribe, verifyResendWebhookSignature } from "./_unsubscribe";

export const config = {
  api: {
    bodyParser: false,
  },
};

async function readRawBody(req: VercelRequest): Promise<string> {
  if (typeof req.body === "string") {
    return req.body;
  }
  if (Buffer.isBuffer(req.body)) {
    return req.body.toString("utf8");
  }

  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

type ResendContactUpdatedEvent = {
  type: string;
  data?: {
    email?: string;
    unsubscribed?: boolean;
  };
};

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const signingSecret = process.env.RESEND_WEBHOOK_SIGNING_SECRET || process.env.RESEND_WEBHOOK_SECRET;
  if (!signingSecret) {
    return res.status(500).json({ error: "Webhook signing secret is not configured" });
  }

  const rawBody = await readRawBody(req);
  if (!verifyResendWebhookSignature(rawBody, req.headers, signingSecret)) {
    return res.status(401).json({ error: "Invalid webhook signature" });
  }

  let event: ResendContactUpdatedEvent;
  try {
    event = JSON.parse(rawBody) as ResendContactUpdatedEvent;
  } catch {
    return res.status(400).json({ error: "Invalid JSON payload" });
  }

  if (event.type !== "contact.updated" || !event.data?.email) {
    return res.status(200).json({ ok: true, ignored: true });
  }

  try {
    await syncNotionUnsubscribe(event.data.email, Boolean(event.data.unsubscribed));
    return res.status(200).json({ ok: true });
  } catch (error) {
    console.error("resend webhook sync error:", error);
    return res.status(500).json({ error: "Failed to sync Notion unsubscribe state" });
  }
}