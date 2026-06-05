export default function Loading() {
  return (
    <div className="flex h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-6">
        <div className="animate-brand-glow">
          <img
            src="/branding/pagetop.logo.png"
            alt="Syzygy"
            className="h-32 w-auto brightness-110"
          />
        </div>
        <img
          src="/branding/syzygy.logo.png"
          alt="SYZYGY"
          className="h-18 w-auto brightness-110 opacity-80"
        />
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
