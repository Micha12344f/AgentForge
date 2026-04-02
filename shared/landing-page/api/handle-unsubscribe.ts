import type { VercelRequest, VercelResponse } from "@vercel/node";
import { normalizeEmail, syncUnsubscribeState, verifySignedUnsubscribe } from "./_unsubscribe";

function renderHtml(title: string, message: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${title}</title>
</head>
<body style="margin:0;background:#f5f7fb;font-family:'Segoe UI',Arial,sans-serif;color:#111827;">
  <div style="max-width:560px;margin:64px auto;padding:0 20px;">
    <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;padding:32px;box-shadow:0 8px 30px rgba(15,23,42,.06);">
      <h1 style="margin:0 0 12px;font-size:28px;line-height:1.2;">${title}</h1>
      <p style="margin:0;font-size:15px;line-height:1.7;color:#4b5563;">${message}</p>
    </div>
  </div>
</body>
</html>`;
}

function sendResponse(req: VercelRequest, res: VercelResponse, status: number, title: string, message: string) {
  if (req.method === "GET") {
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    return res.status(status).send(renderHtml(title, message));
  }
  return res.status(status).json({ success: status < 400, message });
}

function getString(value: unknown): string {
  if (Array.isArray(value)) {
    return typeof value[0] === "string" ? value[0] : "";
  }
  return typeof value === "string" ? value : "";
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "GET" && req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const email = normalizeEmail(getString(req.query.email) || getString(req.body?.email));
  const token = getString(req.query.token) || getString(req.body?.token);

  if (!email || !token) {
    return sendResponse(req, res, 400, "Invalid request", "This unsubscribe link is incomplete.");
  }

  if (!verifySignedUnsubscribe(email, token)) {
    return sendResponse(req, res, 400, "Invalid request", "This unsubscribe link is not valid.");
  }

  try {
    await syncUnsubscribeState(email, true);
    return sendResponse(
      req,
      res,
      200,
      "You are unsubscribed",
      "You will no longer receive Hedge Edge marketing emails. Your preference has also been synced to our CRM.",
    );
  } catch (error) {
    console.error("unsubscribe sync error:", error);
    return sendResponse(
      req,
      res,
      500,
      "Something went wrong",
      "We could not complete your unsubscribe request right now. Please try again shortly.",
    );
  }
}