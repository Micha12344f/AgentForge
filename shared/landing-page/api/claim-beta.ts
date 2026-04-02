import type { VercelRequest, VercelResponse } from "@vercel/node";
import { createClient } from "@supabase/supabase-js";
import { appendUnsubscribeHtml, buildUnsubscribeHeaders } from "./_unsubscribe";

// Pool placeholder — keys with this email are "available" for claiming
const POOL_PLACEHOLDER = "pool-unassigned@beta.hedgedge-internal";

// In-memory rate limit store (resets on cold start — intentional)
const EMAIL_WINDOW_MS = 24 * 60 * 60 * 1000; // 1 claim per email per 24 h
const IP_WINDOW_MS = 60 * 60 * 1000;         // 5 claims per IP per hour
const IP_MAX = 5;

const emailLastClaim = new Map<string, number>();
const ipClaims = new Map<string, number[]>();

function isEmailRateLimited(email: string): boolean {
  const last = emailLastClaim.get(email);
  return last !== undefined && Date.now() - last < EMAIL_WINDOW_MS;
}

function isIpRateLimited(ip: string): boolean {
  const now = Date.now();
  const times = (ipClaims.get(ip) || []).filter(t => now - t < IP_WINDOW_MS);
  ipClaims.set(ip, times);
  return times.length >= IP_MAX;
}

function recordClaim(email: string, ip: string): void {
  emailLastClaim.set(email.toLowerCase(), Date.now());
  const times = ipClaims.get(ip) || [];
  times.push(Date.now());
  ipClaims.set(ip, times);
}

function buildKeyEmail(firstName: string, licenseKey: string): string {
  return `
<div style="font-family:'Segoe UI',Inter,Helvetica,Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0a;color:#e5e5e5;border-radius:16px;overflow:hidden;">
  <!-- Header -->
  <div style="background:linear-gradient(135deg,#0a0a0a 0%,#111 100%);padding:40px 32px 24px;text-align:center;border-bottom:1px solid #1a1a1a;">
    <h1 style="color:#22c55e;font-size:28px;margin:0 0 8px;font-weight:700;">You're In!</h1>
    <p style="color:#a3a3a3;margin:0;font-size:16px;">Welcome to the Hedge Edge Beta, ${firstName}</p>
  </div>

  <div style="padding:32px;">
    <!-- Key Section -->
    <p style="margin:0 0 16px;font-size:15px;color:#d4d4d4;">Here is your <strong style="color:#fff;">unique beta license key</strong>:</p>
    <div style="background:#111;border:2px solid #22c55e40;border-radius:12px;padding:24px;text-align:center;margin:0 0 8px;">
      <code style="font-size:24px;font-weight:700;color:#22c55e;letter-spacing:3px;word-break:break-all;">${licenseKey}</code>
    </div>
    <p style="text-align:center;font-size:12px;color:#666;margin:0 0 24px;">Copy this key &mdash; you'll paste it into the desktop app to activate.</p>

    <!-- 48h Warning -->
    <div style="background:#7f1d1d20;border:1px solid #dc262640;border-radius:10px;padding:16px 20px;margin:0 0 28px;">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#f87171;">&#9200; 48-Hour Activation Required</p>
      <p style="margin:0;font-size:13px;color:#fca5a5;line-height:1.5;">
        You must activate this key within <strong>48 hours</strong> by installing the app and entering your key.
        Unclaimed keys are automatically reassigned to the next person on the waitlist.
      </p>
    </div>

    <!-- Quick Setup Steps -->
    <div style="background:#111;border:1px solid #ffffff10;border-radius:10px;padding:20px 24px;margin:0 0 28px;">
      <p style="margin:0 0 14px;font-size:15px;font-weight:700;color:#fff;">&#128203; Quick Setup (3 minutes)</p>
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="padding:8px 12px 8px 0;vertical-align:top;width:36px;">
            <span style="display:inline-block;width:24px;height:24px;background:#22c55e20;color:#22c55e;border-radius:50%;text-align:center;line-height:24px;font-size:12px;font-weight:700;">1</span>
          </td>
          <td style="padding:8px 0;font-size:14px;color:#d4d4d4;">
            <strong style="color:#fff;">Download</strong> the Hedge Edge desktop app for Windows
          </td>
        </tr>
        <tr>
          <td style="padding:8px 12px 8px 0;vertical-align:top;">
            <span style="display:inline-block;width:24px;height:24px;background:#22c55e20;color:#22c55e;border-radius:50%;text-align:center;line-height:24px;font-size:12px;font-weight:700;">2</span>
          </td>
          <td style="padding:8px 0;font-size:14px;color:#d4d4d4;">
            <strong style="color:#fff;">Enter your key</strong> when prompted during first launch
          </td>
        </tr>
        <tr>
          <td style="padding:8px 12px 8px 0;vertical-align:top;">
            <span style="display:inline-block;width:24px;height:24px;background:#22c55e20;color:#22c55e;border-radius:50%;text-align:center;line-height:24px;font-size:12px;font-weight:700;">3</span>
          </td>
          <td style="padding:8px 0;font-size:14px;color:#d4d4d4;">
            <strong style="color:#fff;">Download the MT5 EA</strong> and follow the setup guide below
          </td>
        </tr>
      </table>
    </div>

    <!-- Action Buttons -->
    <div style="text-align:center;margin:0 0 20px;">
      <a href="https://link.hedgedge.info/download-app" style="display:inline-block;background:#22c55e;color:#000;font-weight:700;text-decoration:none;padding:14px 28px;border-radius:10px;font-size:15px;margin:0 6px 8px;">&#11015; Download Desktop App</a>
      <a href="https://link.hedgedge.info/mt5-experts" style="display:inline-block;background:#1a1a1a;color:#22c55e;font-weight:600;text-decoration:none;padding:14px 28px;border-radius:10px;font-size:15px;border:1px solid #22c55e33;margin:0 6px 8px;">&#11015; Download MT5 EA</a>
    </div>

    <!-- Setup Guide Link -->
    <div style="text-align:center;background:#111;border:1px solid #ffffff10;border-radius:10px;padding:16px;margin:0 0 8px;">
      <p style="margin:0 0 6px;font-size:13px;color:#a3a3a3;">Need step-by-step instructions?</p>
      <a href="https://hedgedge.info/docs#welcome" style="color:#22c55e;font-size:15px;font-weight:600;text-decoration:underline;">&#128214; Full Setup Guide &amp; Documentation</a>
    </div>
  </div>

  <!-- Footer -->
  <div style="padding:20px 32px;border-top:1px solid #1a1a1a;text-align:center;">
    <p style="font-size:12px;color:#525252;margin:0 0 4px;">Need help? Reply to this email or visit <a href="https://hedgedge.info/support" style="color:#22c55e;">hedgedge.info/support</a></p>
    <p style="font-size:11px;color:#404040;margin:0;">Hedge Edge Ltd &bull; England &amp; Wales</p>
  </div>
</div>`;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method === "OPTIONS") {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "content-type");
    return res.status(200).end();
  }
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { email, name, utm } = req.body || {};
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: "Valid email is required" });
  }

  const ip =
    (req.headers["x-forwarded-for"] as string || "").split(",")[0].trim() ||
    req.socket?.remoteAddress ||
    "unknown";

  if (isEmailRateLimited(email.toLowerCase())) {
    return res.status(429).json({ error: "This email has already claimed a beta key. Check your inbox." });
  }
  if (isIpRateLimited(ip)) {
    return res.status(429).json({ error: "Too many requests. Please try again later." });
  }

  const RESEND_API_KEY = process.env.RESEND_API_KEY || "";
  if (!RESEND_API_KEY) {
    return res.status(500).json({ error: "Email service not configured" });
  }

  // Initialize Supabase
  const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "";
  const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
  if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
    return res.status(500).json({ error: "Database not configured" });
  }
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

  const normalizedEmail = email.toLowerCase().trim();

  // Check if this email already has an active key
  const { data: existingKey } = await supabase
    .from("licenses")
    .select("license_key")
    .eq("email", normalizedEmail)
    .eq("is_active", true)
    .limit(1)
    .maybeSingle();

  if (existingKey) {
    return res.status(429).json({ error: "This email already has an active beta key. Check your inbox." });
  }

  // Step 1: Find next available key from pool (oldest first = predictable order)
  const { data: available } = await supabase
    .from("licenses")
    .select("license_key")
    .eq("email", POOL_PLACEHOLDER)
    .eq("is_active", true)
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle();

  if (!available) {
    return res.status(503).json({
      error: "All beta slots are currently taken. Join our waitlist — we'll notify you when more spots open up."
    });
  }

  // Step 2: Atomic claim — WHERE email = placeholder prevents race conditions
  const claimTimestamp = new Date().toISOString();
  const { data: claimed, error: claimErr } = await supabase
    .from("licenses")
    .update({
      email: normalizedEmail,
      notes: JSON.stringify({
        claimed_at: claimTimestamp,
        first_name: ((name as string) || "").trim(),
        claimed_ip: ip,
      }),
      updated_at: claimTimestamp,
    })
    .eq("license_key", available.license_key)
    .eq("email", POOL_PLACEHOLDER) // fails if already claimed by someone else
    .select("license_key")
    .maybeSingle();

  if (claimErr || !claimed) {
    console.error("Claim failed (race or error):", claimErr);
    return res.status(503).json({
      error: "Beta slots are filling fast. Please try again."
    });
  }

  const licenseKey = claimed.license_key;
  const firstName = ((name || "Trader") as string).replace(/[<>&"']/g, "");

  try {
    const html = appendUnsubscribeHtml(buildKeyEmail(firstName, licenseKey), normalizedEmail);

    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from: "Hedge Edge <hello@hedgedge.info>",
        to: [normalizedEmail],
        reply_to: "reply@hedgedge.info",
        subject: "🔑 Your Beta Key — Activate Within 48 Hours",
        html,
        headers: buildUnsubscribeHeaders(normalizedEmail),
      }),
    });

    if (!r.ok) {
      const err = await r.text();
      console.error("Resend error:", r.status, err);
      // Revert claim — put key back in pool
      await supabase
        .from("licenses")
        .update({ email: POOL_PLACEHOLDER, notes: null, updated_at: new Date().toISOString() })
        .eq("license_key", licenseKey);
      return res.status(502).json({ error: "Failed to send email. Please try again." });
    }

    recordClaim(normalizedEmail, ip);

    // Write attribution (non-blocking)
    if (utm) {
      try {
        await supabase.from("user_attribution").insert({
          user_id: crypto.randomUUID(),
          utm_source: utm.utm_source || null,
          utm_medium: utm.utm_medium || null,
          utm_campaign: utm.utm_campaign || null,
          utm_content: utm.utm_content || null,
          utm_term: utm.utm_term || null,
          ref: normalizedEmail,
          landing_url: utm.landing_url || "/",
          landed_at: utm.landed_at || null,
          signup_method: "beta_email",
          signed_up_at: claimTimestamp,
        });
      } catch (attrErr) {
        console.warn("attribution write failed (non-blocking):", attrErr);
      }
    }

    return res.status(200).json({ success: true, message: "Beta key sent to your email!" });
  } catch (err) {
    console.error("claim-beta error:", err);
    return res.status(500).json({ error: "Internal server error" });
  }
}
