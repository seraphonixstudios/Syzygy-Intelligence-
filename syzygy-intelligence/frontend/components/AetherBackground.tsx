"use client";

import { useEffect, useRef } from "react";

const SIGILS = ["☉", "☽", "☿", "♄", "♃", "♂", "♀", "☊", "☋"];
const COLORS = ["#d4a843", "#e8c35a", "#8a7f7a", "#f0d080", "#b8860b"];

interface Particle {
  x: number;
  y: number;
  size: number;
  speedX: number;
  speedY: number;
  opacity: number;
  life: number;
  maxLife: number;
  color: string;
}

export function AetherBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let particles: Particle[] = [];
    let running = true;

    const onVisibility = () => { running = !document.hidden; if (running) animId = requestAnimationFrame(animate); };
    document.addEventListener("visibilitychange", onVisibility);

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const spawnParticle = () => {
      if (particles.length > 60) return;
      particles.push({
        x: Math.random() * canvas.width,
        y: canvas.height + 20,
        size: Math.random() * 3 + 1,
        speedX: (Math.random() - 0.5) * 0.6,
        speedY: -(Math.random() * 0.8 + 0.3),
        opacity: 0,
        life: 0,
        maxLife: 200 + Math.random() * 300,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
      });
    };

    const animate = () => {
      if (!running) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (Math.random() < 0.15) spawnParticle();

      particles = particles.filter((p) => p.life < p.maxLife);

      for (const p of particles) {
        p.x += p.speedX;
        p.y += p.speedY;
        p.life++;

        if (p.life < 30) p.opacity = p.life / 30 * 0.5;
        else if (p.life > p.maxLife - 30) p.opacity = (p.maxLife - p.life) / 30 * 0.5;
        else p.opacity = 0.5;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color.replace(")", `, ${p.opacity})`).replace("rgb", "rgba");
        ctx.fill();

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2);
        const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 3);
        glow.addColorStop(0, p.color.replace(")", `, ${p.opacity * 0.3})`).replace("rgb", "rgba"));
        glow.addColorStop(1, "transparent");
        ctx.fillStyle = glow;
        ctx.fill();
      }

      animId = requestAnimationFrame(animate);
    };

    animId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animId);
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <>
      <canvas
        ref={canvasRef}
        className="pointer-events-none fixed inset-0 z-0"
      />
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        {SIGILS.map((sigil, i) => (
          <span
            key={i}
            className="animate-sigil-pulse absolute select-none font-alchemical text-6xl"
            style={{
              left: `${10 + (i * 37) % 80}%`,
              top: `${5 + (i * 53) % 90}%`,
              animationDelay: `${i * 2.5}s`,
              color: COLORS[i % COLORS.length],
              opacity: 0.06,
              transform: `rotate(${i * 45}deg)`,
              fontSize: `${3 + (i % 3) * 1.5}rem`,
            }}
          >
            {sigil}
          </span>
        ))}
        <span
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 animate-ring-expand select-none rounded-full border border-syzygy-gold/20"
          style={{ width: 200, height: 200, animationDelay: "0s" }}
        />
        <span
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 animate-ring-expand select-none rounded-full border border-syzygy-gold/10"
          style={{ width: 200, height: 200, animationDelay: "1s" }}
        />
        <span
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 animate-ring-expand select-none rounded-full border border-syzygy-gold/10"
          style={{ width: 200, height: 200, animationDelay: "2s" }}
        />
      </div>
    </>
  );
}
