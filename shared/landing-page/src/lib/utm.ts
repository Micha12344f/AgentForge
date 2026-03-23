/**
 * UTM Parameter Utilities
 *
 * Captures UTM query-params on first landing and persists them in
 * BOTH sessionStorage (for SPA navigation) and localStorage (survives
 * browser close/reopen). On signup, these are read and written to
 * the user_attribution table.
 *
 * Storage keys:
 *   sessionStorage: "hedge_utm_params" (SPA session, first-touch wins)
 *   localStorage:   "hedge_utm_full"   (persistent, first-touch wins)
 *   localStorage:   "hedge_utm"        (set by index.html IIFE, simpler format)
 */

const UTM_KEYS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_content",
  "utm_term",
  "ref",          // custom referral tag used by HedgeEdge
] as const;

const SESSION_KEY = "hedge_utm_params";
const LOCAL_KEY   = "hedge_utm_full";
const LEGACY_KEY  = "hedge_utm";          // set by index.html IIFE

export interface UtmParams {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  ref?: string;
  landing_url?: string;
  landed_at?: string;
}

/**
 * Call once on app load. If the current URL has UTM params,
 * persist them to both sessionStorage AND localStorage (first-touch wins).
 */
/**
 * Known search engine hostnames → utm_source values.
 */
const SEARCH_ENGINES: Record<string, string> = {
  "google": "google",
  "bing": "bing",
  "duckduckgo": "duckduckgo",
  "yahoo": "yahoo",
  "baidu": "baidu",
  "yandex": "yandex",
};

/**
 * Referrer host → canonical utm_source + utm_medium.
 * Handles URL shorteners and social link proxies that obscure the true source.
 */
const REFERRER_NORMALIZATIONS: Record<string, { source: string; medium: string }> = {
  "t.co": { source: "twitter", medium: "social" },
  "l.facebook.com": { source: "facebook", medium: "social" },
  "lnkd.in": { source: "linkedin", medium: "social" },
  "www.linkedin.com": { source: "linkedin", medium: "social" },
  "youtube.com": { source: "youtube", medium: "social" },
  "www.youtube.com": { source: "youtube", medium: "social" },
  "youtu.be": { source: "youtube", medium: "social" },
  "reddit.com": { source: "reddit", medium: "social" },
  "www.reddit.com": { source: "reddit", medium: "social" },
};

/** Strip stray curly braces that corrupt GA4 / Supabase data. */
function sanitizeParam(val: string): string {
  return val.replace(/[{}]/g, "");
}

/** Extract hostname from a URL, or return null. */
function referrerHostname(): string | null {
  try {
    const ref = document.referrer;
    if (!ref) return null;
    const host = new URL(ref).hostname.toLowerCase();
    // Ignore self-referrals
    if (host === window.location.hostname) return null;
    return host;
  } catch {
    return null;
  }
}

export function captureUtmParams(): void {
  const params = new URLSearchParams(window.location.search);
  const utm: UtmParams = {};
  let hasAny = false;

  for (const key of UTM_KEYS) {
    const val = params.get(key);
    if (val) {
      (utm as any)[key] = sanitizeParam(val);
      hasAny = true;
    }
  }

  // ── Organic / referral fallback when no explicit UTM params ──
  if (!hasAny) {
    const host = referrerHostname();
    if (host) {
      // First: check known social link proxies / shorteners
      const normalized = REFERRER_NORMALIZATIONS[host];
      if (normalized) {
        utm.utm_source = normalized.source;
        utm.utm_medium = normalized.medium;
      } else {
        // Check search engines
        const engine = Object.keys(SEARCH_ENGINES).find((e) => host.includes(e));
        if (engine) {
          utm.utm_source = SEARCH_ENGINES[engine];
          utm.utm_medium = "organic";
        } else {
          utm.utm_source = host;
          utm.utm_medium = "referral";
        }
      }
      hasAny = true;
    }
  }

  if (hasAny) {
    utm.landing_url = window.location.pathname.replace(/\}+$/, "");
    utm.landed_at = new Date().toISOString();
    const json = JSON.stringify(utm);

    // sessionStorage: first-touch wins per session
    if (!sessionStorage.getItem(SESSION_KEY)) {
      sessionStorage.setItem(SESSION_KEY, json);
    }
    // localStorage: first-touch wins across sessions
    if (!localStorage.getItem(LOCAL_KEY)) {
      localStorage.setItem(LOCAL_KEY, json);
    }
  }
}

/**
 * Retrieve captured UTM params.
 * Priority: sessionStorage > localStorage (full) > localStorage (legacy IIFE)
 * Returns empty object if none found.
 */
export function getUtmParams(): UtmParams {
  try {
    // 1. Check sessionStorage (current session, set by captureUtmParams)
    const session = sessionStorage.getItem(SESSION_KEY);
    if (session) return JSON.parse(session);

    // 2. Check localStorage full format (persists across sessions)
    const local = localStorage.getItem(LOCAL_KEY);
    if (local) return JSON.parse(local);

    // 3. Check legacy localStorage from index.html IIFE
    const legacy = localStorage.getItem(LEGACY_KEY);
    if (legacy) {
      const parsed = JSON.parse(legacy);
      // Legacy format may have slightly different shape; normalize
      return {
        utm_source: parsed.utm_source || parsed.source,
        utm_medium: parsed.utm_medium || parsed.medium,
        utm_campaign: parsed.utm_campaign || parsed.campaign,
        utm_content: parsed.utm_content,
        utm_term: parsed.utm_term,
        ref: parsed.ref,
        landing_url: parsed.landing_url || parsed.page,
        landed_at: parsed.landed_at || parsed.ts,
      };
    }

    return {};
  } catch {
    return {};
  }
}

/**
 * Clear all stored UTM params after attribution has been written.
 * Prevents duplicate attribution on subsequent logins.
 */
export function clearUtmParams(): void {
  try {
    sessionStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(LOCAL_KEY);
    localStorage.removeItem(LEGACY_KEY);
  } catch {
    // Ignore storage errors
  }
}
