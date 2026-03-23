import { createContext, useContext, useEffect, useState, useRef, type ReactNode } from "react";
import { supabase } from "@/lib/supabase";
import { getUtmParams } from "@/lib/utm";
import { writeAttribution } from "@/lib/attribution";
import type { User, Session } from "@supabase/supabase-js";

interface UserProfile {
  id: string;
  full_name: string | null;
  phone_number: string | null;
  license_key: string | null;
  license_tier: string | null;
  license_expires_at: string | null;
  license_status: string | null;
  creem_customer_id: string | null;
  creem_subscription_id: string | null;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: UserProfile | null;
  loading: boolean;
  isPasswordRecovery: boolean;
  clearPasswordRecovery: () => void;
  signUp: (email: string, password: string, fullName: string, phoneNumber?: string) => Promise<{ error: Error | null }>;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signInWithGoogle: () => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<{ error: string | null }>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPasswordRecovery, setIsPasswordRecovery] = useState(() => {
    return sessionStorage.getItem('passwordRecovery') === 'true';
  });
  const deletingAccountRef = useRef(false);

  const fetchProfile = async (userId: string) => {
    const { data, error } = await supabase
      .from("profiles")
      .select("*")
      .eq("id", userId)
      .single();

    if (error) {
      console.error("Error fetching profile:", error);
      return null;
    }
    return data as UserProfile;
  };

  const refreshProfile = async () => {
    if (user) {
      const p = await fetchProfile(user.id);
      setProfile(p);
    }
  };

  useEffect(() => {
    // Check if URL contains auth tokens that Supabase will process
    const hash = window.location.hash;
    const urlHasAuthTokens =
      hash.includes("access_token") ||
      new URLSearchParams(window.location.search).has("code");
    let receivedSessionEvent = false;

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      // If we're in the middle of deleting the account, ignore all auth events
      if (deletingAccountRef.current) return;

      // Detect password recovery event
      if (event === 'PASSWORD_RECOVERY') {
        setIsPasswordRecovery(true);
        sessionStorage.setItem('passwordRecovery', 'true');
      }

      // If URL has auth tokens and this is the initial load with no session,
      // don't set loading=false yet  Supabase will fire another event
      // after processing the URL tokens.
      if (
        urlHasAuthTokens &&
        !receivedSessionEvent &&
        event === 'INITIAL_SESSION' &&
        !session
      ) {
        // Skip  wait for the real session from URL token processing
        return;
      }
      receivedSessionEvent = true;

      if (session?.user) {
        // Only verify server-side on INITIAL_SESSION (catches deleted users
        // whose token is still in localStorage). For SIGNED_IN or TOKEN_REFRESHED
        // the session just came from the server, so it's guaranteed valid.
        let activeUser = session.user;

        if (event === 'INITIAL_SESSION') {
          const { data: { user: verifiedUser }, error: verifyError } = await supabase.auth.getUser();

          if (verifyError || !verifiedUser) {
            console.warn("Session invalid (user may have been deleted). Signing out.");
            setSession(null);
            setUser(null);
            setProfile(null);
            setLoading(false);
            await supabase.auth.signOut({ scope: 'local' });
            return;
          }
          activeUser = verifiedUser;
        }

        setSession(session);
        setUser(activeUser);

        // --- Guard: block auto-signup via Google on the Login tab ---
        // When a user clicks "Sign in with Google" on the Login tab, we
        // store oauth_intent=login. If the account was just created
        // (within the last 60 seconds), it means Google auto-created it
        // but the user only intended to log in. Delete it and show error.
        const oauthIntent = sessionStorage.getItem("oauth_intent");
        sessionStorage.removeItem("oauth_intent");

        if (oauthIntent === "login" && activeUser.created_at) {
          const createdAt = new Date(activeUser.created_at).getTime();
          const now = Date.now();
          const isNewAccount = (now - createdAt) < 60000; // created within last 60s

          if (isNewAccount) {
            console.warn("Blocked auto-signup via Google on login tab. Removing new account.");
            // Fire the delete RPC (fire-and-forget since it kills the session)
            const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || import.meta.env.NEXT_PUBLIC_SUPABASE_URL;
            const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
            if (supabaseUrl && session?.access_token) {
              fetch(`${supabaseUrl}/rest/v1/rpc/delete_own_account`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  "apikey": anonKey || "",
                  "Authorization": `Bearer ${session.access_token}`,
                },
                body: "{}",
              }).catch(() => {});
            }

            // Clear local session
            try {
              const keys = Object.keys(localStorage);
              for (const key of keys) {
                if (key.startsWith("sb-")) localStorage.removeItem(key);
              }
            } catch (_) {}

            setSession(null);
            setUser(null);
            setProfile(null);
            setLoading(false);

            // Redirect to homepage
            window.location.href = "/";
            return;
          }
        }
        // --- End guard ---

        // Fire GA4 sign_up event for new Google OAuth signups
        if (oauthIntent === "signup" && activeUser.created_at) {
          const createdAt = new Date(activeUser.created_at).getTime();
          if (Date.now() - createdAt < 60000) {
            if (typeof window.gtag === "function") {
              window.gtag("event", "sign_up", { method: "google" });
            }
          }
        }

        try {
          const p = await fetchProfile(activeUser.id);
          setProfile(p);

          // Self-heal: if user metadata has phone_number but profile doesn't, sync it
          const metaPhone = activeUser.user_metadata?.phone_number;
          if (p && !p.phone_number && metaPhone) {
            const { data: updated } = await supabase
              .from("profiles")
              .update({ phone_number: metaPhone })
              .eq("id", activeUser.id)
              .select()
              .single();
            if (updated) setProfile(updated as UserProfile);
          }

          // --- Signup Attribution ---
          // For new accounts (created within last 24 hours), write attribution
          // to the user_attribution table. The writeAttribution function is
          // idempotent  it checks localStorage to avoid duplicate writes.
          if (activeUser.created_at) {
            const accountAgeMs = Date.now() - new Date(activeUser.created_at).getTime();
            if (accountAgeMs < 86_400_000) { // account < 24 hours old
              const provider = activeUser.app_metadata?.provider || "email";
              const method = provider === "google" ? "google" as const : "email" as const;
              writeAttribution(activeUser.id, method);
            }
          }
          // --- End attribution ---

        } catch (err) {
          console.error("Error loading profile:", err);
          setProfile(null);
        }
      } else {
        setSession(null);
        setUser(null);
        setProfile(null);
      }

      setLoading(false);
    });

    // Safety timeout  if Supabase never responds, stop loading after 8s
    const timeout = setTimeout(() => {
      setLoading(false);
    }, 8000);

    return () => {
      subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, []);

  const clearPasswordRecovery = () => {
    setIsPasswordRecovery(false);
    sessionStorage.removeItem('passwordRecovery');
  };

  const signUp = async (email: string, password: string, fullName: string, phoneNumber?: string) => {
    const utm = getUtmParams();
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          phone_number: phoneNumber || null,
          ...(Object.keys(utm).length > 0 ? { utm } : {}),
        },
        emailRedirectTo: `${window.location.origin}/dashboard`,
      },
    });
    if (error) {
      console.error("signUp error:", error.message, error);
    } else {
      console.log("signUp success:", data);
    }
    return { error: error as Error | null };
  };

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { error: error as Error | null };
  };

  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/dashboard`,
        queryParams: {
          prompt: 'select_account',
        },
      },
    });
    return { error: error as Error | null };
  };

  const signOut = async () => {
    // Clear React state first
    setUser(null);
    setSession(null);
    setProfile(null);
    // Use 'local' scope so the session is removed from localStorage
    // even if the server-side revocation fails
    await supabase.auth.signOut({ scope: 'local' });
  };

  const deleteAccount = async (): Promise<{ error: string | null }> => {
    // Set the flag so onAuthStateChange doesn't interfere
    deletingAccountRef.current = true;

    const userId = user?.id;
    if (!userId) {
      deletingAccountRef.current = false;
      return { error: "No user session found" };
    }

    // Use raw fetch so we have full control over timeouts.
    // The Supabase client's .rpc() wraps fetch but doesn't let us
    // distinguish "function doesn't exist" (instant 404) from
    // "function ran and killed my session" (never resolves).
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || import.meta.env.NEXT_PUBLIC_SUPABASE_URL;
    const accessToken = session?.access_token;

    if (!supabaseUrl || !accessToken) {
      deletingAccountRef.current = false;
      return { error: "Missing session credentials" };
    }

    const controller = new AbortController();
    // If the function succeeds, it kills the session and the response
    // never arrives. 5 seconds is more than enough for the DB to process.
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch(`${supabaseUrl}/rest/v1/rpc/delete_own_account`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "apikey": import.meta.env.VITE_SUPABASE_ANON_KEY || import.meta.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "",
          "Authorization": `Bearer ${accessToken}`,
        },
        body: "{}",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      // If we get here, the response came back (function either errored or
      // didn't actually delete the user).
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const msg = body?.message || body?.error || `Server returned ${response.status}`;
        console.error("delete_own_account error:", msg);
        deletingAccountRef.current = false;
        return { error: msg };
      }

      // If 200/204, the function ran but somehow the session survived.
      // (Unlikely, but handle it.) Fall through to cleanup.
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        // Timeout = the request hung = the session was killed = success.
        // This is the EXPECTED path for a working deletion.
        console.log("delete_own_account: request timed out (expected  session was destroyed)");
      } else {
        console.error("delete_own_account fetch error:", err);
        deletingAccountRef.current = false;
        return { error: err?.message || "Network error during account deletion" };
      }
    }

    // Clean up localStorage directly (no Supabase API calls  they'd hang)
    try {
      const keys = Object.keys(localStorage);
      for (const key of keys) {
        if (key.startsWith("sb-")) localStorage.removeItem(key);
      }
    } catch (_) { /* ignore */ }

    // Clear React state
    setUser(null);
    setSession(null);
    setProfile(null);

    return { error: null };
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        loading,
        isPasswordRecovery,
        clearPasswordRecovery,
        signUp,
        signIn,
        signInWithGoogle,
        signOut,
        deleteAccount,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
