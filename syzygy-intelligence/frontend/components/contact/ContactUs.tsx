"use client";

import { Mail, ExternalLink } from "lucide-react";

const EMAIL = "seraphonixstudios@gmail.com";
const TWITTER = "https://x.com/seraphonixS";
const TWITTER_HANDLE = "@seraphonixS";

export function ContactUs() {
  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <Mail className="h-8 w-auto text-syzygy-gold" />
        <div>
          <h1 className="syzygy-title text-2xl font-bold tracking-wider">Contact Us</h1>
          <p className="mt-0.5 text-xs text-syzygy-grey/60">Get in touch with the team</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <a
          href={`mailto:${EMAIL}`}
          className="group rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-6 transition-all hover:border-syzygy-gold/40 hover:bg-syzygy-shadow/50"
        >
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-syzygy-gold/10">
            <Mail className="h-6 w-6 text-syzygy-gold" />
          </div>
          <h3 className="font-alchemical text-lg tracking-wider text-syzygy-gold">Email</h3>
          <p className="mt-1 text-sm text-syzygy-grey/60">{EMAIL}</p>
          <p className="mt-2 text-xs text-syzygy-gold/60 group-hover:text-syzygy-gold">Send us a message →</p>
        </a>

        <a
          href={TWITTER}
          target="_blank"
          rel="noopener noreferrer"
          className="group rounded-xl border border-syzygy-surface-border bg-syzygy-shadow/30 p-6 transition-all hover:border-syzygy-gold/40 hover:bg-syzygy-shadow/50"
        >
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-syzygy-gold/10">
            <ExternalLink className="h-6 w-6 text-syzygy-gold" />
          </div>
          <h3 className="font-alchemical text-lg tracking-wider text-syzygy-gold">Twitter / X</h3>
          <p className="mt-1 text-sm text-syzygy-grey/60">{TWITTER_HANDLE}</p>
          <p className="mt-2 text-xs text-syzygy-gold/60 group-hover:text-syzygy-gold">Follow us →</p>
        </a>
      </div>
    </div>
  );
}
