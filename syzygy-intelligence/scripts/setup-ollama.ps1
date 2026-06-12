# Setup Ollama for Syzygy local development
# Run from repo root: .\scripts\setup-ollama.ps1
# Requires: Windows (Ollama installed via MSI), or Docker (CPU or GPU)
# Optional: NVIDIA GPU + nvidia-container-toolkit for GPU acceleration

param(
  [switch]$Docker,
  [switch]$SkipPull
)

$ErrorActionPreference = "Stop"

# Syzygy expects custom-tagged model names (e.g. qwen3:8b-gpu).
# We pull the base model, then create the custom tag.
$MODELS = @(
  @{ PullName = "qwen2.5:7b";        TagName = "qwen3:8b-gpu";           ConfigKey = "default/critic/synthesis/coding"; Gpu = $true;  SizeCpu = "~4.7 GB" },
  @{ PullName = "qwen2.5:7b";        TagName = "";                        ConfigKey = "default (CPU alternative)";       Gpu = $false; SizeCpu = "~4.7 GB" },
  @{ PullName = "dolphin-llama3:8b"; TagName = "dolphin-llama3:8b-gpu";  ConfigKey = "creative/fast";                   Gpu = $true;  SizeCpu = "~4.5 GB" },
  @{ PullName = "llama3.2:3b";       TagName = "";                        ConfigKey = "fast/cpu (CPU alternative)";      Gpu = $false; SizeCpu = "~2.0 GB" },
  @{ PullName = "llava:13b";         TagName = "llava:13b-gpu";           ConfigKey = "vision";                          Gpu = $true;  SizeCpu = "~8.0 GB" },
  @{ PullName = "llava:7b";          TagName = "";                        ConfigKey = "vision-cpu (CPU alternative)";    Gpu = $false; SizeCpu = "~4.5 GB" }
)

Write-Host "=== Syzygy — Ollama Setup ===" -ForegroundColor Cyan
Write-Host ""

# ─── Docker path ──────────────────────────────────────────────
if ($Docker) {
  Write-Host "Using Docker Compose (CPU-only override)" -ForegroundColor Yellow
  docker compose -f docker-compose.yml -f docker-compose.ollama-cpu.yml up -d ollama
  if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed to start Ollama" }
  Write-Host "Waiting for Ollama container to be ready..." -ForegroundColor Yellow
  Start-Sleep -Seconds 5
  docker exec syzygy-ollama ollama pull qwen2.5:7b
  docker exec syzygy-ollama ollama cp qwen2.5:7b qwen3:8b-gpu
  docker exec syzygy-ollama ollama pull dolphin-llama3:8b
  docker exec syzygy-ollama ollama cp dolphin-llama3:8b dolphin-llama3:8b-gpu
  docker exec syzygy-ollama ollama pull llava:13b
  docker exec syzygy-ollama ollama cp llava:13b llava:13b-gpu
  Write-Host "Done. Models pulled and tagged inside container." -ForegroundColor Green
  Write-Host ""
  Write-Host "Backend env (SYZYGY_OLLAMA_BASE_URL=http://ollama:11434 is already set in docker-compose.yml)"
  exit 0
}

# ─── Check if Ollama is installed ─────────────────────────────
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
  Write-Host "Ollama not found. Downloading..." -ForegroundColor Yellow
  $installer = "$env:TEMP\ollama-setup.exe"
  Write-Host "  Downloading from https://ollama.com/download/windows ..."
  Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer
  Write-Host "  Running installer (requires admin)..." -ForegroundColor Yellow
  Start-Process -Wait -FilePath $installer -ArgumentList "/S"
  Remove-Item $installer
  # Refresh PATH
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
  $ollama = Get-Command ollama -ErrorAction Stop
  Write-Host "  Ollama installed: $($ollama.Source)" -ForegroundColor Green
} else {
  Write-Host "Ollama found: $($ollama.Source)" -ForegroundColor Green
}

# ─── Ensure Ollama is running ─────────────────────────────────
$ollamaRunning = $false
try {
  $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
  $ollamaRunning = $true
} catch {
  Write-Host "Ollama server not running. Starting..." -ForegroundColor Yellow
  Start-Process -WindowStyle Hidden ollama -ArgumentList "serve"
  Start-Sleep -Seconds 3
  # Wait for it to be ready
  $maxWait = 15
  for ($i = 0; $i -lt $maxWait; $i++) {
    try {
      $null = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
      $ollamaRunning = $true
      break
    } catch {
      Start-Sleep -Seconds 1
    }
  }
}
if (-not $ollamaRunning) {
  throw "Could not start Ollama server on http://localhost:11434"
}
Write-Host "Ollama server is running on http://localhost:11434" -ForegroundColor Green

# ─── Model management ─────────────────────────────────────────
if ($SkipPull) {
  Write-Host "Skipping model pull (--SkipPull)" -ForegroundColor Yellow
} else {
  Write-Host ""
  Write-Host "Recommended models for Syzygy:" -ForegroundColor Cyan

  # Detect GPU (check for NVIDIA GPU)
  $hasGPU = $false
  try {
    $nvidia = Get-CimInstance -ClassName Win32_VideoController | Where-Object { $_.Name -match "NVIDIA" }
    if ($nvidia) { $hasGPU = $true }
  } catch {}

  if ($hasGPU) {
    $active = $MODELS | Where-Object { $_.Gpu }
    Write-Host "  NVIDIA GPU detected → using full-size models with custom tags" -ForegroundColor Yellow
  } else {
    $active = $MODELS | Where-Object { -not $_.Gpu }
    Write-Host "  No NVIDIA GPU detected → using CPU-friendly models" -ForegroundColor Yellow
  }
  Write-Host ""

  $currentModels = (ollama list) -join "`n"
  foreach ($m in $active) {
    $pullName = $m.PullName
    $tagName = $m.TagName
    $key = $m.ConfigKey
    $sizeInfo = " ($($m.SizeCpu))"

    $basePulled = $currentModels -match [regex]::Escape($pullName.Split(':')[0])
    if (-not $basePulled) {
      Write-Host "  Pulling $pullName$sizeInfo → $key" -ForegroundColor Yellow
      ollama pull $pullName
      if ($LASTEXITCODE -eq 0) {
        Write-Host "  [done] $pullName" -ForegroundColor Green
      } else {
        Write-Host "  [failed] $pullName — skipping" -ForegroundColor Red
        continue
      }
    } else {
      Write-Host "  [already pulled] $pullName" -ForegroundColor Green
    }

    if ($tagName) {
      $tagExists = $currentModels -match [regex]::Escape($tagName)
      if (-not $tagExists) {
        Write-Host "  Creating tag: $pullName → $tagName" -ForegroundColor Yellow
        ollama cp $pullName $tagName
        if ($LASTEXITCODE -eq 0) {
          Write-Host "  [tagged] $tagName" -ForegroundColor Green
        }
      } else {
        Write-Host "  [tag exists] $tagName" -ForegroundColor Green
      }
    }
  }
}

# ─── Connection test ──────────────────────────────────────────
Write-Host ""
Write-Host "Testing Ollama connection..." -ForegroundColor Cyan
try {
  $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
  $count = $tags.models.Count
  Write-Host "OK — $count model(s) available" -ForegroundColor Green
} catch {
  Write-Host "FAIL — Ollama responded but /api/tags failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. The backend .env is already configured with the custom tags:" -ForegroundColor White
Write-Host "     SYZYGY_OLLAMA_BASE_URL=http://localhost:11434" -ForegroundColor Gray
if ($hasGPU) {
  Write-Host "     SYZYGY_DEFAULT_MODEL=qwen3:8b-gpu  (=> qwen2.5:7b)" -ForegroundColor Gray
  Write-Host "     SYZYGY_VISION_MODEL=llava:13b-gpu  (=> llava:13b)" -ForegroundColor Gray
} else {
  Write-Host "     SYZYGY_DEFAULT_MODEL=qwen2.5:7b     (direct, no tag)" -ForegroundColor Gray
  Write-Host "     SYZYGY_VISION_MODEL=llava:7b        (CPU-friendly)" -ForegroundColor Gray
}
Write-Host ""
Write-Host "     To use the default .env.example values as-is, the tags are already created." -ForegroundColor White
Write-Host ""
Write-Host "  2. Start the backend:" -ForegroundColor White
Write-Host "     cd backend && uvicorn app.main:app --reload --port 8001" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Verify:" -ForegroundColor White
Write-Host "     curl http://localhost:11434/api/generate -d '{\"model\":\"qwen3:8b-gpu\",\"prompt\":\"Hello\"}'" -ForegroundColor Gray
