import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { randomBytes } from "crypto";

export function middleware(request: NextRequest) {
    const response = NextResponse.next();
    
    // Generate a unique nonce for inline scripts (prevents injected scripts from running)
    // Base64-encode to safely embed in CSP header
    const nonce = randomBytes(16).toString("base64");
    
    // Enhanced CSP that removes 'unsafe-eval' and uses nonces for inline scripts
    // This prevents inline script injection attacks while allowing necessary functionality
    response.headers.set(
        "Content-Security-Policy",
        [
            "default-src 'self'",
            `script-src 'self' 'nonce-${nonce}' https://js.stripe.com`,
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: blob:",
            "font-src 'self' data: https://fonts.gstatic.com",
            "connect-src 'self' https://api.stripe.com wss:",
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
