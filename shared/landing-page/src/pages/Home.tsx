import React, { useRef, useEffect, useState } from "react";
import { motion, useScroll, useTransform, animate, useReducedMotion } from "motion/react";
import {
  AlertCircle, TrendingUp, Wallet, BarChart3, Percent, Users,
  Zap, Shield, Activity, Link2, GitBranch,
  ArrowRight, X, Star, CheckCircle2, Loader2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { PricingCard } from "@/components/PricingCard";
import { SubscriptionAgreementModal } from "@/components/SubscriptionAgreementModal";
import { BetaAccessModal } from "@/components/BetaAccessModal";
import { tiersData } from "@/data/siteData";
import { cn } from "@/lib/utils";
import { getUtmParams, clearUtmParams } from "@/lib/utm";
import cert5percenters from "@/assets/cert-5percenters.png";
import certFtmo from "@/assets/cert-ftmo.png";
import certTopstep from "@/assets/cert-topstep.png";
import certAtf from "@/assets/cert-atf.png";
import vantageLogo from "@/assets/vantage-logo-new.png";
import blackbullLogo from "@/assets/blackbull-banner-new.png";
import mt4Logo from "@/assets/MT4-logo.png";
import mt5Logo from "@/assets/mt5-logo.png";
import cTraderLogo from "@/assets/ctrader-logo.png";
import tradovateLogo from "@/assets/tradovate-logo.png";
import ninjaTraderLogo from "@/assets/ninjatrader-logo.png";
import dxTradeLogo from "@/assets/dxtrade-logo.png";
import analyticsImg from "@/assets/analytics.png";
import pnlChartImg from "@/assets/PnL-chart.png";
import dashboardPreview from "@/assets/dashboard-preview.png";
import hedgeMapPreview from "@/assets/hedge-map-preview.png";
import howItWorksSvg from "@/assets/how-it-works.svg";
import howItWorksMobileSvg from "@/assets/how-it-works-mobile.svg";


/* ─── Floating Orb Background ─── */
function FloatingOrbs() {
  const prefersReduced = useReducedMotion();
  if (prefersReduced) return null;

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div
        className="absolute w-[700px] h-[700px] rounded-full opacity-[0.09]"
        style={{
          background: "radial-gradient(circle, hsl(120 100% 54%), transparent 70%)",
          top: "-15%", right: "-10%",
          transform: "translateZ(0)",
        }}
      />
      <div
        className="absolute w-[500px] h-[500px] rounded-full opacity-[0.07]"
        style={{
          background: "radial-gradient(circle, hsl(185 80% 55%), transparent 70%)",
          bottom: "10%", left: "-5%",
          transform: "translateZ(0)",
        }}
      />
      <div
        className="absolute w-[400px] h-[400px] rounded-full opacity-[0.05]"
        style={{
          background: "radial-gradient(circle, hsl(265 80% 60%), transparent 70%)",
          top: "40%", right: "20%",
          transform: "translateZ(0)",
        }}
      />
    </div>
  );
}

/* ─── Section Reveal Wrapper ─── */
function SectionReveal({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const prefersReduced = useReducedMotion();
  return (
    <motion.div
      initial={prefersReduced ? {} : { opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ─── Stagger Variants ─── */
const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 },
  },
};
const staggerItem = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};





/* ─── Animated Counter ─── */
function AnimatedNumber({ value, prefix = "", suffix = "" }: { value: number; prefix?: string; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;
          observer.disconnect();
          const count = { v: 0 };
          const controls = animate(count, { v: value }, {
            duration: 2,
            ease: "easeOut",
            onUpdate: () => setDisplay(Math.round(count.v)),
            onComplete: () => setDisplay(value),
          });
          return () => controls.stop();
        }
      },
      { threshold: 0, rootMargin: "200px" }
    );
    observer.observe(el);

    const fallback = setTimeout(() => {
      if (!hasAnimated.current) {
        hasAnimated.current = true;
        setDisplay(value);
      }
    }, 5000);

    return () => {
      observer.disconnect();
      clearTimeout(fallback);
    };
  }, [value]);

  return <span ref={ref}>{prefix}{display.toLocaleString()}{suffix}</span>;
}

/* ─── Grid Background ─── */
function GridBackground({ className = "" }: { className?: string }) {
  return (
    <div className={`absolute inset-0 grid-bg opacity-40 ${className}`}>
      <div className="absolute inset-0 scan-line overflow-hidden" />
    </div>
  );
}





/* ─── Live Dot ─── */
function LiveDot() {
  return (
    <span className="relative flex h-2.5 w-2.5">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary" />
    </span>
  );
}

/* ─── Particle Field Canvas ─── */
function ParticleField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const prefersReduced = useReducedMotion();

  useEffect(() => {
    if (prefersReduced) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      canvas.width = canvas.offsetWidth * dpr;
      canvas.height = canvas.offsetHeight * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();

    const particles: { x: number; y: number; vx: number; vy: number; r: number; a: number }[] = [];
    const count = 30;
    const w = () => canvas.offsetWidth;
    const h = () => canvas.offsetHeight;

    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * w(),
        y: Math.random() * h(),
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 1.5 + 0.5,
        a: Math.random() * 0.3 + 0.1,
      });
    }

    let lastTime = 0;
    const draw = (now: number) => {
      // Throttle to ~30fps
      if (now - lastTime < 33) {
        animId = requestAnimationFrame(draw);
        return;
      }
      lastTime = now;

      ctx.clearRect(0, 0, w(), h());
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = w();
        if (p.x > w()) p.x = 0;
        if (p.y < 0) p.y = h();
        if (p.y > h()) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(30, 255, 50, ${p.a})`;
        ctx.fill();
      }

      // Draw connection lines — only check nearby pairs
      for (let i = 0; i < count; i++) {
        for (let j = i + 1; j < count; j++) {
          const dx = particles[i].x - particles[j].x;
          if (dx > 120 || dx < -120) continue;
          const dy = particles[i].y - particles[j].y;
          if (dy > 120 || dy < -120) continue;
          const distSq = dx * dx + dy * dy;
          if (distSq < 14400) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(30, 255, 50, ${0.08 * (1 - Math.sqrt(distSq) / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      animId = requestAnimationFrame(draw);
    };

    draw(0);
    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, [prefersReduced]);

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" style={{ willChange: 'auto', transform: 'translateZ(0)' }} />;
}

/* ═══════════ MAIN HOME ═══════════ */
export default function Home() {

  const [showBanner, setShowBanner] = useState(true);
  const [isScrolled, setIsScrolled] = useState(false);
  const [isAnnualBilling, setIsAnnualBilling] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);
  const [showBetaModal, setShowBetaModal] = useState(false);
  const [pendingProductId, setPendingProductId] = useState<string | null>(null);
  const [pendingTierName, setPendingTierName] = useState("");
  const [pendingTierPrice, setPendingTierPrice] = useState("");

  // Email capture form state
  const [guideEmail, setGuideEmail] = useState("");
  const [guideLoading, setGuideLoading] = useState(false);
  const [guideSuccess, setGuideSuccess] = useState(false);
  const [guideError, setGuideError] = useState<string | null>(null);

  // Auto-fullscreen when user clicks play via Wistia JS API
  useEffect(() => {
    (window as any)._wq = (window as any)._wq || [];
    (window as any)._wq.push({
      id: "fnui5hp47h",
      onReady: (video: any) => {
        video.bind("play", () => {
          video.requestFullscreen();
        });
      },
    });
  }, []);

  const handleGuideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!guideEmail || guideLoading) return;
    setGuideLoading(true);
    setGuideError(null);
    setGuideSuccess(false);
    try {
      const resp = await fetch("/api/send-guide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: guideEmail }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setGuideError(data.error || "Something went wrong. Please try again.");
      } else {
        setGuideSuccess(true);
        setGuideEmail("");
      }
    } catch {
      setGuideError("Network error. Please check your connection and try again.");
    } finally {
      setGuideLoading(false);
    }
  };

  const handleCheckout = async () => {
    if (!pendingProductId || checkoutLoading) return;
    setShowSubscriptionModal(false);
    setCheckoutLoading(true);

    try {
      const resp = await fetch("/api/creem-checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: pendingProductId }),
      });
      if (!resp.ok) throw new Error("Checkout failed");
      const data = await resp.json();
      if (!data.checkout_url) throw new Error("No checkout URL returned");
      window.location.href = data.checkout_url;
    } catch {
      setCheckoutLoading(false);
      alert("Unable to start checkout. Please try again or contact support.");
    }
  };

  const [betaLoading, setBetaLoading] = useState(false);
  const [betaSuccess, setBetaSuccess] = useState(false);
  const [betaError, setBetaError] = useState<string | null>(null);

  const handleBetaAccept = async (email: string, firstName: string) => {
    setBetaLoading(true);
    setBetaError(null);
    try {
      const utm = getUtmParams();
      const resp = await fetch("/api/claim-beta", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name: firstName, utm }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setBetaError(data.error || "Failed to send. Please try again.");
        setBetaLoading(false);
        return;
      }
      setBetaSuccess(true);
      setBetaLoading(false);
      clearUtmParams();
      window.gtag?.("event", "sign_up", { method: "email", form: "beta_claim" });
    } catch {
      setBetaError("Network error. Please check your connection.");
      setBetaLoading(false);
    }
  };

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">

      {/* ─── Promo Banner ─── */}
      {showBanner && (
        <motion.div
          initial={{ y: -40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -40, opacity: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-primary/[0.06] via-primary/[0.03] to-primary/[0.06] backdrop-blur-md"
        >
          <div className="container mx-auto px-4 py-2.5 flex items-center justify-center gap-3 relative">
            <LiveDot />
            <button
              onClick={() => setShowBetaModal(true)}
              className="text-sm font-medium text-foreground/80 hover:text-foreground inline-flex items-center gap-1.5 group transition-colors"
            >
              🎉 Claim free Windows beta access <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button
              onClick={() => setShowBanner(false)}
              className="absolute right-4 p-1 hover:bg-white/10 rounded transition-colors"
              aria-label="Close banner"
            >
              <X className="w-4 h-4 text-foreground/60 hover:text-foreground/80" />
            </button>
          </div>
        </motion.div>
      )}

      {/* Spacer for fixed trial banner */}
      <div className={showBanner ? "h-[38px]" : ""} />

      {/* ─── Header ─── */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className={cn(
          "sticky z-40 transition-all duration-300 w-full",
          showBanner ? 'top-[38px]' : 'top-0',
          isScrolled
            ? "glass glass-border bg-background/80 backdrop-blur-md shadow-2xl py-3"
            : "bg-transparent border-b border-transparent py-3"
        )}
      >
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <a href="/" className="flex items-center gap-2.5 group">
                <div className="relative">
                  <TrendingUp className="w-7 h-7 text-primary" strokeWidth={2.5} />
                  <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                <span className="text-xl font-bold tracking-tight">
                  <span className="text-primary">Hedge</span>
                  <span className="text-foreground">Edge</span>
                </span>
              </a>
              <nav className="hidden md:flex items-center gap-1 font-mono uppercase">
                {[
                  { label: "// Features", target: "features" },
                  { label: "// How It Works", target: "how-it-works" },
                  { label: "// Pricing", target: "pricing" },
                  { label: "// Free Guide", target: "email-capture" },
                ].map((item) => (
                  <a
                    key={item.label}
                    href={`#${item.target}`}
                    onClick={(e) => {
                      e.preventDefault();
                      const el = document.getElementById(item.target);
                      if (el) {
                        const headerOffset = 80;
                        const y = el.getBoundingClientRect().top + window.scrollY - headerOffset;
                        window.scrollTo({ top: y, behavior: "smooth" });
                      }
                    }}
                    className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-white/[0.04] transition-colors"
                  >
                    {item.label}
                  </a>
                ))}

              </nav>
            </div>
            <div className="flex items-center gap-1 sm:gap-2">
              <Button asChild variant="outline" size="sm" className="rounded-lg border-white/10 hover:bg-white/[0.04] hover:border-primary/30 h-8 text-xs px-3 text-white/70 bg-transparent font-mono uppercase tracking-widest flex">
                <a href="/docs">Docs</a>
              </Button>
              <Button asChild variant="outline" size="sm" className="rounded-lg border-white/10 hover:bg-white/[0.04] hover:border-white/20 h-8 text-xs px-2 sm:px-3 text-white bg-transparent">
                <a href="https://discord.gg/yJvG9jkP9e" target="_blank" rel="noreferrer" className="flex items-center gap-1.5">
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                  </svg>
                  <span className="hidden sm:inline">Discord</span>
                </a>
              </Button>
              <div className="transition-transform hover:scale-[1.03] active:scale-[0.97]">
                <Button
                  size="sm"
                  onClick={() => setShowBetaModal(true)}
                  className="px-3 sm:px-4 h-8 text-xs font-semibold glow-green bg-primary/10 border border-primary/20 hover:bg-primary/20 rounded-none font-mono uppercase tracking-widest text-primary hover:text-primary/80 transition-colors"
                >
                  Claim Beta
                </Button>
              </div>
            </div>
          </div>
        </div>
      </motion.header>

      {/* ═══════════════════════════════════════════
          HERO SECTION — Immersive with particles
      ═══════════════════════════════════════════ */}
      <section className="relative min-h-[92vh] flex items-center overflow-hidden">
        <ParticleField />
        <FloatingOrbs />

        {/* Radial gradient spotlight — using radial-gradient instead of blur filter for GPU perf */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[700px] rounded-full" style={{ background: 'radial-gradient(circle, hsl(120 100% 54% / 0.06), transparent 70%)', transform: 'translate(-50%, -50%) translateZ(0)' }} />
        <div className="absolute top-[30%] left-[70%] -translate-x-1/2 -translate-y-1/2 w-[500px] h-[400px] rounded-full" style={{ background: 'radial-gradient(circle, hsl(185 80% 55% / 0.03), transparent 70%)', transform: 'translate(-50%, -50%) translateZ(0)' }} />

        {/* AHA MOMENT BACKGROUND CERTIFICATES */}
        <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden w-full h-full">
          {/* 5%ers (Top Left focus) - Positioned far top-left */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 0, filter: "drop-shadow(0 0 30px rgba(0,0,0,0.8)) grayscale(40%) saturate(80%) brightness(0.8)" }}
            animate={{ opacity: 0.4, scale: 0.85, y: -20, rotate: -15, filter: "drop-shadow(0 0 30px rgba(0,0,0,0.8)) grayscale(40%) saturate(80%) brightness(0.8)" }}
            whileHover={{ scale: 1.05, opacity: 1, x: 40, y: 30, rotate: -5, zIndex: 50, filter: "drop-shadow(0 0 40px rgba(0,0,0,0.9)) grayscale(0%) saturate(100%) brightness(1.1)" }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            className="absolute pointer-events-auto cursor-pointer p-4 w-[280px] z-10"
            style={{ top: "0%", left: "5%" }}
          >
            <img src={cert5percenters} alt="The 5%ers Certificate" className="w-full h-auto rounded-xl border border-white/10" />
          </motion.div>

          {/* ATF (Bottom Left focus) - Positioned far bottom-left */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 0, filter: "drop-shadow(0 0 30px rgba(0,0,0,0.8)) grayscale(40%) saturate(80%) brightness(0.8)" }}
            animate={{ opacity: 0.3, scale: 0.85, y: -10, rotate: -12, filter: "drop-shadow(0 0 30px rgba(0,0,0,0.8)) grayscale(40%) saturate(80%) brightness(0.8)" }}
            whileHover={{ scale: 1.05, opacity: 1, x: 80, y: -40, rotate: 0, zIndex: 50, filter: "drop-shadow(0 0 40px rgba(0,0,0,0.9)) grayscale(0%) saturate(100%) brightness(1.1)" }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            className="absolute pointer-events-auto cursor-pointer p-4 w-[250px] z-0"
            style={{ bottom: "15%", left: "calc(-60px - 5%)" }}
          >
            <img src={certAtf} alt="ATF Certificate" className="w-full h-auto rounded-xl border border-white/10" />
          </motion.div>

          {/* FTMO (Top Right focus) - Positioned far top-right */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 0, filter: "drop-shadow(0 0 30px rgba(0,0,0,0.8)) grayscale(40%) saturate(80%) brightness(0.8)" }}
            animate={{ opacity: 0.4, scale: 0.85, y: -20, rotate: 15, filter: "drop-shadow(0 0 30px rgba(0,0,0,0.8)) grayscale(40%) saturate(80%) brightness(0.8)" }}
            whileHover={{ scale: 1.05, opacity: 1, x: -60, y: 30, rotate: 0, zIndex: 50, filter: "drop-shadow(0 0 40px rgba(0,0,0,0.9)) grayscale(0%) saturate(100%) brightness(1.1)" }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            className="absolute pointer-events-auto cursor-pointer p-4 w-[280px] z-10"
            style={{ top: "30%", right: "5%" }}
          >
            <img src={certFtmo} alt="FTMO Certificate" className="w-full h-auto rounded-xl border border-white/10" />
          </motion.div>

          {/* Topstep (Bottom Right focus) - Positioned far bottom-right */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 0, filter: "drop-shadow(0 0 30px rgba(0,0,0,0.8)) grayscale(40%) saturate(80%) brightness(0.8)" }}
            animate={{ opacity: 0.3, scale: 0.85, y: -10, rotate: 15, filter: "drop-shadow(0 0 30px rgba(0,0,0,0.8)) grayscale(40%) saturate(80%) brightness(0.8)" }}
            whileHover={{ scale: 1.05, opacity: 1, x: -80, y: -40, rotate: 0, zIndex: 50, filter: "drop-shadow(0 0 40px rgba(0,0,0,0.9)) grayscale(0%) saturate(100%) brightness(1.1)" }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            className="absolute pointer-events-auto cursor-pointer p-4 w-[250px] z-10"
            style={{ bottom: "-5%", right: "calc(-60px - 3%)" }}
          >
            <img src={certTopstep} alt="Topstep Certificate" className="w-full h-auto rounded-xl border border-white/10" />
          </motion.div>
        </div>

        <div className="container mx-auto px-4 relative z-10">
          <div className="flex flex-col items-center justify-center text-center pt-20 pb-4">

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="text-4xl sm:text-5xl lg:text-[4rem] xl:text-[4.5rem] font-bold tracking-tight leading-[1.08] mb-6 max-w-5xl mx-auto"
            >
              Unlock Prop Firm <span className="text-glow-gold-outline">Payouts</span> <br /><span className="text-primary text-glow">using math, not luck.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.65, duration: 0.6 }}
              className="text-base lg:text-lg text-muted-foreground leading-relaxed mb-10 max-w-2xl mx-auto"
            >
              Learn the proven, math-driven approach that nobody knows about, yet generates consistent prop firm payouts.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.5 }}
              className="flex justify-center flex-col items-center gap-6 mb-16 relative w-full"
            >
              {/* AHA MOMENT BACKGROUND CERTIFICATES (Interactive Group) */}
              {/* Certificates moved to outer hero section bounds */}

              <div className="flex justify-center flex-wrap gap-4 relative z-20 w-full mt-2 group">
                <div className="tech-bracket transition-transform hover:scale-[1.03] active:scale-[0.95] bg-background/80 backdrop-blur-md rounded-none relative z-20 shadow-[0_0_100px_rgba(0,0,0,0.8)]">
                  <Button asChild size="lg" className="px-10 h-14 text-sm font-semibold glow-green bg-primary/10 border border-primary/20 hover:bg-primary/20 rounded-none font-mono uppercase tracking-wider text-primary hover:text-primary/80 transition-colors">
                    <a href="#email-capture" className="flex items-center gap-2 justify-center w-full h-full relative z-30">
                      Get Free Guide <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                    </a>
                  </Button>
                </div>
              </div>

              {/* Trustpilot-style Social Proof (Inspired by FTMO) */}
              <div className="flex items-center gap-3 bg-white/[0.02] border border-white/[0.05] px-4 py-2 rounded-full backdrop-blur-sm">
                <div className="flex gap-0.5 text-green-500">
                  <Star className="w-4 h-4 fill-green-500" />
                  <Star className="w-4 h-4 fill-green-500" />
                  <Star className="w-4 h-4 fill-green-500" />
                  <Star className="w-4 h-4 fill-green-500" />
                  <Star className="w-4 h-4 fill-green-500" />
                </div>
                <span className="text-sm font-medium text-muted-foreground"><span className="text-foreground">4.8/5</span> from 1,250+ Traders</span>
              </div>
            </motion.div>

            {/* AHA MOMENT VIDEO */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9, duration: 0.9, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="w-full max-w-5xl mx-auto relative z-20 mb-8"
            >
              <div
                className="relative w-full rounded-none tech-bracket glow-green border border-white/[0.08] bg-black/50"
                style={{ boxShadow: "0 0 60px rgba(0, 255, 128, 0.15)" }}
              >
                <div className="flex items-center justify-between px-4 py-2 bg-white/[0.02] border-b border-white/[0.08]">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
                  </div>
                  <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest">// INITIALIZATION_PREVIEW.MP4</span>
                </div>
                <div className="wistia_responsive_padding" style={{ padding: "56.25% 0 0 0", position: "relative", background: "#000" }}>
                  <div className="wistia_responsive_wrapper" style={{ height: "100%", left: 0, position: "absolute", top: 0, width: "100%" }}>
                    <div className="wistia_embed wistia_async_fnui5hp47h videoFoam=true" style={{ height: "100%", position: "relative", width: "100%" }}>
                      <div className="wistia_swatch" style={{ height: "100%", left: 0, opacity: 0, overflow: "hidden", position: "absolute", top: 0, transition: "opacity 200ms", width: "100%" }}>
                        <img
                          src="https://fast.wistia.com/embed/medias/fnui5hp47h/swatch"
                          style={{ filter: "blur(5px)", height: "100%", objectFit: "contain", width: "100%" }}
                          alt=""
                          aria-hidden="true"
                          onLoad={(e) => { (e.target as HTMLElement).parentElement!.style.opacity = "1"; }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>


          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent pointer-events-none" />
      </section >

      {/* ═══════════════════════════════════════════
          WALL OF TRUST (SOCIAL PROOF)
      ═══════════════════════════════════════════ */}
      <section className="relative py-12 border-b border-white/[0.04] bg-background z-20">
        <div className="container mx-auto px-4 mb-8">
          <SectionReveal className="text-center">
            <p className="text-xs font-mono text-muted-foreground tracking-widest uppercase">// OPEN YOUR HEDGE ACCOUNT TODAY TO RECYCLE CHALLENGE FEES</p>
          </SectionReveal>
        </div>
        <div className="relative overflow-hidden w-full max-w-7xl mx-auto">
          <div className="pointer-events-none absolute inset-y-0 left-0 w-24 z-10 bg-gradient-to-r from-background to-transparent" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-24 z-10 bg-gradient-to-l from-background to-transparent" />

          <div className="marquee-track flex gap-8 md:gap-16 items-center">
            {[0, 1].map((half) => (
              <div key={half} className="flex items-center gap-8 md:gap-16 flex-shrink-0" aria-hidden={half === 1}>
                {[...Array(3)].map((_, i) => (
                  <React.Fragment key={i}>
                    <a href="https://link.hedgedge.info/vantage-signup" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center">
                      <img src={vantageLogo} alt="Vantage" className="h-[270px] md:h-[350px] w-auto opacity-50 grayscale hover:grayscale-0 hover:opacity-100 transition-all hover:scale-105 cursor-pointer object-contain" />
                    </a>
                    <a href="https://link.hedgedge.info/blackbull-signup" target="_blank" rel="noopener noreferrer" className="flex items-center justify-center">
                      <img src={blackbullLogo} alt="BlackBull Markets" className="h-[50px] md:h-[70px] w-auto opacity-50 grayscale hover:grayscale-0 hover:opacity-100 transition-all hover:scale-105 cursor-pointer object-contain" />
                    </a>
                  </React.Fragment>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section >

      {/* ═══════════════════════════════════════════
          SECTION 1 — DASHBOARD OVERVIEW
      ═══════════════════════════════════════════ */}
      <section id="features" className="relative py-28 overflow-hidden section-glow-green">
        <div className="absolute inset-0 dot-grid opacity-30" />

        <div className="container mx-auto px-4 relative z-10">
          <SectionReveal>
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 border border-primary/20">
                <span className="text-xs font-bold text-primary">01</span>
              </div>
              <span className="text-xs font-semibold text-primary tracking-[0.2em] uppercase">Dashboard Overview</span>
            </div>
          </SectionReveal>

          <div className="grid lg:grid-cols-[5fr_8fr] gap-16 items-center">
            <SectionReveal>
              <h2 className="text-3xl md:text-4xl lg:text-[2.75rem] font-bold mb-6 leading-tight tracking-tight">
                Your Trading{" "}
                <span className="text-primary text-glow">Command Center</span>
              </h2>
              <p className="text-base text-muted-foreground mb-10 leading-relaxed max-w-md">
                Track all prop firm accounts, monitor P&L, and manage hedge positions in one powerful dashboard.
              </p>

              <motion.div
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-60px" }}
                className="grid grid-cols-2 gap-3 mb-10"
              >
                {[
                  { icon: Wallet, title: "Prop Balance", desc: "Track total across firms" },
                  { icon: BarChart3, title: "Live P&L", desc: "Real-time profit tracking" },
                  { icon: Percent, title: "Drawdown Monitor", desc: "Stay within limits" },
                  { icon: Users, title: "Multi-Account", desc: "Evaluation, Funded, Hedge" },
                ].map(({ icon: Icon, title, desc }) => (
                  <motion.div
                    key={title}
                    variants={staggerItem}
                    whileHover={{ y: -3, transition: { duration: 0.2 } }}
                    className="group p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-primary/20 hover:bg-white/[0.04] transition-all"
                  >
                    <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center mb-3 group-hover:glow-green transition-shadow">
                      <Icon className="w-4 h-4 text-primary" />
                    </div>
                    <p className="font-semibold text-sm mb-0.5">{title}</p>
                    <p className="text-xs text-muted-foreground">{desc}</p>
                  </motion.div>
                ))}
              </motion.div>

              <div className="flex gap-10 pt-6 border-t border-white/[0.06]">
                {[
                  { value: 20, suffix: "+", label: "Prop Firms" },
                  { label: "Real-time Sync", raw: "24/7" },
                  { value: 500, suffix: "+", label: "Beta Users" },
                ].map((stat) => (
                  <div key={stat.label}>
                    <p className="text-2xl font-bold text-primary">
                      {stat.raw ?? <AnimatedNumber value={stat.value!} suffix={stat.suffix!} />}
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">{stat.label}</p>
                  </div>
                ))}
              </div>
            </SectionReveal>

            <SectionReveal className="relative">
              <div className="absolute -inset-6 bg-primary/[0.03] rounded-3xl blur-3xl" />

              <motion.div
                whileHover={{ y: -4 }}
                transition={{ type: "spring", stiffness: 200, damping: 25 }}
                className="relative gradient-border rounded-2xl overflow-hidden glow-green"
              >
                <img
                  src={dashboardPreview}
                  alt="Hedge Edge dashboard showing Total P&L, Assets Under Management, ROI, and account cards"
                  className="w-full h-auto block"
                  loading="lazy"
                />
              </motion.div>
            </SectionReveal>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          SECTION 2 — HEDGE MAP VISUALIZATION
      ═══════════════════════════════════════════ */}
      <section className="relative py-28 overflow-hidden section-glow-cyan">
        <GridBackground className="opacity-20" />

        <div className="container mx-auto px-4 relative z-10">
          <SectionReveal>
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 border border-primary/20">
                <span className="text-xs font-bold text-primary">02</span>
              </div>
              <span className="text-xs font-semibold text-primary tracking-[0.2em] uppercase">Visual Hedge Mapping</span>
            </div>
          </SectionReveal>

          <div className="grid lg:grid-cols-[8fr_5fr] gap-16 items-center">
            <SectionReveal className="relative">
              <div className="absolute -inset-6 bg-cyan-500/[0.02] rounded-3xl blur-3xl" />

              <motion.div
                whileHover={{ y: -4 }}
                transition={{ type: "spring", stiffness: 200, damping: 25 }}
                className="relative gradient-border rounded-2xl overflow-hidden glow-cyan"
              >
                <img
                  src={hedgeMapPreview}
                  alt="Visual hedge mapping showing broker accounts connected to prop firm challenges"
                  className="w-full h-auto block"
                  loading="lazy"
                />
              </motion.div>
            </SectionReveal>

            <SectionReveal>
              <h2 className="text-3xl md:text-4xl lg:text-[2.75rem] font-bold mb-6 leading-tight tracking-tight">
                See Your <span className="text-primary text-glow">Connections</span> at a Glance
              </h2>
              <p className="text-base text-muted-foreground mb-10 leading-relaxed max-w-md">
                Our interactive hedge map visualizes exactly how your broker accounts connect to your prop firm challenges.
              </p>

              <motion.div
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-60px" }}
                className="space-y-4"
              >
                {[
                  { icon: Link2, title: "Visual Pair Linking", desc: "See which hedge pairs with which challenge" },
                  { icon: GitBranch, title: "Multi-Pair Support", desc: "One hedge to multiple evaluations" },
                  { icon: Activity, title: "Real-time Status", desc: "Live connection indicators" },
                ].map(({ icon: Icon, title, desc }) => (
                  <motion.div key={title} variants={staggerItem} className="flex items-start gap-4 group">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0 group-hover:glow-green transition-shadow">
                      <Icon className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm mb-0.5">{title}</h4>
                      <p className="text-xs text-muted-foreground">{desc}</p>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </SectionReveal>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          SECTION 3 — ANALYTICS
      ═══════════════════════════════════════════ */}
      <section className="relative py-28 overflow-hidden section-glow-purple">
        <div className="absolute inset-0 dot-grid opacity-20" />

        <div className="container mx-auto px-4 relative z-10">
          <SectionReveal>
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 border border-primary/20">
                <span className="text-xs font-bold text-primary">03</span>
              </div>
              <span className="text-xs font-semibold text-primary tracking-[0.2em] uppercase">Performance Analytics</span>
            </div>
          </SectionReveal>

          <div className="grid lg:grid-cols-[5fr_8fr] gap-16 items-center">
            <SectionReveal>
              <h2 className="text-3xl md:text-4xl lg:text-[2.75rem] font-bold mb-6 leading-tight tracking-tight">
                Every Metric,{" "}
                <span className="text-primary text-glow">One Dashboard</span>
              </h2>
              <p className="text-base text-muted-foreground mb-10 leading-relaxed max-w-md">
                Complete breakdown of your hedging performance. From total P&L to hedge accuracy.
              </p>

              <motion.div
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-60px" }}
                className="grid grid-cols-2 gap-3"
              >
                {[
                  { icon: Wallet, title: "Total P&L", desc: "Real profit across all accounts" },
                  { icon: Shield, title: "Hedge P&L", desc: "Track hedge recovery amount" },
                  { icon: BarChart3, title: "Payouts & ROI", desc: "Returns as a percentage" },
                  { icon: Percent, title: "Hedge Accuracy", desc: "Spot slippage and gaps" },
                ].map(({ icon: Icon, title, desc }) => (
                  <motion.div
                    key={title}
                    variants={staggerItem}
                    whileHover={{ y: -3 }}
                    className="group p-4 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-primary/20 hover:bg-white/[0.04] transition-all"
                  >
                    <Icon className="w-4 h-4 text-primary mb-2.5" />
                    <h4 className="font-semibold text-xs mb-1">{title}</h4>
                    <p className="text-[10px] text-muted-foreground leading-relaxed">{desc}</p>
                  </motion.div>
                ))}
              </motion.div>
            </SectionReveal>

            <SectionReveal className="relative">
              <div className="absolute -inset-4 bg-primary/[0.06] rounded-3xl blur-3xl" />
              <motion.div
                whileHover={{ y: -4 }}
                transition={{ type: "spring", stiffness: 200, damping: 25 }}
              >
                <img
                  src={analyticsImg}
                  alt="HedgeEdge Analytics Dashboard"
                  className="relative w-full h-auto rounded-2xl glow-green border border-white/[0.08]"
                  style={{ filter: "contrast(1.1) brightness(1.05)" }}
                />
              </motion.div>
            </SectionReveal>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          SECTION 4 — P&L CHART
      ═══════════════════════════════════════════ */}
      <section className="relative py-28 overflow-hidden section-glow-green">
        <GridBackground className="opacity-15" />

        <div className="container mx-auto px-4 relative z-10">
          <SectionReveal>
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/10 border border-primary/20">
                <span className="text-xs font-bold text-primary">04</span>
              </div>
              <span className="text-xs font-semibold text-primary tracking-[0.2em] uppercase">P&L Tracking</span>
            </div>
          </SectionReveal>

          <div className="grid lg:grid-cols-[8fr_5fr] gap-16 items-center">
            <SectionReveal className="relative order-2 lg:order-1">
              <div className="absolute -inset-4 bg-primary/[0.06] rounded-3xl blur-3xl" />
              <motion.div
                whileHover={{ y: -4 }}
                transition={{ type: "spring", stiffness: 200, damping: 25 }}
              >
                <img
                  src={pnlChartImg}
                  alt="HedgeEdge P&L Chart"
                  className="relative w-full h-auto rounded-2xl glow-green border border-white/[0.08]"
                  style={{ filter: "contrast(1.1) brightness(1.05)" }}
                />
              </motion.div>
            </SectionReveal>

            <SectionReveal className="order-1 lg:order-2">
              <h2 className="text-3xl md:text-4xl lg:text-[2.75rem] font-bold mb-6 leading-tight tracking-tight">
                Watch Your{" "}
                <span className="text-primary text-glow">Recovery</span> in Real Time
              </h2>
              <p className="text-base text-muted-foreground mb-10 leading-relaxed max-w-md">
                Clear visual of how your hedge account recovers challenge fees. See exactly when your hedge kicks in.
              </p>

              <motion.div
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-60px" }}
                className="space-y-4"
              >
                {[
                  { icon: TrendingUp, title: "Equity Curve", desc: "Prop and hedge P&L side by side" },
                  { icon: Zap, title: "Fee Recovery", desc: "Know exactly how much recovered" },
                  { icon: BarChart3, title: "Performance History", desc: "Identify patterns and refine" },
                ].map(({ icon: Icon, title, desc }) => (
                  <motion.div key={title} variants={staggerItem} className="flex items-start gap-4 group">
                    <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center flex-shrink-0 group-hover:glow-green transition-shadow">
                      <Icon className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm mb-0.5">{title}</h4>
                      <p className="text-xs text-muted-foreground">{desc}</p>
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </SectionReveal>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          HOW IT WORKS
      ═══════════════════════════════════════════ */}
      <section id="how-it-works" className="relative pt-6 pb-10 md:pt-12 md:pb-20 bg-[#0a0d0e] border-y border-white/[0.05]">
        <div className="container mx-auto px-1 sm:px-4 relative z-10 max-w-6xl">
          {/* Mobile: optimized vertical layout */}
          <img src={howItWorksMobileSvg} alt="How it Works - 3 Step Hedge Strategy" className="block md:hidden h-auto object-contain mx-auto w-full" style={{ filter: 'drop-shadow(0 4px 20px rgba(0,0,0,0.3))' }} />
          {/* Desktop: original horizontal layout */}
          <img src={howItWorksSvg} alt="How it Works - 3 Step Hedge Strategy" className="hidden md:block h-auto object-contain mx-auto min-w-[600px] w-full" style={{ filter: 'drop-shadow(0 4px 20px rgba(0,0,0,0.3))' }} />
        </div>
      </section>



      {/* ═══════════════════════════════════════════
          PRICING
      ═══════════════════════════════════════════ */}
      < section id="pricing" className="relative py-28 overflow-hidden" >
        <div className="absolute inset-0 dot-grid opacity-20" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/[0.02] to-transparent" />

        <div className="container mx-auto px-4 relative z-10">
          <SectionReveal className="text-center mb-16">
            <span className="text-xs font-mono font-semibold text-muted-foreground tracking-[0.2em] uppercase block mb-3">// Pricing Protocol</span>
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4 max-w-2xl mx-auto">
              Challenge Fee <span className="text-primary text-glow">Insurance</span>
            </h2>
            <p className="text-sm text-muted-foreground max-w-lg mx-auto mb-4">
              The average prop firm challenge costs $300–$600. Hedge Edge pays for itself with just one successful hedge recovery.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-none tech-bracket bg-primary/10 border border-primary/20">
              <p className="text-xs text-primary font-mono tracking-wide">RECOVER 90%+ OF FAILED CHALLENGE FEES</p>
            </div>
          </SectionReveal>

          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-60px" }}
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 max-w-5xl mx-auto items-stretch"
          >
            {tiersData.map((tier) => (
              <motion.div key={tier.name} variants={staggerItem} className="flex">
                <PricingCard
                  {...tier}
                  isAnnual={false}
                  onCtaClick={(tier as any).creemProductId
                    ? () => {
                        setPendingProductId(
                          isAnnualBilling
                            ? (tier as any).creemAnnualProductId
                            : (tier as any).creemProductId
                        );
                        setPendingTierName(tier.name);
                        setPendingTierPrice(isAnnualBilling ? (tier as any).annualPrice : tier.monthlyPrice);
                        setShowSubscriptionModal(true);
                      }
                    : (tier as any).betaTag
                    ? () => setShowBetaModal(true)
                    : undefined}
                />
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section >

      {/* ═══════════════════════════════════════════
          FINAL CTA
      ═══════════════════════════════════════════ */}
      < section id="email-capture" className="relative py-28 overflow-hidden z-10" >
        <div className="absolute inset-0 bg-primary/[0.02]" />

        <div className="container mx-auto px-4">
          <SectionReveal className="text-center max-w-4xl mx-auto relative tech-bracket glass border border-white/[0.08] p-10 md:p-16 overflow-hidden">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1/2 bg-primary/20 blur-[100px] pointer-events-none" />

            <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 relative z-10">
              Get Your <span className="text-primary text-glow">Free Hedge Guide</span>
            </h2>
            <p className="text-base text-muted-foreground mb-10 max-w-2xl mx-auto relative z-10">
              Join leading traders who don't rely on luck. Learn the definitive mathematical approach to turning failed evaluations into guaranteed refunds today.
            </p>

            {guideSuccess ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center gap-4 relative z-20"
              >
                <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-primary" />
                </div>
                <p className="text-lg font-semibold text-foreground">Guide sent! Check your email 📬</p>
                <p className="text-sm text-muted-foreground">Can't find it? Check your spam folder.</p>
                <button
                  onClick={() => setGuideSuccess(false)}
                  className="text-xs text-primary hover:underline mt-2"
                >
                  Send to another email
                </button>
              </motion.div>
            ) : (
              <>
                <form onSubmit={handleGuideSubmit} className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-xl mx-auto relative z-20">
                  <input
                    type="email"
                    required
                    value={guideEmail}
                    onChange={(e) => setGuideEmail(e.target.value)}
                    placeholder="Enter your email address"
                    disabled={guideLoading}
                    className="w-full h-14 px-6 bg-black/40 border border-white/10 text-foreground placeholder-muted-foreground font-mono text-sm focus:outline-none focus:border-primary/50 transition-colors rounded-none outline-none disabled:opacity-50"
                  />
                  <motion.div whileHover={{ scale: guideLoading ? 1 : 1.02 }} whileTap={{ scale: guideLoading ? 1 : 0.98 }} className="w-full sm:w-auto flex-shrink-0 relative group">
                    <div className="absolute -inset-2 bg-primary/20 blur-xl rounded-full opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
                    <Button type="submit" size="lg" disabled={guideLoading} className="w-full relative bg-primary/10 hover:bg-primary/20 text-primary hover:text-primary-foreground h-14 px-10 text-sm sm:text-lg font-bold glow-green rounded-none font-mono uppercase tracking-widest border border-primary/50 transition-all duration-300 shadow-[0_0_20px_rgba(30,255,50,0.1)] group-hover:shadow-[0_0_30px_rgba(30,255,50,0.3)] disabled:opacity-50">
                      {guideLoading ? (
                        <span className="flex items-center gap-2">
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Sending...
                        </span>
                      ) : (
                        "Send Guide"
                      )}
                    </Button>
                  </motion.div>
                </form>
                {guideError && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-sm text-red-400 mt-4 relative z-20"
                  >
                    {guideError}
                  </motion.p>
                )}
              </>
            )}
          </SectionReveal>
        </div>
      </section >

      {/* ═══════════════════════════════════════════
          FOOTER + DISCLOSURE
      ═══════════════════════════════════════════ */}
      <footer className="pt-20 pb-10 px-4 border-t border-white/[0.04] bg-background">
        <div className="container mx-auto">
          <div className="grid md:grid-cols-12 gap-12 lg:gap-8 mb-16">
            {/* Brand Column */}
            <div className="md:col-span-5 lg:col-span-4">
              <div className="flex items-center gap-2 mb-6">
                <TrendingUp className="w-6 h-6 text-primary glow-green" strokeWidth={2.5} />
                <span className="text-xl font-bold tracking-tight uppercase font-mono">
                  <span className="text-primary">Hedge</span>
                  <span className="text-foreground">Edge</span>
                </span>
              </div>
              <p className="text-muted-foreground text-sm max-w-[280px] mb-8 leading-relaxed">
                The leading risk mitigation protocol for funded traders. Reclaim your capital with precision-engineered hedging software.
              </p>

              <div className="flex gap-4">
                <a href="https://discord.gg/yJvG9jkP9e" target="_blank" rel="noopener noreferrer" className="w-10 h-10 flex items-center justify-center rounded-none tech-bracket border border-white/[0.08] text-muted-foreground hover:text-primary transition-all hover:border-primary/50 group bg-white/[0.02] hover:bg-primary/10">
                  <span className="sr-only">Discord</span>
                  <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 group-hover:scale-110 transition-transform"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" /></svg>
                </a>
                <a href="https://x.com/HedgEdgeinfo" target="_blank" rel="noopener noreferrer" className="w-10 h-10 flex items-center justify-center rounded-none tech-bracket border border-white/[0.08] text-muted-foreground hover:text-primary transition-all hover:border-primary/50 group bg-white/[0.02] hover:bg-primary/10">
                  <span className="sr-only">X (Twitter)</span>
                  <svg viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5 group-hover:scale-110 transition-transform"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>
                </a>
                <a href="https://www.youtube.com/@Hedge-Edge" target="_blank" rel="noopener noreferrer" className="w-10 h-10 flex items-center justify-center rounded-none tech-bracket border border-white/[0.08] text-muted-foreground hover:text-primary transition-all hover:border-primary/50 group bg-white/[0.02] hover:bg-primary/10">
                  <span className="sr-only">YouTube</span>
                  <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 group-hover:scale-110 transition-transform"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" /></svg>
                </a>
              </div>
            </div>

            {/* Empty Spacer Column */}
            <div className="hidden lg:block lg:col-span-2"></div>

            {/* Navigation Links */}
            <div className="md:col-span-7 lg:col-span-6 flex items-start justify-start md:justify-end">
              <div className="flex flex-col gap-4">
                <a href="/privacy-policy" className="text-muted-foreground hover:text-primary transition-colors text-sm">Privacy Policy</a>
                <a href="/terms-of-service" className="text-muted-foreground hover:text-primary transition-colors text-sm">Terms of Service</a>
                <a href="/docs" className="text-muted-foreground hover:text-primary transition-colors text-sm">Docs</a>
                <a href="mailto:team@hedgedge.info" className="text-muted-foreground hover:text-primary transition-colors text-sm">Contact Us</a>
              </div>
            </div>
          </div>

          <div className="border-t border-white/[0.04] pt-8">
            <div className="flex items-start gap-4 text-muted-foreground/50 text-[10px] leading-relaxed max-w-5xl">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <p>
                <strong className="text-white/40 uppercase tracking-wide">Risk & Broker Disclosure:</strong> Trading foreign exchange, CFDs, and other financial instruments on margin carries a high level of risk. The high degree of leverage can work against you as well as for you. Before deciding to trade, carefully consider your investment objectives, level of experience, and risk appetite. HedgeEdge is a software tool designed to assist with trade and risk management, not a trading signal service or financial advisor. We may receive compensation via affiliate links at no cost to you. Past performance does not guarantee future results.
              </p>
            </div>
          </div>
        </div>
      </footer >

      <BetaAccessModal
        open={showBetaModal}
        onClose={() => { setShowBetaModal(false); setBetaSuccess(false); setBetaError(null); }}
        onSubmit={handleBetaAccept}
        loading={betaLoading}
        success={betaSuccess}
        error={betaError}
      />

      <SubscriptionAgreementModal
        open={showSubscriptionModal}
        onClose={() => setShowSubscriptionModal(false)}
        onAccept={handleCheckout}
        loading={checkoutLoading}
        planName={pendingTierName}
        price={pendingTierPrice}
        billingPeriod={isAnnualBilling ? "year" : "month"}
      />

    </div >
  );
}
