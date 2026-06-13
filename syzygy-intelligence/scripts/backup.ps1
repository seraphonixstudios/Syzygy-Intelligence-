# Manual database backup for Syzygy Intelligence.
# Run from repo root: .\scripts\backup.ps1
# Requires: Running PostgreSQL container (syzygy-postgres) or local psql.

param(
  [string]$OutputDir = "./backups",
  [int]$RetentionDays = 30,
  [switch]$Docker
)

$ErrorActionPreference = "Stop"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Filename = "syzygy-db-$Timestamp.sql"
$Path = Join-Path $OutputDir $Filename

# Ensure output directory exists
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Write-Host "=== Syzygy — Database Backup ===" -ForegroundColor Cyan
Write-Host ""

if ($Docker) {
  # Backup from the running Docker PostgreSQL container
  Write-Host "Backing up from Docker container 'syzygy-postgres'..." -ForegroundColor Yellow

  $user = $env:SYZYGY_DB_USER ?? "syzygy"
  $pass = $env:SYZYGY_DB_PASSWORD ?? "syzygy_secret"
  $db   = $env:SYZYGY_DB_NAME ?? "syzygy"

  docker exec syzygy-postgres pg_dump --no-owner --no-acl -U $user -d $db > $Path 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Backup via Docker failed. Is 'syzygy-postgres' running?" -ForegroundColor Red
    Remove-Item $Path -ErrorAction SilentlyContinue
    exit 1
  }
} else {
  # Backup using local psql
  Write-Host "Backing up with local psql..." -ForegroundColor Yellow

  $env:PGPASSWORD = $env:SYZYGY_DB_PASSWORD ?? "syzygy_secret"
  $hostName = $env:SYZYGY_DB_HOST ?? "localhost"
  $port     = $env:SYZYGY_DB_PORT ?? 5432
  $user     = $env:SYZYGY_DB_USER ?? "syzygy"
  $db       = $env:SYZYGY_DB_NAME ?? "syzygy"

  pg_dump --no-owner --no-acl -h $hostName -p $port -U $user -d $db > $Path 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pg_dump failed. Is PostgreSQL running and accessible?" -ForegroundColor Red
    Remove-Item $Path -ErrorAction SilentlyContinue
    exit 1
  }
}

# Compress
$GzPath = "$Path.gz"
if (Get-Command gzip -ErrorAction SilentlyContinue) {
  gzip -f $Path
  $Path = $GzPath
} elseif (Get-Command Compress-Archive -ErrorAction SilentlyContinue) {
  Compress-Archive -Path $Path -DestinationPath "$Path.zip" -CompressionLevel Optimal
  Remove-Item $Path -ErrorAction SilentlyContinue
  $Path = "$Path.zip"
}

$size = (Get-Item $Path).Length / 1MB
Write-Host "Backup created: $Path" -ForegroundColor Green
Write-Host "Size: $([math]::Round($size, 2)) MB" -ForegroundColor Green

# Cleanup old backups
$oldFiles = Get-ChildItem $OutputDir -Filter "syzygy-db-*" | Where-Object {
  $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays)
}
foreach ($f in $oldFiles) {
  Remove-Item $f.FullName -Force
  Write-Host "Removed old backup: $($f.Name)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
