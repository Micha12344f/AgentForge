/**
 * Signup Attribution Writer
 *
 * Reads stored UTM params and writes a row to the user_attribution
 * table in Supabase. This creates a clean, queryable record of which
 * channel/campaign led to each signup.
 *
 * Primary attribution is written server-side by the /api/claim-beta
 * endpoint when a user claims beta access (email-based conversion).
 *
 * This client-side function is kept as a fallback for authenticated
 * signups (e.g. Google OAuth or email/password via AuthContext).
 */

import { supabase } from "./supabase";
import { getUtmParams, clearUtmParams } from "./utm";

const ATTRIBUTION_WRITTEN_KEY = "hedge_attribution_done";

/**
 * Write signup attribution for a newly registered user.
 * Reads UTM params from storage, INSERTs into user_attribution,
 * then clears the stored UTM to prevent duplicate writes.
 *
 * Safe to call multiple times  uses a localStorage flag to
 * ensure attribution is only written once per user.
 */
export async function writeAttribution(
  userId: string,
  signupMethod: "email" | "google"
): Promise<void> {
  try {
    // Guard: don't write attribution twice for the same user
    const doneKey = `${ATTRIBUTION_WRITTEN_KEY}_${userId}`;
    if (localStorage.getItem(doneKey)) return;

    const utm = getUtmParams();

    // Only write if we have at least some attribution data
    // (even direct visits get logged so we know they had no UTM)
    const row = {
      user_id: userId,
      utm_source: utm.utm_source || null,
      utm_medium: utm.utm_medium || null,
      utm_campaign: utm.utm_campaign || null,
      utm_content: utm.utm_content || null,
      utm_term: utm.utm_term || null,
      ref: utm.ref || null,
      landing_url: utm.landing_url || window.location.pathname,
      landed_at: utm.landed_at || null,
      signup_method: signupMethod,
      signed_up_at: new Date().toISOString(),
    };

    const { error } = await supabase
      .from("user_attribution")
      .insert(row);

    if (error) {
      console.warn("[attribution] insert failed:", error.message);
      return;
    }

    // Mark as done so we don't write again on subsequent page loads
    localStorage.setItem(doneKey, "true");

    // Clear UTM storage now that it's been persisted to the database
    clearUtmParams();

    console.log("[attribution] recorded:", {
      source: utm.utm_source || "(direct)",
      method: signupMethod,
    });
  } catch (err) {
    console.warn("[attribution] error:", err);
  }
}
