"use client";

import { Code, FileText, Globe, Shield, CheckCircle2, ChevronDown, ChevronRight, Sparkles, Lightbulb, AlertTriangle, TrendingUp, Target, Layers, GitBranch, Database, Zap, BookOpen, Mic, BarChart3, ArrowRight, Search } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium", className)}>{children}</span>;
}

function SectionCard({ title, icon: Icon, children, defaultOpen = true }: { title: string; icon?: React.ElementType; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 overflow-hidden">
      <button type="button" onClick={() => setOpen(!open)} className="flex w-full items-center gap-2 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-syzygy-grey/50 hover:bg-syzygy-shadow/20">
        {Icon && <Icon className="h-3.5 w-3.5" />}
        <span className="flex-1">{title}</span>
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
      </button>
      {open && <div className="px-4 pb-3 space-y-2">{children}</div>}
    </div>
  );
}

function FormattedText({ text }: { text: string | undefined | null }) {
  if (!text) return <span className="text-syzygy-grey/40 text-xs italic">No data</span>;
  const str = typeof text === "object" ? JSON.stringify(text, null, 2) : String(text);
  return <p className="text-xs text-syzygy-grey/80 leading-relaxed whitespace-pre-wrap">{str}</p>;
}

function CodeBlock({ code, label }: { code: string | undefined | null; label?: string }) {
  if (!code) return null;
  return (
    <div className="space-y-1">
      {label && <p className="text-[10px] font-medium uppercase tracking-wider text-syzygy-grey/40">{label}</p>}
      <pre className="overflow-auto rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/70 p-3 text-[11px] text-syzygy-grey/80 font-mono max-h-64">{String(code)}</pre>
    </div>
  );
}

function render_coding(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10"><Code className="h-3 w-3" />{d.language || "python"}</Badge>
        <Badge className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10"><CheckCircle2 className="h-3 w-3" />{d.status}</Badge>
      </div>
      {d.steps && Object.entries(d.steps).map(([step, val]: [string, any]) => (
        <SectionCard key={step} title={step} icon={step === "generation" ? Code : step === "review" ? Shield : step === "test" ? CheckCircle2 : Zap}>
          {typeof val === "object" && val !== null ? (
            Object.entries(val).map(([k, v]) => {
              const keyLower = k.toLowerCase();
              return keyLower === "code" || keyLower === "unit_tests" ? <CodeBlock key={k} code={String(v)} label={k} />
                : <FormattedText key={k} text={String(v)} />;
            })
          ) : <FormattedText text={String(val)} />}
        </SectionCard>
      ))}
      {d.reasoning?.length > 0 && (
        <SectionCard title="Agent Reasoning" icon={Lightbulb}>
          {d.reasoning.map((r: any, i: number) => (
            <div key={i} className="flex items-start gap-2 rounded-lg bg-syzygy-shadow/20 p-2">
              <span className="shrink-0 rounded bg-syzygy-gold/10 px-1.5 py-0.5 text-[10px] font-mono text-syzygy-gold">{r.agent}</span>
              <span className="text-xs text-syzygy-grey/70">{r.thought}</span>
              {r.confidence && <span className="ml-auto shrink-0 text-[10px] text-syzygy-grey/40">{Math.round(r.confidence * 100)}%</span>}
            </div>
          ))}
        </SectionCard>
      )}
    </div>
  );
}

function render_research(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-syzygy-grey/60"><Globe className="h-3.5 w-3.5" />{d.query}</div>
      <Badge className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10"><BarChart3 className="h-3 w-3" />{d.sources_count || 0} sources</Badge>
      {Array.isArray(d.findings) && d.findings.length > 0 && (
        <SectionCard title="Findings" icon={Lightbulb}>
          {d.findings.map((f: any, i: number) => (
            <div key={i} className="rounded-lg border border-syzygy-surface-border/50 bg-syzygy-shadow/20 p-3 space-y-1">
              <p className="text-xs font-medium text-syzygy-grey-light">{f.title || `Finding ${i + 1}`}</p>
              <p className="text-[11px] text-syzygy-grey/60 leading-relaxed">{f.snippet || f.content || JSON.stringify(f)}</p>
              {f.url && <p className="text-[10px] text-syzygy-gold/60 truncate">{f.url}</p>}
            </div>
          ))}
        </SectionCard>
      )}
      {d.synthesis && <SectionCard title="Synthesis" icon={Sparkles}><FormattedText text={d.synthesis} /></SectionCard>}
    </div>
  );
}

function render_content(d: any) {
  const stages = ["research", "outline", "draft", "edited", "final"];
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-purple-500/30 text-purple-400 bg-purple-500/10"><FileText className="h-3 w-3" />{d.topic}</Badge>
        {d.polarity && <Badge className="border-amber-500/30 text-amber-400 bg-amber-500/10">{d.polarity}</Badge>}
      </div>
      {stages.map((s) => {
        const val = d[s];
        if (!val) return null;
        return <SectionCard key={s} title={s.charAt(0).toUpperCase() + s.slice(1)} icon={FileText}><FormattedText text={typeof val === "object" ? val.polished || val.content || JSON.stringify(val) : val} /></SectionCard>;
      })}
    </div>
  );
}

function render_debate(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-syzygy-grey/60"><GitBranch className="h-3.5 w-3.5" />{d.topic}</div>
      <Badge className="border-amber-500/30 text-amber-400 bg-amber-500/10">{d.rounds_completed || 0} rounds</Badge>
      {["openings", "rebuttals", "closings"].map((phase) => {
        const phaseData = d[phase];
        if (!phaseData) return null;
        return (
          <SectionCard key={phase} title={phase.charAt(0).toUpperCase() + phase.slice(1)} icon={phase === "openings" ? Zap : phase === "rebuttals" ? AlertTriangle : Target}>
            {typeof phaseData === "object" ? Object.entries(phaseData).map(([side, text]: [string, any]) => (
              <div key={side} className="rounded-lg border border-syzygy-surface-border/50 bg-syzygy-shadow/20 p-3">
                <Badge className="mb-1 border-syzygy-gold/30 text-syzygy-gold-light bg-syzygy-gold/10">{side}</Badge>
                <FormattedText text={String(text)} />
              </div>
            )) : <FormattedText text={phaseData} />}
          </SectionCard>
        );
      })}
      {d.synthesis && <SectionCard title="Synthesis" icon={Sparkles}><FormattedText text={d.synthesis} /></SectionCard>}
    </div>
  );
}

function render_task_decomposition(d: any) {
  const subtasks = Array.isArray(d) ? d : d.subtasks || [];
  return (
    <div className="space-y-2">
      {subtasks.length === 0 ? (
        <p className="text-xs text-syzygy-grey/40 italic">No subtasks returned</p>
      ) : (
        subtasks.map((st: any, i: number) => (
          <div key={st.id || i} className="flex items-start gap-3 rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-3">
            <div className={cn("mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold", st.status === "completed" ? "bg-emerald-500/20 text-emerald-400" : "bg-syzygy-grey/20 text-syzygy-grey/40")}>{st.status === "completed" ? "✓" : i + 1}</div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-1.5">
                <p className="text-xs font-medium text-syzygy-grey-light">{st.description || st.id}</p>
                <Badge className={st.polarity === "masculine" ? "border-blue-500/30 text-blue-400 bg-blue-500/10" : st.polarity === "feminine" ? "border-pink-500/30 text-pink-400 bg-pink-500/10" : "border-purple-500/30 text-purple-400 bg-purple-500/10"}>{st.agent_archetype || st.archetype}</Badge>
                {st.priority && <span className="text-[10px] text-syzygy-grey/40">P{st.priority}</span>}
              </div>
              {st.result && <p className="mt-1 text-[11px] text-syzygy-grey/60 leading-relaxed">{st.result}</p>}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function render_audit(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-red-500/30 text-red-400 bg-red-500/10"><Shield className="h-3 w-3" />{d.language || "code"}</Badge>
      </div>
      {d.vulnerabilities && <SectionCard title="Vulnerabilities" icon={AlertTriangle}><FormattedText text={d.vulnerabilities} /></SectionCard>}
      {d.quality_review && <SectionCard title="Quality Review" icon={TrendingUp}><FormattedText text={d.quality_review} /></SectionCard>}
      {d.compliance_check && <SectionCard title="Compliance Check" icon={Shield}><FormattedText text={d.compliance_check} /></SectionCard>}
      {d.report && <SectionCard title="Full Report" icon={FileText}><FormattedText text={d.report} /></SectionCard>}
    </div>
  );
}

function render_test_gen(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10"><Code className="h-3 w-3" />{d.language || "python"}</Badge>
      </div>
      {d.analysis && <SectionCard title="Code Analysis" icon={Lightbulb}><FormattedText text={d.analysis} /></SectionCard>}
      {d.unit_tests && <SectionCard title="Unit Tests" icon={Code}><FormattedText text={typeof d.unit_tests === "object" ? d.unit_tests.unit_tests || JSON.stringify(d.unit_tests) : d.unit_tests} /></SectionCard>}
      {d.edge_cases && <SectionCard title="Edge Cases" icon={AlertTriangle}><FormattedText text={typeof d.edge_cases === "object" ? d.edge_cases.edge_cases || JSON.stringify(d.edge_cases) : d.edge_cases} /></SectionCard>}
      {d.validation && <SectionCard title="Validation" icon={CheckCircle2}><FormattedText text={d.validation} /></SectionCard>}
    </div>
  );
}

function render_summary(d: any) {
  return (
    <div className="space-y-3">
      <Badge className="border-teal-500/30 text-teal-400 bg-teal-500/10"><FileText className="h-3 w-3" />{d.document_count || 1} document(s)</Badge>
      {d.key_points && <SectionCard title="Key Points" icon={Lightbulb}><FormattedText text={d.key_points} /></SectionCard>}
      {d.themes && <SectionCard title="Themes" icon={Layers}><FormattedText text={d.themes} /></SectionCard>}
      {d.insights && <SectionCard title="Insights" icon={Sparkles}><FormattedText text={d.insights} /></SectionCard>}
      {d.summary && <SectionCard title="Summary" icon={FileText} defaultOpen={true}><FormattedText text={d.summary} /></SectionCard>}
    </div>
  );
}

function render_compliance(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5">
        {(Array.isArray(d.frameworks_checked) ? d.frameworks_checked : []).map((fw: string) => (
          <Badge key={fw} className="border-red-500/30 text-red-400 bg-red-500/10"><Shield className="h-3 w-3" />{fw.toUpperCase()}</Badge>
        ))}
      </div>
      {Array.isArray(d.analyses) && d.analyses.length > 0 && <SectionCard title="Analyses" icon={Search}><div className="space-y-2">{d.analyses.map((a: any, i: number) => <FormattedText key={i} text={typeof a === "object" ? JSON.stringify(a) : a} />)}</div></SectionCard>}
      {d.requirements_mapping && <SectionCard title="Requirements Mapping" icon={Layers}><FormattedText text={d.requirements_mapping} /></SectionCard>}
      {d.risk_assessment && <SectionCard title="Risk Assessment" icon={AlertTriangle}><FormattedText text={d.risk_assessment} /></SectionCard>}
      {d.remediation_plan && <SectionCard title="Remediation Plan" icon={Target}><FormattedText text={d.remediation_plan} /></SectionCard>}
    </div>
  );
}

function render_qa_bot(d: any) {
  return (
    <div className="space-y-3">
      {d.action === "ingested" ? (
        <Badge className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10"><CheckCircle2 className="h-3 w-3" />Document ingested</Badge>
      ) : (
        <>
          <div className="flex items-center gap-2 text-xs text-syzygy-grey/60"><BookOpen className="h-3.5 w-3.5" />{d.query}</div>
          {d.answer && <SectionCard title="Answer" icon={Sparkles}><FormattedText text={d.answer} /></SectionCard>}
          {d.context_used && <SectionCard title="Context Used" icon={Database}><FormattedText text={d.context_used} /></SectionCard>}
          {d.suggested_follow_ups && <SectionCard title="Follow-ups" icon={Lightbulb}><FormattedText text={d.suggested_follow_ups} /></SectionCard>}
        </>
      )}
    </div>
  );
}

function render_translate(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge className="border-blue-500/30 text-blue-400 bg-blue-500/10">{d.source_language || "auto"}</Badge>
        <ArrowRight className="h-3 w-3 text-syzygy-grey/40" />
        <Badge className="border-purple-500/30 text-purple-400 bg-purple-500/10">{d.target_language || "en"}</Badge>
      </div>
      {d.detection && <SectionCard title="Language Detection" icon={Globe}><FormattedText text={d.detection} /></SectionCard>}
      {d.direct_translation && <SectionCard title="Direct Translation" icon={Globe}><FormattedText text={typeof d.direct_translation === "object" ? d.direct_translation.translation || JSON.stringify(d.direct_translation) : d.direct_translation} /></SectionCard>}
      {d.cultural_adaptation && <SectionCard title="Cultural Adaptation" icon={Sparkles}><FormattedText text={d.cultural_adaptation} /></SectionCard>}
      {d.quality_review && <SectionCard title="Quality Review" icon={Shield}><FormattedText text={d.quality_review} /></SectionCard>}
    </div>
  );
}

function render_interview_coach(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-amber-500/30 text-amber-400 bg-amber-500/10"><Mic className="h-3 w-3" />{d.role || "general"}</Badge>
        <Badge className="border-teal-500/30 text-teal-400 bg-teal-500/10">{d.difficulty || "medium"}</Badge>
      </div>
      {Array.isArray(d.questions) && d.questions.length > 0 && (
        <SectionCard title="Questions" icon={BookOpen}>
          {d.questions.map((q: any, i: number) => (
            <div key={i} className="rounded-lg border border-syzygy-surface-border/50 bg-syzygy-shadow/20 p-3 text-xs">
              <p className="font-medium text-syzygy-grey-light">{typeof q === "object" ? q.question || JSON.stringify(q) : q}</p>
            </div>
          ))}
        </SectionCard>
      )}
      {Array.isArray(d.evaluations) && d.evaluations.length > 0 && (
        <SectionCard title="Evaluations" icon={Target}>
          {d.evaluations.map((e: any, i: number) => (
            <div key={i} className="rounded-lg border border-syzygy-surface-border/50 bg-syzygy-shadow/20 p-3 space-y-1">
              <FormattedText text={typeof e === "object" ? JSON.stringify(e) : e} />
            </div>
          ))}
        </SectionCard>
      )}
      {d.feedback && <SectionCard title="Feedback" icon={Sparkles}><FormattedText text={d.feedback} /></SectionCard>}
    </div>
  );
}

function render_data_analyzer(d: any) {
  return (
    <div className="space-y-3">
      <Badge className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10"><Database className="h-3 w-3" />{d.format || "data"}</Badge>
      {d.summary && <SectionCard title="Summary" icon={BarChart3}><FormattedText text={d.summary} /></SectionCard>}
      {d.anomalies && <SectionCard title="Anomalies" icon={AlertTriangle}><FormattedText text={d.anomalies} /></SectionCard>}
      {d.correlations && <SectionCard title="Correlations" icon={GitBranch}><FormattedText text={d.correlations} /></SectionCard>}
      {d.visualization_recommendations && <SectionCard title="Visualization Recommendations" icon={TrendingUp}><FormattedText text={d.visualization_recommendations} /></SectionCard>}
    </div>
  );
}

function render_api_designer(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10">{d.api_style || "REST"}</Badge>
        <Badge className="border-purple-500/30 text-purple-400 bg-purple-500/10"><Code className="h-3 w-3" />{d.language || "python"}</Badge>
      </div>
      {d.endpoint_design && <SectionCard title="Endpoint Design" icon={Layers}><FormattedText text={d.endpoint_design} /></SectionCard>}
      {d.openapi_spec && <SectionCard title="OpenAPI Spec" icon={FileText}><FormattedText text={typeof d.openapi_spec === "object" ? JSON.stringify(d.openapi_spec, null, 2) : d.openapi_spec} /></SectionCard>}
      {d.endpoint_stubs && <SectionCard title="Endpoint Stubs" icon={Code}><FormattedText text={typeof d.endpoint_stubs === "object" ? JSON.stringify(d.endpoint_stubs, null, 2) : d.endpoint_stubs} /></SectionCard>}
      {d.validation_tests && <SectionCard title="Validation Tests" icon={Shield}><FormattedText text={typeof d.validation_tests === "object" ? JSON.stringify(d.validation_tests, null, 2) : d.validation_tests} /></SectionCard>}
    </div>
  );
}

function render_agentic_rag(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-syzygy-grey/60"><Database className="h-3.5 w-3.5" />{d.original_query}</div>
      {d.decomposed_query && <SectionCard title="Decomposed Query" icon={GitBranch}><FormattedText text={d.decomposed_query} /></SectionCard>}
      {Array.isArray(d.retrieval_results) && d.retrieval_results.length > 0 && (
        <SectionCard title="Retrieval Results" icon={Database}>
          {d.retrieval_results.map((r: any, i: number) => <FormattedText key={i} text={typeof r === "object" ? JSON.stringify(r) : r} />)}
        </SectionCard>
      )}
      {d.synthesized_answer && <SectionCard title="Synthesized Answer" icon={Sparkles}><FormattedText text={d.synthesized_answer} /></SectionCard>}
      {d.validation && <SectionCard title="Validation" icon={CheckCircle2}><FormattedText text={d.validation} /></SectionCard>}
    </div>
  );
}

function render_report_gen(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-purple-500/30 text-purple-400 bg-purple-500/10"><FileText className="h-3 w-3" />{d.topic}</Badge>
        <Badge className="border-teal-500/30 text-teal-400 bg-teal-500/10">{d.format || "markdown"}</Badge>
      </div>
      {d.executive_summary && <SectionCard title="Executive Summary" icon={Sparkles}><FormattedText text={d.executive_summary} /></SectionCard>}
      {Array.isArray(d.sections) && d.sections.length > 0 && (
        <SectionCard title="Sections" icon={Layers}>
          {d.sections.map((s: string, i: number) => <FormattedText key={i} text={s} />)}
        </SectionCard>
      )}
      {d.report && <SectionCard title="Full Report" icon={FileText} defaultOpen={false}><FormattedText text={d.report} /></SectionCard>}
    </div>
  );
}

function render_data_pipeline(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10">{d.source_type || "csv"}</Badge>
        <ArrowRight className="h-3 w-3 text-syzygy-grey/40" />
        <Badge className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10">{d.target || "database"}</Badge>
      </div>
      {d.ingestion_analysis && <SectionCard title="Ingestion Analysis" icon={Database}><FormattedText text={d.ingestion_analysis} /></SectionCard>}
      {d.cleaning_plan && <SectionCard title="Cleaning Plan" icon={AlertTriangle}><FormattedText text={d.cleaning_plan} /></SectionCard>}
      {d.transformations && <SectionCard title="Transformations" icon={GitBranch}><FormattedText text={d.transformations} /></SectionCard>}
      {d.schema_validation && Object.keys(d.schema_validation).length > 0 && <SectionCard title="Schema Validation" icon={Shield}><FormattedText text={d.schema_validation} /></SectionCard>}
      {d.load_plan && <SectionCard title="Load Plan" icon={Zap}><FormattedText text={d.load_plan} /></SectionCard>}
    </div>
  );
}

function render_ci_piper(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10"><Code className="h-3 w-3" />{d.language || "python"}</Badge>
        {d.framework && <Badge className="border-amber-500/30 text-amber-400 bg-amber-500/10">{d.framework}</Badge>}
      </div>
      {d.analysis && <SectionCard title="Project Analysis" icon={Lightbulb}><FormattedText text={d.analysis} /></SectionCard>}
      {Array.isArray(d.configs) && d.configs.length > 0 && (
        <SectionCard title="CI/CD Configs" icon={Layers}>
          {d.configs.map((cfg: any, i: number) => (
            <div key={i} className="space-y-1">
              {typeof cfg === "object" && cfg !== null ? (
                Object.entries(cfg).map(([k, v]) => <CodeBlock key={k} code={String(v)} label={k} />)
              ) : <CodeBlock code={String(cfg)} label={`Config ${i + 1}`} />}
            </div>
          ))}
        </SectionCard>
      )}
    </div>
  );
}

function render_finetune(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-pink-500/30 text-pink-400 bg-pink-500/10"><Zap className="h-3 w-3" />{d.method || "qlora"}</Badge>
        <Badge className="border-cyan-500/30 text-cyan-400 bg-cyan-500/10">{d.model || "unknown"}</Badge>
        <Badge className={d.status === "completed" ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10" : "border-red-500/30 text-red-400 bg-red-500/10"}>{d.status}</Badge>
      </div>

      {d.metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-3">
            <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Final Loss</p>
            <p className="mt-1 text-lg font-bold text-syzygy-gold-light">{d.metrics.final_loss ?? "—"}</p>
          </div>
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-3">
            <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Perplexity</p>
            <p className="mt-1 text-lg font-bold text-syzygy-bone">{d.metrics.perplexity ?? "—"}</p>
          </div>
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-3">
            <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Steps</p>
            <p className="mt-1 text-lg font-bold text-syzygy-grey-light">{d.metrics.total_steps ?? 0}</p>
          </div>
          <div className="rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-3">
            <p className="text-[10px] uppercase tracking-wider text-syzygy-grey/40">Duration</p>
            <p className="mt-1 text-lg font-bold text-syzygy-grey-light">{d.metrics.elapsed_seconds ? `${d.metrics.elapsed_seconds}s` : "—"}</p>
          </div>
        </div>
      )}

      {d.metrics?.loss_curve && d.metrics.loss_curve.length > 1 && (
        <SectionCard title="Loss Curve" icon={TrendingUp}>
          <svg viewBox="0 0 280 80" className="w-full h-20" preserveAspectRatio="none">
            <defs>
              <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#e8c35a" />
                <stop offset="100%" stopColor="#d4a843" stopOpacity={0.2} />
              </linearGradient>
            </defs>
            {d.metrics.loss_curve.map((pt: any, i: number) => {
              if (i === 0) return null;
              const prev = d.metrics.loss_curve[i - 1];
              const x1 = ((i - 1) / (d.metrics.loss_curve.length - 1)) * 280;
              const y1 = 80 - (Math.min(prev.loss, 5) / 5) * 75;
              const x2 = (i / (d.metrics.loss_curve.length - 1)) * 280;
              const y2 = 80 - (Math.min(pt.loss, 5) / 5) * 75;
              return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#e8c35a" strokeWidth={1.5} opacity={0.8} />;
            })}
          </svg>
        </SectionCard>
      )}

      {d.error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-xs text-red-400">
          <AlertTriangle className="h-3.5 w-3.5" /> {d.error}
        </div>
      )}
    </div>
  );
}

function render_support(d: any) {
  const priorityColors: Record<string, string> = { critical: "border-red-500/30 text-red-400 bg-red-500/10", high: "border-orange-500/30 text-orange-400 bg-orange-500/10", medium: "border-yellow-500/30 text-yellow-400 bg-yellow-500/10", low: "border-green-500/30 text-green-400 bg-green-500/10" };
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-sky-500/30 text-sky-400 bg-sky-500/10"><Zap className="h-3 w-3" />{d.ticket_id}</Badge>
        <Badge className={cn(priorityColors[d.priority] || "border-syzygy-gold/30 text-syzygy-gold bg-syzygy-gold/10")}>{d.priority}</Badge>
        <Badge className="border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30">{d.category}</Badge>
        <Badge className={d.needs_escalation ? "border-red-500/30 text-red-400 bg-red-500/10" : "border-emerald-500/30 text-emerald-400 bg-emerald-500/10"}>{d.needs_escalation ? "Escalated" : "Resolved"}</Badge>
      </div>
      <SectionCard title="Resolution Steps" icon={CheckCircle2}>
        <ol className="list-decimal list-inside space-y-1">
          {Array.isArray(d.resolution_steps) ? d.resolution_steps.map((s: string, i: number) => (
            <li key={i} className="text-xs text-syzygy-grey/80 leading-relaxed">{s}</li>
          )) : <FormattedText text={d.resolution_steps} />}
        </ol>
      </SectionCard>
      {Array.isArray(d.kb_articles) && d.kb_articles.length > 0 && (
        <SectionCard title="Knowledge Base Articles" icon={BookOpen}>
          <ul className="space-y-1">
            {d.kb_articles.map((a: string, i: number) => (
              <li key={i} className="flex items-center gap-2 text-xs text-syzygy-grey/80">
                <span className="h-1 w-1 rounded-full bg-syzygy-gold/40 shrink-0" />
                {a}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}
      {d.needs_escalation && (
        <SectionCard title="Escalation Notice" icon={AlertTriangle} defaultOpen={true}>
          <p className="text-xs text-red-400/80 leading-relaxed">{d.escalation_reason || "This issue requires human intervention"}</p>
          {d.support_email && <p className="text-xs text-syzygy-grey/60 mt-1">Contact: <span className="text-syzygy-gold">{d.support_email}</span></p>}
        </SectionCard>
      )}
      <SectionCard title="Summary" icon={BarChart3}>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Confidence</p><p className="text-sm font-semibold text-syzygy-grey/80">{(d.confidence * 100).toFixed(0)}%</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Response Time</p><p className="text-sm font-semibold text-syzygy-grey/80 capitalize">{d.response_time_estimate || "immediate"}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Processed In</p><p className="text-sm font-semibold text-syzygy-grey/80">{d.elapsed_seconds}s</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Escalation Score</p><p className="text-sm font-semibold text-syzygy-grey/80">{d.escalation_score ? `${(d.escalation_score * 100).toFixed(0)}%` : "N/A"}</p></div>
        </div>
      </SectionCard>
    </div>
  );
}

function render_meeting(d: any) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-violet-500/30 text-violet-400 bg-violet-500/10"><Mic className="h-3 w-3" />{d.meeting_type?.replace(/_/g, " ") || "meeting"}</Badge>
        {Array.isArray(d.attendees) && d.attendees.map((a: string) => (
          <Badge key={a} className="border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30">{a}</Badge>
        ))}
        <Badge className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10">{d.action_items?.length || 0} action items</Badge>
      </div>
      <SectionCard title="Discussion Points" icon={Layers} defaultOpen={true}>
        {Array.isArray(d.discussion_points) && d.discussion_points.length > 0 ? (
          <ul className="space-y-1">
            {d.discussion_points.map((p: string, i: number) => (
              <li key={i} className="text-xs text-syzygy-grey/80 leading-relaxed flex items-start gap-2">
                <span className="h-1 w-1 rounded-full bg-syzygy-gold/40 shrink-0 mt-1.5" />
                {p}
              </li>
            ))}
          </ul>
        ) : <FormattedText text={d.summary} />}
      </SectionCard>
      {Array.isArray(d.decisions) && d.decisions.length > 0 && (
        <SectionCard title="Decisions Made" icon={Target}>
          <ul className="space-y-1">
            {d.decisions.map((dec: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-xs text-syzygy-grey/80">
                <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0 mt-0.5" />
                {dec}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}
      {Array.isArray(d.action_items) && d.action_items.length > 0 && (
        <SectionCard title="Action Items" icon={Target} defaultOpen={true}>
          <div className="space-y-1">
            {d.action_items.map((item: any, i: number) => (
              <div key={i} className="flex items-start gap-2 rounded-lg bg-syzygy-shadow/20 p-2">
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-400 shrink-0">{i + 1}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-syzygy-grey/80">{item.action || item.task}</p>
                  {item.assignee && <p className="text-[10px] text-syzygy-gold/60 mt-0.5">Assignee: {item.assignee}</p>}
                  {item.status && <Badge className="mt-1 border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30 capitalize">{item.status}</Badge>}
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
      {Array.isArray(d.blockers) && d.blockers.length > 0 && (
        <SectionCard title="Blockers" icon={AlertTriangle}>
          <ul className="space-y-1">
            {d.blockers.map((b: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-xs text-red-400/80">
                <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                {b}
              </li>
            ))}
          </ul>
        </SectionCard>
      )}
      {Array.isArray(d.email_drafts) && d.email_drafts.length > 0 && (
        <SectionCard title="Email Drafts" icon={FileText}>
          <div className="space-y-2">
            {d.email_drafts.map((draft: any, i: number) => (
              <div key={i} className="rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/50 p-3">
                <div className="flex items-center gap-2 text-xs mb-2">
                  <span className="font-medium text-syzygy-grey/60">To:</span>
                  <span className="text-syzygy-gold">{draft.to}</span>
                  <span className="text-syzygy-grey/30">|</span>
                  <span className="font-medium text-syzygy-grey/60">Subject:</span>
                  <span className="text-syzygy-grey/80">{draft.subject}</span>
                </div>
                <pre className="text-[11px] text-syzygy-grey/70 leading-relaxed whitespace-pre-wrap font-sans">{draft.body}</pre>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
      {Array.isArray(d.next_steps) && d.next_steps.length > 0 && (
        <SectionCard title="Recommended Next Steps" icon={ArrowRight}>
          <ol className="list-decimal list-inside space-y-1">
            {d.next_steps.map((s: string, i: number) => (
              <li key={i} className="text-xs text-syzygy-grey/80">{s}</li>
            ))}
          </ol>
        </SectionCard>
      )}
    </div>
  );
}

function render_sales(d: any) {
  const ls = d.lead_summary || {};
  const pa = d.pipeline_analysis || {};
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-emerald-500/30 text-emerald-400 bg-emerald-500/10"><TrendingUp className="h-3 w-3" />Score: {ls.score}/10</Badge>
        <Badge className={ls.status === "qualified" ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10" : ls.status === "nurture" ? "border-amber-500/30 text-amber-400 bg-amber-500/10" : "border-red-500/30 text-red-400 bg-red-500/10"}>{ls.status}</Badge>
        <Badge className="border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30 capitalize">{ls.company_size}</Badge>
        <Badge className="border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30 capitalize">{ls.relevance}</Badge>
      </div>
      <SectionCard title="Lead Qualification" icon={Target} defaultOpen={true}>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Title Level</p><p className="text-xs font-semibold text-syzygy-grey/80 capitalize">{ls.title_level?.replace(/_/g, " ")}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Company Size</p><p className="text-xs font-semibold text-syzygy-grey/80 capitalize">{ls.company_size}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Relevance</p><p className="text-xs font-semibold text-syzygy-grey/80 capitalize">{ls.relevance}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Action</p><p className="text-xs font-semibold text-syzygy-grey/80 capitalize">{ls.recommended_action?.replace(/_/g, " ") || "review"}</p></div>
        </div>
      </SectionCard>
      {Array.isArray(d.followup_sequence) && d.followup_sequence.length > 0 && (
        <SectionCard title="Follow-Up Sequence" icon={Zap} defaultOpen={true}>
          <div className="space-y-2">
            {d.followup_sequence.map((e: any, i: number) => (
              <div key={i} className="rounded-lg border border-syzygy-surface-border bg-syzygy-obsidian/50 p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-medium text-syzygy-gold/60 uppercase">{e.timing}</span>
                  <Badge className="border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30">#{i + 1}</Badge>
                </div>
                <p className="text-xs font-medium text-syzygy-grey/80 mb-1">{e.subject}</p>
                <pre className="text-[11px] text-syzygy-grey/60 leading-relaxed whitespace-pre-wrap font-sans">{e.body}</pre>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
      <SectionCard title="Pipeline Analysis" icon={BarChart3}>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Stage</p><p className="text-xs font-semibold text-syzygy-grey/80 capitalize">{pa.current_stage}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Next Stage</p><p className="text-xs font-semibold text-syzygy-grey/80 capitalize">{pa.recommended_next_stage}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Velocity</p><p className="text-xs font-semibold text-syzygy-grey/80 capitalize">{pa.pipeline_velocity}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Recommendation</p><p className="text-[11px] font-semibold text-syzygy-grey/80">{pa.recommendation}</p></div>
        </div>
      </SectionCard>
      {Array.isArray(d.next_steps) && <SectionCard title="Next Steps" icon={ArrowRight}><ol className="list-decimal list-inside space-y-1">{d.next_steps.map((s: string, i: number) => <li key={i} className="text-xs text-syzygy-grey/80">{s}</li>)}</ol></SectionCard>}
    </div>
  );
}

function render_legal(d: any) {
  const risk = d.risk_assessment || {};
  const riskColors: Record<string, string> = { critical: "border-red-500/30 text-red-400 bg-red-500/10", high: "border-orange-500/30 text-orange-400 bg-orange-500/10", medium: "border-yellow-500/30 text-yellow-400 bg-yellow-500/10", low: "border-green-500/30 text-green-400 bg-green-500/10" };
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-indigo-500/30 text-indigo-400 bg-indigo-500/10"><FileText className="h-3 w-3" />{d.contract_type?.replace(/_/g, " ")}</Badge>
        <Badge className={cn(riskColors[risk.overall_risk] || "border-syzygy-gold/30 text-syzygy-gold bg-syzygy-gold/10")}>{risk.overall_risk?.toUpperCase()}</Badge>
        <Badge className="border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30">Score: {risk.risk_score}/10</Badge>
      </div>
      <SectionCard title="Risk Assessment" icon={AlertTriangle} defaultOpen={true}>
        <p className="text-xs text-syzygy-grey/80 leading-relaxed mb-2">{risk.summary}</p>
        <div className="grid grid-cols-4 gap-2">
          {["critical", "high", "medium", "low"].map((lvl) => (
            <div key={lvl} className={`rounded-lg p-2 ${risk.risk_counts?.[lvl] > 0 ? "bg-syzygy-shadow/30" : "bg-syzygy-shadow/10 opacity-50"}`}>
              <p className="text-[10px] text-syzygy-grey/40 uppercase">{lvl}</p>
              <p className="text-sm font-bold text-syzygy-grey/80">{risk.risk_counts?.[lvl] || 0}</p>
            </div>
          ))}
        </div>
      </SectionCard>
      {Array.isArray(d.clauses) && d.clauses.length > 0 && (
        <SectionCard title={`Clauses (${d.clauses.length})`} icon={Layers} defaultOpen={true}>
          <div className="space-y-1">
            {d.clauses.map((c: any, i: number) => (
              <div key={i} className={`flex items-start gap-2 rounded-lg p-2 ${c.risk === "critical" ? "bg-red-500/5 border border-red-500/10" : c.risk === "high" ? "bg-orange-500/5" : "bg-syzygy-shadow/20"}`}>
                <Badge className={cn("shrink-0 mt-0.5", riskColors[c.risk] || "border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30")}>{c.risk}</Badge>
                <div className="min-w-0"><p className="text-xs font-medium text-syzygy-grey/80">{c.clause}</p><p className="text-[10px] text-syzygy-grey/50 mt-0.5">{c.note}</p></div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
      {Array.isArray(d.recommendations) && <SectionCard title="Recommendations" icon={CheckCircle2}><ol className="list-decimal list-inside space-y-1">{d.recommendations.map((r: string, i: number) => <li key={i} className="text-xs text-syzygy-grey/80">{r}</li>)}</ol></SectionCard>}
    </div>
  );
}

function render_procurement(d: any) {
  const req = d.requirements || {};
  const vendor = d.vendor_match || {};
  const po = d.purchase_order || {};
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Badge className="border-teal-500/30 text-teal-400 bg-teal-500/10"><Database className="h-3 w-3" />{po.po_id || "PO"}</Badge>
        <Badge className="border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30 capitalize">{req.category}</Badge>
        <Badge className={req.urgency === "critical" ? "border-red-500/30 text-red-400 bg-red-500/10" : "border-emerald-500/30 text-emerald-400 bg-emerald-500/10"}>{req.urgency}</Badge>
        <Badge className="border-syzygy-surface-border text-syzygy-grey/60 bg-syzygy-shadow/30">${Number(req.estimated_amount || 0).toLocaleString()}</Badge>
      </div>
      <SectionCard title="Vendor Match" icon={Target} defaultOpen={true}>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-syzygy-shadow/20 p-2 col-span-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Recommended</p><p className="text-sm font-semibold text-emerald-400">{vendor.recommended_vendor || "N/A"}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Tier</p><p className="text-xs font-semibold text-syzygy-grey/80 capitalize">{vendor.tier}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Rating</p><p className="text-xs font-semibold text-syzygy-grey/80">{vendor.rating}/5.0</p></div>
          {Array.isArray(vendor.alternatives) && vendor.alternatives.length > 0 && (
            <div className="rounded-lg bg-syzygy-shadow/20 p-2 col-span-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Alternatives</p><p className="text-xs text-syzygy-grey/70">{vendor.alternatives.join(", ")}</p></div>
          )}
        </div>
      </SectionCard>
      {Array.isArray(d.compliance_flags) && d.compliance_flags.length > 0 && (
        <SectionCard title="Compliance Flags" icon={Shield} defaultOpen={true}>
          <div className="space-y-1">
            {d.compliance_flags.map((f: any, i: number) => (
              <div key={i} className={`flex items-start gap-2 rounded-lg p-2 ${f.severity === "high" ? "bg-red-500/5 border border-red-500/10" : "bg-amber-500/5"}`}>
                <AlertTriangle className={`h-3 w-3 shrink-0 mt-0.5 ${f.severity === "high" ? "text-red-400" : "text-amber-400"}`} />
                <div><p className="text-xs font-medium text-syzygy-grey/80 capitalize">{f.flag?.replace(/_/g, " ")}</p><p className="text-[10px] text-syzygy-grey/50">{f.detail}</p></div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}
      <SectionCard title="Purchase Order" icon={FileText} defaultOpen={true}>
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">PO ID</p><p className="text-xs font-semibold text-syzygy-grey/80">{po.po_id}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Amount</p><p className="text-xs font-semibold text-syzygy-grey/80">${Number(po.amount || 0).toLocaleString()}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Approver</p><p className="text-xs font-semibold text-syzygy-grey/80">{po.approver}</p></div>
          <div className="rounded-lg bg-syzygy-shadow/20 p-2"><p className="text-[10px] text-syzygy-grey/40 uppercase">Approval Levels</p><p className="text-xs font-semibold text-syzygy-grey/80">{po.approval_levels}</p></div>
          {po.requires_escalation && (
            <div className="col-span-2 rounded-lg bg-red-500/5 border border-red-500/10 p-2"><p className="text-[10px] text-red-400 font-medium">⚠ Escalation Required — compliance flags detected</p></div>
          )}
        </div>
      </SectionCard>
      {Array.isArray(d.next_steps) && <SectionCard title="Next Steps" icon={ArrowRight}><ol className="list-decimal list-inside space-y-1">{d.next_steps.map((s: string, i: number) => <li key={i} className="text-xs text-syzygy-grey/80">{s}</li>)}</ol></SectionCard>}
    </div>
  );
}

export function WorkflowResult({ workflow, data }: { workflow: string; data: any }) {
  const inner = data?.result || data;

  if (!inner) return <p className="text-xs text-syzygy-grey/40 italic">No result data</p>;

  const renderers: Record<string, (d: any) => React.ReactNode> = {
    coding: render_coding,
    finetune: render_finetune,
    support: render_support,
    meeting: render_meeting,
    sales: render_sales,
    legal: render_legal,
    procurement: render_procurement,
    research: render_research,
    content: render_content,
    debate: render_debate,
    task_decomposition: render_task_decomposition,
    audit: render_audit,
    test_gen: render_test_gen,
    summary: render_summary,
    compliance: render_compliance,
    qa_bot: render_qa_bot,
    translate: render_translate,
    interview_coach: render_interview_coach,
    data_analyzer: render_data_analyzer,
    api_designer: render_api_designer,
    agentic_rag: render_agentic_rag,
    report_gen: render_report_gen,
    data_pipeline: render_data_pipeline,
    ci_piper: render_ci_piper,
  };

  const renderFn = renderers[workflow];
  if (renderFn) {
    return <div className="space-y-3 animate-fade-in-up">{renderFn(inner)}</div>;
  }

  return <FormattedText text={JSON.stringify(inner, null, 2)} />;
}
