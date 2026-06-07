export default function Loading() {
  return (
    <div className="flex h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-6">
        <div className="animate-brand-glow">
          <span className="font-cinzel text-5xl font-bold tracking-[0.3em] text-syzygy-gold">
            SYZYGY
          </span>
        </div>
        <span className="font-cinzel text-sm tracking-[0.5em] text-syzygy-grey/40">
          INTELLIGENCE
        </span>
        <div className="flex flex-col items-center gap-3">
          <div className="ouroboros-ring h-10 w-10" />
          <p className="text-xs text-syzygy-grey/60 animate-pulse">
            Solve et Coagula...
          </p>
        </div>
      </div>
    </div>
  );
}
