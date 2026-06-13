# Generate production secrets for Syzygy Intelligence.
# Run from repo root: .\scripts\generate-secrets.ps1
# Output: .env.production file with secure random values.

param(
  [string]$OutputFile = ".env.production",
  [int]$SecretKeyBytes = 32,
  [int]$PasswordLength = 24
)

$ErrorActionPreference = "Stop"

function New-RandomString {
  param([int]$Length = 24, [string]$Chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#%^&*()-_=+")
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $bytes = [byte[]]::new($Length)
  $rng.GetBytes($bytes)
  $rng.Dispose()
  -join ($bytes | ForEach-Object { $Chars[$_ % $Chars.Length] })
}

function New-HexString {
  param([int]$Bytes = 32)
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $bytes = [byte[]]::new($Bytes)
  $rng.GetBytes($bytes)
  $rng.Dispose()
  -join ($bytes | ForEach-Object { $_.ToString("x2") })
}

Write-Host "=== Syzygy — Production Secrets Generator ===" -ForegroundColor Cyan
Write-Host ""

$secretKey  = New-HexString -Bytes $SecretKeyBytes
$dbPassword = New-RandomString -Length $PasswordLength
$neo4jPass  = New-RandomString -Length $PasswordLength
$jwtSecret  = New-HexString -Bytes 32
$apiKeySalt = New-HexString -Bytes 16
$redisPass  = New-RandomString -Length $PasswordLength

$content = @"
# ═══════════════════════════════════════════════════════════════
# Syzygy Intelligence — Production Secrets
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC")
# WARNING: Keep this file secure! Never commit to version control.
# ═══════════════════════════════════════════════════════════════

# General
SYZYGY_ENV=production
SYZYGY_SECRET_KEY=$secretKey
SYZYGY_JWT_SECRET=$jwtSecret
SYZYGY_API_KEY_SALT=$apiKeySalt
SYZYGY_LOG_FORMAT=json
SYZYGY_LOG_LEVEL=INFO

# PostgreSQL
SYZYGY_DB_PASSWORD=$dbPassword
SYZYGY_DB_NAME=syzygy
SYZYGY_DB_USER=syzygy
SYZYGY_DB_HOST=postgres
SYZYGY_DB_PORT=5432

# Redis (optional password)
SYZYGY_REDIS_URL=redis://:$redisPass@redis:6379/0

# Neo4j
SYZYGY_NEO4J_PASSWORD=$neo4jPass
SYZYGY_NEO4J_USER=neo4j

# Ollama
SYZYGY_OLLAMA_BASE_URL=http://ollama:11434

# CORS — Replace with your actual domain
SYZYGY_CORS_ORIGINS=https://app.example.com,https://api.example.com
SYZYGY_OAUTH_REDIRECT_URL=https://api.example.com/api/auth/oauth

# Next.js public URLs (inlined at build time)
NEXT_PUBLIC_SYZYGY_API_URL=https://api.example.com
NEXT_PUBLIC_SYZYGY_WS_URL=wss://api.example.com/ws

# Stripe — Set real keys
SYZYGY_STRIPE_SECRET_KEY=
SYZYGY_STRIPE_PUBLISHABLE_KEY=
SYZYGY_STRIPE_WEBHOOK_SECRET=

# Email — Choose one provider
SYZYGY_EMAIL_PROVIDER=console
# SYZYGY_SENDGRID_API_KEY=
# SYZYGY_SES_REGION=us-east-1
# SYZYGY_SES_ACCESS_KEY_ID=
# SYZYGY_SES_SECRET_ACCESS_KEY=

# OAuth — Set real client IDs/secrets
SYZYGY_GOOGLE_CLIENT_ID=
SYZYGY_GOOGLE_CLIENT_SECRET=
SYZYGY_GITHUB_CLIENT_ID=
SYZYGY_GITHUB_CLIENT_SECRET=
"@

$content | Out-File -FilePath $OutputFile -Encoding utf8NoBOM

Write-Host "Secrets written to: $OutputFile" -ForegroundColor Green
Write-Host ""
Write-Host "  SYZYGY_SECRET_KEY : $secretKey" -ForegroundColor DarkYellow
Write-Host "  SYZYGY_DB_PASSWORD: $dbPassword" -ForegroundColor DarkYellow
Write-Host "  SYZYGY_NEO4J_PASS : $neo4jPass"  -ForegroundColor DarkYellow
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Red
Write-Host "  1. Edit $OutputFile and replace placeholder values (CORS, OAuth, Stripe, domain)."
Write-Host "  2. Source it before deploying: set -o allexport; source $OutputFile; set +o allexport"
Write-Host "  3. Or pass each var individually to docker compose: --env-file $OutputFile"
Write-Host "  4. NEVER commit $OutputFile to git. Add it to .gitignore."
Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
