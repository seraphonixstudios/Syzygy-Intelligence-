import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
    const response = NextResponse.next();
    
    // Generate a unique nonce for inline scripts (prevents injected scripts from running)
    const nonce = crypto.randomUUID();
    
    // Enhanced CSP that uses nonces for inline scripts.
    // NOTE: `next dev` (webpack eval source-maps + React Refresh runtime) requires
    // 'unsafe-eval' to boot at all — without it the client bundle throws EvalError
    // and the page freezes on its server-rendered state. Production stays strict.
    const isDev = process.env.NODE_ENV === "development";
    const scriptSrc = isDev
        ? `script-src 'self' 'unsafe-eval' 'nonce-${nonce}' https://js.stripe.com`
        : `script-src 'self' 'nonce-${nonce}' https://js.stripe.com`;
    // In dev the API runs on a different origin (:8001) than the frontend (:3000),
    // so connect-src must allow it or every browser->backend fetch is blocked.
    const connectSrc = isDev
        ? "connect-src 'self' http://localhost:8000 http://localhost:8001 ws://localhost:8000 ws://localhost:8001 https://api.stripe.com wss:"
        : "connect-src 'self' https://api.stripe.com wss:";
    response.headers.set(
        "Content-Security-Policy",
        [
            "default-src 'self'",
            scriptSrc,
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: blob:",
            "font-src 'self' data: https://fonts.gstatic.com",
            connectSrc,
            "frame-src 'self' https://js.stripe.com",
        ].join("; ")
    );
    
    // Store nonce in response headers so Next.js can access it in _document or app layout
    response.headers.set("X-Nonce", nonce);
    
    return response;
}

export const config = {
    matcher: "/:path*",
};
