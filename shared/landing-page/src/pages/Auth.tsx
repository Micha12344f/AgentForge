import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { TrendingUp, Mail, Lock, User, ArrowLeft, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import PhoneInput from "@/components/ui/PhoneInput";
import { useAuth } from "../contexts/AuthContext";
import { supabase } from "@/lib/supabase";

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [isForgotPassword, setIsForgotPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Detect if we arrived with OAuth/verification tokens in the URL.
  // Supabase (detectSessionInUrl: true) handles them automatically;
  // we only use this flag to show a loading screen while it works.
  const [isProcessingAuth] = useState(() => {
    const hash = window.location.hash;
    const hasCode = new URLSearchParams(window.location.search).has("code");
    return hash.includes("access_token") || hasCode;
  });

  const {
    signIn, signUp, signInWithGoogle,
    user, loading: authLoading,
    isPasswordRecovery, clearPasswordRecovery,
  } = useAuth();
  const navigate = useNavigate();

  // Use context-level recovery flag (persisted in sessionStorage for refreshes)
  const showPasswordReset = isPasswordRecovery;

  // Check for success message from password reset redirect
  useEffect(() => {
    const authMessage = sessionStorage.getItem("authMessage");
    if (authMessage) {
      setMessage(authMessage);
      sessionStorage.removeItem("authMessage");
    }
    // Pick up error from OAuth guard (auto-signup blocked)
    const authError = sessionStorage.getItem("authError");
    if (authError) {
      setError(authError);
      sessionStorage.removeItem("authError");
    }
  }, []);

  // Handle error in URL hash (expired link, etc.) — Supabase won't surface these
  useEffect(() => {
    const hash = window.location.hash;
    if (hash && hash.includes("error=")) {
      const params = new URLSearchParams(hash.substring(1));
      const errorDesc = params.get("error_description");
      if (errorDesc) {
        const decoded = decodeURIComponent(errorDesc.replace(/\+/g, " "));
        if (decoded.toLowerCase().includes("invalid") || decoded.toLowerCase().includes("expired")) {
          setError("This reset link has expired or was already used. Please request a new one below.");
          setIsForgotPassword(true);
        } else {
          setError(decoded);
        }
      }
      window.history.replaceState(null, "", window.location.pathname);
    }
  }, []);

  // Redirect when user is authenticated — unless in password recovery
  useEffect(() => {
    if (user && !showPasswordReset) {
      navigate("/dashboard", { replace: true });
    }
  }, [user, navigate, showPasswordReset]);

  // Clear loading/message state when password reset form is ready to show
  useEffect(() => {
    if (showPasswordReset && user) {
      setLoading(false);
      setMessage(null);
    }
  }, [showPasswordReset, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    if (isLogin) {
      const { error } = await signIn(email, password);
      if (error) {
        setError(error.message);
      }
      // Always stop the button spinner — on success the useEffect will
      // detect `user` and navigate to dashboard.
      setLoading(false);
    } else {
      if (password.length < 6) {
        setError("Password must be at least 6 characters");
        setLoading(false);
        return;
      }
      const { error } = await signUp(email, password, name, phoneNumber);
      if (error) {
        // Supabase returns this when its built-in email service fails
        if (error.message.toLowerCase().includes("email") && error.message.toLowerCase().includes("send")) {
          setError("Unable to send confirmation email. Please try again in a few minutes, or try a different email provider.");
        } else if (error.message.toLowerCase().includes("database")) {
          setError("Account creation failed due to a server issue. Please try again or contact support.");
        } else {
          setError(error.message);
        }
        setLoading(false);
      } else {
        // Fire GA4 sign_up conversion event — gtag.js is loaded in index.html.
        // Because this runs in the same browser session as the tracked link click,
        // GA4 automatically attributes this signup to the UTM source (e.g. Twitter).
        if (typeof window.gtag === "function") {
          window.gtag("event", "sign_up", { method: "email" });
        }
        setMessage("Check your email for a confirmation link to activate your account.");
        setLoading(false);
      }
    }
  };

  const handleGoogleSignIn = async () => {
    setError(null);
    // Save whether the user is on the Login or Sign Up tab so we can
    // block auto-account-creation on the Login tab after the redirect.
    sessionStorage.setItem("oauth_intent", isLogin ? "login" : "signup");
    const { error } = await signInWithGoogle();
    if (error) {
      setError(error.message);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      setError("Please enter your email address");
      return;
    }
    setLoading(true);
    setError(null);
    setMessage(null);

    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/dashboard`,
    });

    if (error) {
      setError(error.message);
    } else {
      setMessage("Check your email for a password reset link.");
    }
    setLoading(false);
  };

  const handleSetNewPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      // The recovery session is already established on the main Supabase client
      // (Supabase auto-processed the recovery hash via detectSessionInUrl: true
      //  and fired PASSWORD_RECOVERY through onAuthStateChange).
      const { error: updateError } = await supabase.auth.updateUser({ password });

      if (updateError) {
        throw new Error(updateError.message);
      }

      // Success — clean up recovery state
      clearPasswordRecovery();
      // Remove legacy sessionStorage keys (from older code paths)
      sessionStorage.removeItem("recoveryAccessToken");
      sessionStorage.removeItem("recoveryRefreshToken");

      // Sign out so the user logs in fresh with the new password
      try { await supabase.auth.signOut(); } catch (_) { /* ignore */ }

      // Full page reload prevents Chrome from autofilling recovery password
      sessionStorage.setItem("authMessage", "Password updated! Please sign in with your new password.");
      window.location.href = "/dashboard";
    } catch (err: any) {
      setError(err.message || "Failed to update password. Please try again.");
      setLoading(false);
    }
  };

  // ── Full-page loading screen while Supabase processes OAuth / email tokens ──
  if (isProcessingAuth && authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-muted to-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <p className="text-muted-foreground">Signing you in…</p>
        </div>
      </div>
    );
  }

  // User is authenticated and about to be redirected — keep showing a spinner
  // so the login form never flashes.
  if (user && !showPasswordReset) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-muted to-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <p className="text-muted-foreground">Redirecting to dashboard…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted to-background flex flex-col">
      {/* Header */}
      <header className="p-4">
        <a href="/" className="inline-flex items-center gap-2 text-foreground hover:text-primary transition-colors">
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Home</span>
        </a>
      </header>

      {/* Auth Form */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="text-center mb-8">
            <a href="/" className="inline-flex items-center gap-2 text-3xl font-bold text-primary">
              <TrendingUp className="w-10 h-10" />
              <span>HedgeEdge</span>
            </a>
            <p className="text-muted-foreground mt-2">
              {showPasswordReset
                ? "Enter your new password"
                : isForgotPassword
                ? "Enter your email to reset your password"
                : isLogin
                ? "Welcome back! Sign in to your account"
                : "Create your account to get started"}
            </p>
          </div>

          {/* Form Card */}
          <div className="bg-card border border-primary/20 rounded-xl p-8 shadow-lg shadow-primary/5">
            {/* Toggle Tabs - hide for forgot password and password reset */}
            {!isForgotPassword && !showPasswordReset && (
              <div className="flex mb-6 bg-muted rounded-lg p-1">
                <button
                  onClick={() => { setIsLogin(true); setError(null); setMessage(null); }}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                    isLogin
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Log In
                </button>
                <button
                  onClick={() => { setIsLogin(false); setError(null); setMessage(null); }}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                    !isLogin
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Sign Up
                </button>
              </div>
            )}

            {/* Forgot Password Header */}
            {isForgotPassword && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-foreground">Reset Password</h2>
              </div>
            )}

            {/* Set New Password Header */}
            {showPasswordReset && (
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-foreground">Set New Password</h2>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-destructive shrink-0" />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Success Message */}
            {message && (
              <div className="mb-4 p-3 bg-primary/10 border border-primary/30 rounded-lg">
                <p className="text-sm text-primary">{message}</p>
              </div>
            )}

            {/* Set New Password Form */}
            {showPasswordReset ? (
              <form onSubmit={handleSetNewPassword} className="space-y-4" autoComplete="off">
                <div>
                  <label htmlFor="newPassword" className="block text-sm font-medium text-foreground mb-1.5">
                    New Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                      type="password"
                      id="newPassword"
                      name="new-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min. 6 characters"
                      autoComplete="new-password"
                      className="w-full pl-10 pr-4 py-3 bg-background border border-primary/20 rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                      required
                      minLength={6}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground mb-1.5">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                      type="password"
                      id="confirmPassword"
                      name="confirm-password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm your password"
                      autoComplete="new-password"
                      className="w-full pl-10 pr-4 py-3 bg-background border border-primary/20 rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                      required
                      minLength={6}
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90 py-3 text-base font-semibold disabled:opacity-50"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Updating Password...
                    </span>
                  ) : (
                    "Update Password"
                  )}
                </Button>
              </form>
            ) : (
            <form onSubmit={isForgotPassword ? handleForgotPassword : handleSubmit} className="space-y-4" autoComplete="on">
              {/* Name field (only for signup) */}
              {!isLogin && !isForgotPassword && (
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-foreground mb-1.5">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                      type="text"
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Enter your name"
                      className="w-full pl-10 pr-4 py-3 bg-background border border-primary/20 rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                      required={!isLogin}
                    />
                  </div>
                </div>
              )}

              {/* Phone Number field (only for signup, optional) */}
              {!isLogin && !isForgotPassword && (
                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-foreground mb-1.5">
                    Phone Number <span className="text-muted-foreground font-normal">(optional)</span>
                  </label>
                  <PhoneInput
                    id="phone"
                    value={phoneNumber}
                    onChange={setPhoneNumber}
                    placeholder="Phone number"
                  />
                </div>
              )}

              {/* Email field */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    autoComplete="email"
                    className="w-full pl-10 pr-4 py-3 bg-background border border-primary/20 rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                    required
                  />
                </div>
              </div>

              {/* Password field (hidden for forgot password) */}
              {!isForgotPassword && (
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-foreground mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                    <input
                      type="password"
                      id="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder={isLogin ? "Enter your password" : "Min. 6 characters"}
                      autoComplete={isLogin ? "current-password" : "new-password"}
                      className="w-full pl-10 pr-4 py-3 bg-background border border-primary/20 rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                      required
                      minLength={6}
                    />
                  </div>
                </div>
              )}

              {/* Forgot password link (only for login) */}
              {isLogin && !isForgotPassword && (
                <div className="text-right">
                  <button
                    type="button"
                    onClick={() => { setIsForgotPassword(true); setError(null); setMessage(null); }}
                    className="text-sm text-primary hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
              )}

              {/* Submit button */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 py-3 text-base font-semibold disabled:opacity-50"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {isForgotPassword ? "Sending..." : isLogin ? "Signing In..." : "Creating Account..."}
                  </span>
                ) : (
                  isForgotPassword ? "Send Reset Link" : isLogin ? "Sign In" : "Create Account"
                )}
              </Button>

              {/* Back to login link (only for forgot password) */}
              {isForgotPassword && (
                <div className="text-center mt-4">
                  <button
                    type="button"
                    onClick={() => { setIsForgotPassword(false); setError(null); setMessage(null); }}
                    className="text-sm text-primary hover:underline"
                  >
                    ← Back to Login
                  </button>
                </div>
              )}
            </form>
            )}

            {/* Divider - hide for forgot password and password reset */}
            {!isForgotPassword && !showPasswordReset && (
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-primary/20"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-card text-muted-foreground">or continue with</span>
                </div>
              </div>
            )}

            {/* Social login button - hide for forgot password and password reset */}
            {!isForgotPassword && !showPasswordReset && (
              <div className="flex justify-center">
                <button
                  onClick={handleGoogleSignIn}
                  type="button"
                  className="flex items-center justify-center gap-2 py-3 px-8 bg-background border border-primary/20 rounded-lg text-foreground hover:bg-muted transition-colors"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  <span className="text-sm font-medium">Google</span>
                </button>
              </div>
            )}
          </div>

          {/* cTrader promo */}
          <div className="mt-6 p-4 bg-primary/10 border border-primary/30 rounded-lg text-center">
            <p className="text-sm text-foreground">
              🎉 Join the wait for an <span className="font-semibold text-primary">elite hedgers tool</span> — available for all users!
            </p>
          </div>

          {/* Terms */}
          <p className="text-center text-xs text-muted-foreground mt-6">
            By continuing, you agree to our{" "}
            <a href="/terms-of-service" className="text-primary hover:underline">Terms of Service</a>
            {" "}and{" "}
            <a href="/privacy-policy" className="text-primary hover:underline">Privacy Policy</a>
          </p>
        </div>
      </div>
    </div>
  );
}
