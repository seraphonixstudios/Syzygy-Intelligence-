"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  Check,
  ChevronDown,
  Sparkles,
  Cloud,
  Server,
  Shield,
  Workflow,
  Layers,
  Zap,
  BarChart3,
  Lock,
  Users,
  Cpu,
  Infinity,
  ArrowRight,
  Mail,
  Send,
  Star,
} from "lucide-react";

// ─── DATA ─────────────────────────────────────────────────
const TIERS = [
  {
    id: "open-source",
    name: "Nigredo",
    subtitle: "The Prima Materia",
    price: 0,
    period: "forever free",
    icon: "/branding/sol.logo.png",
    badge: "Open Source",
    badgeClass: "bg-syzygy-obsidian text-syzygy-grey-light border-syzygy-surface-border",
    description: "The raw material of transformation—our MIT-licensed core. Self-host, fork, and build without limits.",
    popular: false,
    features: [
      { text: "All 11 workflow engines", included: true },
      { text: "Unlimited local agents", included: true },
      { text: "Consensus engine", included: true },
      { text: "Self-hosted (Docker)", included: true },
      { text: "Community support", included: true },
      { text: "Basic observability", included: false },
      { text: "Cloud hosting", included: false },
      { text: "Team collaboration", included: false },
      { text: "Priority support", included: false },
    ],
    cta: "Get Started Free",
    href: "https://github.com/seraphonixstudios/Syzygy-Intelligence-",
  },
  {
    id: "solve",
    name: "Solve",
    subtitle: "Dissolution",
    price: 29,
    period: "/month",
    icon: "/branding/sol.logo.png",
    badge: "Popular",
    badgeClass: "bg-syzygy-gold/20 text-syzygy-gold border-syzygy-gold/30",
    description: "Break down complexity. Managed cloud with agent observability for small teams.",
    popular: true,
    features: [
      { text: "All workflow engines", included: true },
      { text: "5 team members", included: true },
      { text: "10,000 executions/mo", included: true },
      { text: "Cloud-hosted inference", included: true },
      { text: "Agent tracing & logs", included: true },
      { text: "Cost tracking per agent", included: true },
      { text: "Email support", included: true },
      { text: "SSO & audit logs", included: false },
      { text: "On-prem deployment", included: false },
    ],
    cta: "Start Free Trial",
    href: "#waitlist",
  },
  {
    id: "coagula",
    name: "Coagula",
    subtitle: "Coalescence",
    price: 99,
    period: "/month",
    icon: "/branding/luna.logo.png",
    badge: "Best Value",
    badgeClass: "bg-syzygy-bone/20 text-syzygy-bone border-syzygy-bone/30",
    description: "Bring your agents together. Full observability, governance, and team-scale orchestration.",
    popular: false,
    features: [
      { text: "Everything in Solve", included: true },
      { text: "25 team members", included: true },
      { text: "100,000 executions/mo", included: true },
      { text: "Multi-agent orchestration", included: true },
      { text: "Evaluation & scoring", included: true },
      { text: "Custom model fine-tuning", included: true },
      { text: "Priority support", included: true },
      { text: "SSO & audit logs", included: true },
      { text: "99.9% SLA", included: true },
    ],
    cta: "Start Free Trial",
    href: "#waitlist",
  },
  {
    id: "rebis",
    name: "Rebis",
    subtitle: "The Unified",
    price: null,
    period: "custom",
    icon: "/branding/rebis.logo.png",
    badge: "Enterprise",
    badgeClass: "bg-syzygy-gold/10 text-syzygy-gold-light border-syzygy-gold/20",
    description: "The completed Great Work. Dedicated infrastructure, compliance, and white-glove deployment.",
    popular: false,
    features: [
      { text: "Everything in Coagula", included: true },
      { text: "Unlimited team members", included: true },
      { text: "Unlimited executions", included: true },
      { text: "On-premise deployment", included: true },
      { text: "Custom GPU orchestration", included: true },
      { text: "Dedicated support engineer", included: true },
      { text: "Custom agent training", included: true },
      { text: "Regulatory compliance (SOC2/GDPR)", included: true },
      { text: "Private Slack channel", included: true },
    ],
    cta: "Contact Us",
    href: "#waitlist",
  },
];

const FAQS = [
  {
    q: "Is Syzygy truly open source?",
    a: "Yes. The core Syzygy platform is MIT-licensed—the same license used by React, Next.js, and DenchClaw. You can self-host, fork, modify, and redistribute freely. Our cloud services are a separate paid offering for those who want managed infrastructure.",
  },
  {
    q: "What happens if I stop paying?",
    a: "Your data remains accessible. You can export everything and self-host using the open-source core at any time. No lock-in, no data hostage. Your cloud workspace will be downgraded to the free tier limits.",
  },
  {
    q: "Can I use my own LLM models?",
    a: "Absolutely. Syzygy is model-agnostic—bring your own Ollama models, OpenAI keys, or any LiteLLM-compatible provider. Cloud plans include managed inference for supported open models.",
  },
  {
    q: "How is pricing calculated?",
    a: "Plans are based on team size and execution volume. An 'execution' is one complete agent run—from task receipt to final output. Most teams use 1,000–5,000 executions per month. We offer generous overage limits before throttling.",
  },
  {
    q: "Do you offer academic or non-profit discounts?",
    a: "Yes. We provide significant discounts for verified academic institutions, open-source projects, and registered non-profits. Contact us for details.",
  },
  {
    q: "What does 'managed inference' include?",
    a: "Managed inference means we host and optimize the Ollama models on our GPU infrastructure—no need to provision your own hardware. You get faster response times, automatic updates, and pay-per-execution rather than per-GPU-hour.",
  },
];

const FEATURES_COMPARE = [
  { category: "Core Engine", items: [
    { name: "Workflow engines", free: "11", solve: "11", coagula: "11", rebis: "11 + custom" },
    { name: "Consensus engine", free: true, solve: true, coagula: true, rebis: true },
    { name: "Custom agents", free: true, solve: true, coagula: true, rebis: true },
    { name: "Multi-agent orchestration", free: false, solve: false, coagula: true, rebis: true },
    { name: "Custom model fine-tuning", free: false, solve: false, coagula: true, rebis: true },
  ]},
  { category: "Deployment", items: [
    { name: "Self-hosted (Docker)", free: true, solve: true, coagula: true, rebis: true },
    { name: "Cloud hosted", free: false, solve: true, coagula: true, rebis: true },
    { name: "On-premise", free: false, solve: false, coagula: false, rebis: true },
    { name: "Kubernetes support", free: false, solve: false, coagula: true, rebis: true },
  ]},
  { category: "Observability", items: [
    { name: "Agent tracing", free: false, solve: true, coagula: true, rebis: true },
    { name: "Execution logs", free: "Basic", solve: "30 days", coagula: "90 days", rebis: "Unlimited" },
    { name: "Cost tracking", free: false, solve: true, coagula: true, rebis: true },
    { name: "Evaluation scoring", free: false, solve: false, coagula: true, rebis: true },
  ]},
  { category: "Team & Security", items: [
    { name: "Team members", free: "1", solve: "5", coagula: "25", rebis: "Unlimited" },
    { name: "SSO", free: false, solve: false, coagula: true, rebis: true },
    { name: "Audit logs", free: false, solve: false, coagula: true, rebis: true },
    { name: "Compliance reports", free: false, solve: false, coagula: false, rebis: true },
    { name: "SLA", free: false, solve: false, coagula: "99.9%", rebis: "99.99%" },
  ]},
];

const QUOTES = [
  {
    text: "Syzygy's polarity-aware consensus completely changed how we approach agent collaboration. It's like having a team of expert debaters who always find the truth.",
    author: "Dr. Elena Vasquez",
    role: "CTO, Synthwave Labs",
  },
  {
    text: "We evaluated LangChain, CrewAI, and every agent framework out there. Syzygy's workflow engine and observability layer won us over in a single demo.",
    author: "Marcus Chen",
    role: "Head of AI, Prism Analytics",
  },
  {
    text: "The alchemical design philosophy isn't just aesthetic—it produces genuinely better consensus outcomes. Our team's output quality improved 40% after switching.",
    author: "Sarah Okonkwo",
    role: "AI Research Lead, Quantum Dynamics",
  },
];

// ─── SUB-COMPONENTS ──────────────────────────────────────

function Particles({ tier }: { tier?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let particles: { x: number; y: number; vx: number; vy: number; size: number; alpha: number; symbol: string }[] = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const syms = ["\u2606", "\u25cb", "\u25b3", "\u25bd", "\u221e", "\u2727", "\u2609", "\u263d"];
    for (let i = 0; i < 60; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: 6 + Math.random() * 14,
        alpha: 0.06 + Math.random() * 0.12,
        symbol: syms[Math.floor(Math.random() * syms.length)],
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.font = `${p.size}px Arial`;
        ctx.fillStyle = `rgba(212, 168, 67, ${p.alpha})`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(p.symbol, p.x, p.y);
      });
      animId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="pointer-events-none fixed inset-0 z-0" />;
}

function PricingCard({ tier, index, isAnnual }: { tier: typeof TIERS[0]; index: number; isAnnual: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const effectivePrice = tier.price !== null && isAnnual ? Math.round(tier.price * 10 * 12) / 12 : tier.price;

  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ delay: index * 0.12, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
      className={cn(
        "group relative flex flex-col rounded-2xl border p-6 transition-all duration-500",
        tier.popular
          ? "border-syzygy-gold/40 bg-gradient-to-b from-syzygy-gold/[0.04] to-syzygy-deep shadow-2xl shadow-syzygy-gold/10"
          : "border-syzygy-surface-border bg-syzygy-card hover:border-syzygy-gold/20"
      )}
    >
      {/* Glow overlay */}
      <div
        className={cn(
          "pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-500",
          "bg-gradient-to-b from-syzygy-gold/[0.02] to-transparent",
          "group-hover:opacity-100"
        )}
      />

      {/* Badge */}
      {tier.badge && (
        <div className="absolute -top-3 left-6 z-10">
          <Badge className={cn("px-3 py-1 text-[10px] font-semibold uppercase tracking-widest", tier.badgeClass)}>
            {tier.badge}
          </Badge>
        </div>
      )}

      {/* Header */}
      <div className="relative z-10 mb-4 flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center">
          <img
            src={tier.icon}
            alt={tier.name}
            className={cn(
              "h-full w-full object-contain brightness-110 transition-transform duration-500",
              "group-hover:scale-110"
            )}
          />
        </div>
        <div>
          <h3 className={cn(
            "font-alchemical text-lg font-semibold",
            tier.popular ? "text-syzygy-gold" : "text-syzygy-grey-light"
          )}>
            {tier.name}
          </h3>
          <p className="text-[10px] uppercase tracking-[0.2em] text-syzygy-grey/50">{tier.subtitle}</p>
        </div>
      </div>

      {/* Description */}
      <p className="relative z-10 mb-4 text-xs leading-relaxed text-syzygy-grey/60">{tier.description}</p>

      {/* Price */}
      <div className="relative z-10 mb-4 flex items-baseline gap-1">
        {tier.price !== null ? (
          <>
            <span className="font-alchemical text-4xl font-bold text-foreground">
              ${isAnnual ? effectivePrice : tier.price}
            </span>
            <span className="text-xs text-syzygy-grey/50">
              {isAnnual ? `/mo (billed annually)` : tier.period}
            </span>
          </>
        ) : (
          <span className="font-alchemical text-3xl font-bold text-syzygy-gold-light">Custom</span>
        )}
      </div>

      {/* CTA */}
      <Button
        onClick={() => {
          if (tier.href.startsWith("http")) window.open(tier.href, "_blank");
          else document.getElementById("waitlist")?.scrollIntoView({ behavior: "smooth" });
        }}
        variant={tier.popular ? "gold" : "occult"}
        size="lg"
        className="relative z-10 mb-5 w-full gap-2"
      >
        {tier.cta}
        <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
      </Button>

      {/* Features */}
      <ul className="relative z-10 space-y-2.5">
        {tier.features.map((f, i) => (
          <motion.li
            key={i}
            initial={{ opacity: 0, x: -8 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.12 + i * 0.03 }}
            className="flex items-center gap-2.5 text-xs"
          >
            <div
              className={cn(
                "flex h-4 w-4 shrink-0 items-center justify-center rounded-full",
                f.included
                  ? "bg-syzygy-gold/20 text-syzygy-gold"
                  : "bg-syzygy-obsidian text-syzygy-grey/30"
              )}
            >
              {f.included ? (
                <Check className="h-2.5 w-2.5" />
              ) : (
                <div className="h-1.5 w-1.5 rounded-full bg-syzygy-grey/20" />
              )}
            </div>
            <span className={f.included ? "text-syzygy-grey-light" : "text-syzygy-grey/40"}>
              {f.text}
            </span>
          </motion.li>
        ))}
      </ul>
    </motion.div>
  );
}

function ComparisonTable() {
  const [openCategory, setOpenCategory] = useState<string | null>(FEATURES_COMPARE[0].category);

  const cellClass = (val: any) =>
    val === true
      ? "text-syzygy-gold"
      : val === false
      ? "text-syzygy-grey/30"
      : "text-syzygy-grey-light";

  const cellContent = (val: any) =>
    val === true ? <Check className="h-4 w-4" /> : val === false ? <div className="h-1.5 w-1.5 rounded-full bg-syzygy-grey/20" /> : val;

  return (
    <div className="space-y-2">
      {FEATURES_COMPARE.map((cat) => (
        <div key={cat.category} className="overflow-hidden rounded-xl border border-syzygy-surface-border">
          <button
            onClick={() => setOpenCategory(openCategory === cat.category ? null : cat.category)}
            className="flex w-full items-center justify-between bg-syzygy-shadow/50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-syzygy-gold transition-colors hover:bg-syzygy-obsidian"
          >
            {cat.category}
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 transition-transform duration-300",
                openCategory === cat.category && "rotate-180"
              )}
            />
          </button>
          <AnimatePresence initial={false}>
            {openCategory === cat.category && (
              <motion.div
                key="content"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="overflow-hidden"
              >
                <div className="divide-y divide-syzygy-surface-border/50">
                  {cat.items.map((item, i) => (
                    <div
                      key={i}
                      className="grid grid-cols-[1fr_60px_60px_60px_60px] gap-2 px-4 py-2.5 text-xs hover:bg-syzygy-shadow/30"
                    >
                      <span className="text-syzygy-grey-light">{item.name}</span>
                      <span className={cn("text-center", cellClass(item.free))}>{cellContent(item.free)}</span>
                      <span className={cn("text-center", cellClass(item.solve))}>{cellContent(item.solve)}</span>
                      <span className={cn("text-center", cellClass(item.coagula))}>{cellContent(item.coagula)}</span>
                      <span className={cn("text-center", cellClass(item.rebis))}>{cellContent(item.rebis)}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}

function FAQ({ faqs }: { faqs: typeof FAQS }) {
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  return (
    <div className="space-y-2">
      {faqs.map((faq, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: i * 0.05 }}
          className="overflow-hidden rounded-xl border border-syzygy-surface-border"
        >
          <button
            onClick={() => setOpenIdx(openIdx === i ? null : i)}
            className="flex w-full items-center justify-between bg-syzygy-card px-5 py-3.5 text-left text-sm font-medium text-syzygy-grey-light transition-colors hover:bg-syzygy-obsidian"
          >
            {faq.q}
            <ChevronDown
              className={cn(
                "h-4 w-4 shrink-0 text-syzygy-gold/60 transition-transform duration-300",
                openIdx === i && "rotate-180"
              )}
            />
          </button>
          <AnimatePresence initial={false}>
            {openIdx === i && (
              <motion.div
                key="faq-answer"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="overflow-hidden"
              >
                <div className="border-t border-syzygy-surface-border/50 px-5 py-3.5 text-xs leading-relaxed text-syzygy-grey/60">
                  {faq.a}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      ))}
    </div>
  );
}

// ─── MAIN PAGE ───────────────────────────────────────────

export default function CloudPage() {
  const [isAnnual, setIsAnnual] = useState(false);
  const [email, setEmail] = useState("");
  const [tierInterest, setTierInterest] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [testimonialIdx, setTestimonialIdx] = useState(0);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  // Rotating testimonials
  useEffect(() => {
    const t = setInterval(() => setTestimonialIdx((i) => (i + 1) % QUOTES.length), 5000);
    return () => clearInterval(t);
  }, []);

  // Waitlist submit
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!email.trim()) return;
      setSubmitting(true);
      // Simulate API call
      await new Promise((r) => setTimeout(r, 1200));
      setSubmitted(true);
      toast.success("You're on the list! We'll be in touch soon.");
      setSubmitting(false);
    },
    [email]
  );

  return (
    <>
      {/* Particle canvas background */}
      <Particles />

      <div className="relative z-10 space-y-6">
        {/* ── Sticky Nav ── */}
        <motion.nav
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="sticky top-0 z-50 -mx-6 -mt-6 mb-0 border-b border-syzygy-surface-border/50 bg-black/80 px-6 py-3 backdrop-blur-xl"
        >
          <div className="mx-auto flex max-w-6xl items-center justify-between">
            <div className="flex items-center gap-3">
              <img src="/branding/pagetop.logo.png" alt="Syzygy" className="h-7 w-auto brightness-110" />
              <span className="hidden text-xs font-semibold uppercase tracking-[0.25em] text-syzygy-gold md:block">
                Cloud
              </span>
            </div>
            <div className="hidden items-center gap-6 md:flex">
              {["Plans", "Features", "FAQ", "Contact"].map((s) => (
                <a
                  key={s}
                  href={`#${s.toLowerCase()}`}
                  className="text-[11px] uppercase tracking-[0.15em] text-syzygy-grey/50 transition-colors hover:text-syzygy-gold"
                >
                  {s}
                </a>
              ))}
              <Button variant="gold" size="sm" className="gap-1.5 text-xs">
                <Sparkles className="h-3 w-3" /> Get Early Access
              </Button>
            </div>
            <button
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="flex flex-col gap-1 md:hidden"
            >
              <div className="h-px w-5 bg-syzygy-grey/60" />
              <div className="h-px w-5 bg-syzygy-grey/60" />
              <div className="h-px w-5 bg-syzygy-grey/60" />
            </button>
          </div>
        </motion.nav>

        {/* ── Hero ── */}
        <section className="relative overflow-hidden rounded-2xl border border-syzygy-surface-border py-16 md:py-24">
          {/* Gradient glow */}
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-syzygy-gold/[0.03] via-transparent to-transparent" />
          <div className="pointer-events-none absolute -top-40 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-syzygy-gold/5 blur-[120px]" />

          <div className="relative mx-auto max-w-4xl px-6 text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            >
              <img
                src="/branding/rebis.logo.png"
                alt="Rebis"
                className="mx-auto mb-6 h-20 w-auto animate-breathe brightness-110 drop-shadow-[0_0_30px_rgba(212,168,67,0.15)]"
              />
              <h1 className="mb-3 font-alchemical text-4xl font-bold tracking-wider md:text-6xl">
                <span className="syzygy-title">Syzygy Cloud</span>
              </h1>
              <p className="mx-auto mb-6 max-w-2xl text-sm leading-relaxed text-syzygy-grey/60 md:text-base">
                The alchemical cloud for multi-agent intelligence. Deploy, observe, and scale
                polarity-aware agent teams without managing infrastructure.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <Button variant="gold" size="lg" className="gap-2">
                  <Sparkles className="h-4 w-4" /> See Plans Below
                </Button>
                <Button
                  variant="occult"
                  size="lg"
                  className="gap-2"
                  onClick={() => {
                    window.open("https://github.com/seraphonixstudios/Syzygy-Intelligence-", "_blank");
                  }}
                >
                  <Star className="h-4 w-4" /> Self-Host Free
                </Button>
              </div>
            </motion.div>

            {/* Trust strip */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="mt-10 flex flex-wrap items-center justify-center gap-6 text-[10px] uppercase tracking-[0.15em] text-syzygy-grey/40"
            >
              <span className="flex items-center gap-1.5"><Cloud className="h-3 w-3" /> Managed Infra</span>
              <span className="flex items-center gap-1.5"><Shield className="h-3 w-3" /> SOC2 Ready</span>
              <span className="flex items-center gap-1.5"><Zap className="h-3 w-3" /> GPU Optimized</span>
              <span className="flex items-center gap-1.5"><Lock className="h-3 w-3" /> Data Sovereign</span>
            </motion.div>
          </div>
        </section>

        {/* ── Pricing ── */}
        <section id="plans" className="scroll-mt-20">
          <div className="mb-8 text-center">
            <h2 className="syzygy-title font-alchemical text-2xl font-bold tracking-wider">Choose Your Path</h2>
            <p className="mt-1 text-xs text-syzygy-grey/50">
              All plans include access to the open-source core. Upgrade when you need managed infrastructure.
            </p>

            {/* Annual toggle */}
            <div className="mt-4 flex items-center justify-center gap-3">
              <span className={cn("text-xs transition-colors", !isAnnual ? "text-syzygy-grey-light" : "text-syzygy-grey/40")}>
                Monthly
              </span>
              <button
                onClick={() => setIsAnnual(!isAnnual)}
                className={cn(
                  "relative h-5 w-10 rounded-full transition-colors",
                  isAnnual ? "bg-syzygy-gold" : "bg-syzygy-obsidian"
                )}
              >
                <div
                  className={cn(
                    "absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-black transition-transform duration-300",
                    isAnnual && "translate-x-5"
                  )}
                />
              </button>
              <span className={cn("text-xs transition-colors", isAnnual ? "text-syzygy-grey-light" : "text-syzygy-grey/40")}>
                Annual <span className="text-syzygy-gold">Save ~17%</span>
              </span>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {TIERS.map((tier, i) => (
              <PricingCard key={tier.id} tier={tier} index={i} isAnnual={isAnnual} />
            ))}
          </div>
        </section>

        {/* ── Value Props Strip ── */}
        <motion.section
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="grid gap-3 rounded-xl border border-syzygy-surface-border bg-syzygy-card p-6 md:grid-cols-4"
        >
          {[
            { icon: Server, label: "Managed GPU Infra", desc: "No more provisioning. We handle Ollama, scaling, and uptime." },
            { icon: BarChart3, label: "Full Observability", desc: "Trace every agent thought, cost, and execution path." },
            { icon: Workflow, label: "11 Workflow Engines", desc: "From consensus to code-gen—orchestrate any task." },
            { icon: Users, label: "Team Collaboration", desc: "Share agents, workspaces, and insights across your org." },
          ].map((v, i) => (
            <div key={i} className="space-y-1.5 text-center">
              <v.icon className="mx-auto h-5 w-5 text-syzygy-gold" />
              <h4 className="text-xs font-semibold text-syzygy-grey-light">{v.label}</h4>
              <p className="text-[10px] leading-relaxed text-syzygy-grey/50">{v.desc}</p>
            </div>
          ))}
        </motion.section>

        {/* ── Testimonials ── */}
        <section className="relative overflow-hidden rounded-xl border border-syzygy-surface-border bg-gradient-to-br from-syzygy-gold/[0.02] to-transparent py-10">
          <div className="mx-auto max-w-2xl px-6 text-center">
            <AnimatePresence mode="wait">
              <motion.div
                key={testimonialIdx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.4 }}
              >
                <div className="mb-4 flex justify-center gap-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-3.5 w-3.5 fill-syzygy-gold text-syzygy-gold" />
                  ))}
                </div>
                <p className="mb-4 text-sm italic leading-relaxed text-syzygy-grey-light/80">
                  &ldquo;{QUOTES[testimonialIdx].text}&rdquo;
                </p>
                <div>
                  <p className="text-xs font-semibold text-syzygy-grey-light">{QUOTES[testimonialIdx].author}</p>
                  <p className="text-[10px] text-syzygy-grey/50">{QUOTES[testimonialIdx].role}</p>
                </div>
              </motion.div>
            </AnimatePresence>
            <div className="mt-4 flex justify-center gap-2">
              {QUOTES.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setTestimonialIdx(i)}
                  className={cn(
                    "h-1.5 rounded-full transition-all duration-300",
                    i === testimonialIdx ? "w-6 bg-syzygy-gold" : "w-1.5 bg-syzygy-obsidian"
                  )}
                />
              ))}
            </div>
          </div>
        </section>

        {/* ── Feature Comparison ── */}
        <section id="features" className="scroll-mt-20">
          <h2 className="mb-4 text-center font-alchemical text-xl font-bold tracking-wider text-syzygy-gold">
            Compare Plans
          </h2>
          <p className="mb-6 text-center text-xs text-syzygy-grey/50">
            Every feature available in every tier—limits scale with your needs.
          </p>
          <ComparisonTable />
        </section>

        {/* ── FAQ ── */}
        <section id="faq" className="scroll-mt-20">
          <h2 className="mb-4 text-center font-alchemical text-xl font-bold tracking-wider text-syzygy-gold">
            Frequently Asked Questions
          </h2>
          <p className="mb-6 text-center text-xs text-syzygy-grey/50">
            Everything you need to know about Syzygy Cloud.
          </p>
          <FAQ faqs={FAQS} />
        </section>

        {/* ── Waitlist CTA ── */}
        <section
          id="waitlist"
          className="scroll-mt-20 overflow-hidden rounded-2xl border border-syzygy-gold/20 bg-gradient-to-br from-syzygy-gold/[0.04] via-syzygy-deep to-syzygy-gold/[0.02] py-12"
        >
          <div className="relative mx-auto max-w-xl px-6 text-center">
            <div className="pointer-events-none absolute -inset-20 bg-gradient-radial from-syzygy-gold/5 to-transparent blur-[100px]" />

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <div className="mb-4 flex justify-center gap-3">
                <img src="/branding/sol.logo.png" alt="Sol" className="h-10 w-auto animate-breathe brightness-110" />
                <img src="/branding/rebis.logo.png" alt="Rebis" className="h-12 w-auto animate-breathe brightness-110" />
                <img src="/branding/luna.logo.png" alt="Luna" className="h-10 w-auto animate-breathe brightness-110" />
              </div>

              <h2 className="mb-2 font-alchemical text-2xl font-bold tracking-wider">
                <span className="syzygy-title">Join the Waitlist</span>
              </h2>
              <p className="mb-6 text-sm text-syzygy-grey/60">
                Syzygy Cloud is in private beta. Early adopters get founding member pricing and priority access to GPU-backed inference.
              </p>

              <AnimatePresence mode="wait">
                {!submitted ? (
                  <motion.form
                    key="form"
                    onSubmit={handleSubmit}
                    exit={{ opacity: 0, y: -10 }}
                    className="mx-auto flex max-w-md flex-col gap-3"
                  >
                    <div className="flex items-center gap-2 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/50 px-4 py-2.5 focus-within:border-syzygy-gold/50 focus-within:shadow-lg">
                      <Mail className="h-4 w-4 shrink-0 text-syzygy-grey/40" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@company.com"
                        required
                        className="flex-1 bg-transparent text-sm text-foreground placeholder-syzygy-grey/30 outline-none"
                      />
                      <select
                        value={tierInterest}
                        onChange={(e) => setTierInterest(e.target.value)}
                        className="hidden bg-transparent text-xs text-syzygy-grey/50 outline-none md:block"
                      >
                        <option value="">Any plan</option>
                        <option value="solve">Solve</option>
                        <option value="coagula">Coagula</option>
                        <option value="rebis">Rebis</option>
                      </select>
                    </div>
                    <Button type="submit" variant="gold" size="lg" disabled={submitting} className="gap-2">
                      {submitting ? (
                        <div className="ouroboros-ring h-4 w-4" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                      {submitting ? "Joining..." : "Get Early Access"}
                    </Button>
                    <p className="text-[10px] text-syzygy-grey/30">
                      No spam. We&apos;ll only email about your waitlist status and launch updates.
                    </p>
                  </motion.form>
                ) : (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="space-y-3"
                  >
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-syzygy-gold/20">
                      <Check className="h-8 w-8 text-syzygy-gold" />
                    </div>
                    <p className="font-alchemical text-lg text-syzygy-gold">You&apos;re on the list</p>
                    <p className="text-xs text-syzygy-grey/50">
                      We&apos;ll notify you at <span className="text-syzygy-grey-light">{email}</span> when your spot is ready.
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        </section>

        {/* ── Footer ── */}
        <footer className="border-t border-syzygy-surface-border px-6 py-8 text-center">
          <div className="flex flex-col items-center gap-3">
            <img src="/branding/seraphonixlogo.png" alt="Seraphonix" className="h-8 w-auto brightness-110" />
            <div className="flex items-center gap-4 text-[10px] uppercase tracking-[0.15em] text-syzygy-grey/30">
              <span>Syzygy Intelligence</span>
              <span className="h-3 w-px bg-syzygy-surface-border" />
              <span>Seraphonix Studios</span>
              <span className="h-3 w-px bg-syzygy-surface-border" />
              <span>{new Date().getFullYear()}</span>
            </div>
            <p className="text-[10px] text-syzygy-grey/20">
              Solve et Coagula — The Great Work continues.
            </p>
          </div>
        </footer>
      </div>
    </>
  );
}
