import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4">
      <h1 className="text-6xl font-bold text-zinc-600">404</h1>
      <p className="text-lg text-zinc-400">Page not found</p>
      <Link
        href="/"
        className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-700"
      >
        Go home
      </Link>
    </div>
  );
}
