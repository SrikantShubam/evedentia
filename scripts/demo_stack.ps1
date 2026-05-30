param(
  [switch]$KeepRunning,
  [int]$BackendPort = 0,
  [int]$FrontendPort = 0
)

$ErrorActionPreference = "Stop"

function Get-FreePort {
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
  $listener.Start()
  $port = $listener.LocalEndpoint.Port
  $listener.Stop()
  return $port
}

function Wait-ForUrl {
  param(
    [string]$Url,
    [int]$TimeoutSeconds = 20
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      return Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }

  throw "Timed out waiting for $Url"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendPort = if ($BackendPort -gt 0) { $BackendPort } else { Get-FreePort }
$frontendPort = if ($FrontendPort -gt 0) { $FrontendPort } else { Get-FreePort }
$backendUrl = "http://127.0.0.1:$backendPort"
$frontendUrl = "http://127.0.0.1:$frontendPort"
$logDir = Join-Path $repoRoot "outputs"
$backendOut = Join-Path $logDir "demo-backend.log"
$backendErr = Join-Path $logDir "demo-backend.err.log"
$frontendOut = Join-Path $logDir "demo-frontend.log"
$frontendErr = Join-Path $logDir "demo-frontend.err.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$backend = Start-Process `
  -FilePath python `
  -ArgumentList "-m", "uvicorn", "--app-dir", "src", "evidentia.api:app", "--host", "127.0.0.1", "--port", "$backendPort" `
  -WorkingDirectory $repoRoot `
  -WindowStyle Hidden `
  -RedirectStandardOutput $backendOut `
  -RedirectStandardError $backendErr `
  -PassThru

$frontendCommand = "`$env:NEXT_PUBLIC_EVIDENTIA_API='$backendUrl'; npm.cmd run start -- --hostname 127.0.0.1 --port $frontendPort"
$frontend = Start-Process `
  -FilePath powershell `
  -ArgumentList "-NoProfile", "-Command", $frontendCommand `
  -WorkingDirectory (Join-Path $repoRoot "docs\\frontend") `
  -WindowStyle Hidden `
  -RedirectStandardOutput $frontendOut `
  -RedirectStandardError $frontendErr `
  -PassThru

try {
  Wait-ForUrl -Url "$backendUrl/health" | Out-Null
  Wait-ForUrl -Url "$frontendUrl/tournament/new" | Out-Null

  $player = @{
    id = "agency-a"
    team = "Edge Agency"
    skills = @("python", "sales")
    budget_validate_usd = 2500
    budget_build_usd = 10000
    budget_reach_usd = 1500
    weeks_to_ship = 8
    risk = "med"
    max_llm_calls_per_tournament = 200
    max_paid_queries_per_tournament = 50
    max_reentry_rounds = 1
  } | ConvertTo-Json -Depth 5

  $idea = @{
    id = "demo-idea-1"
    label = "SMB invoicing dispute resolver"
    anchor_slug = "smb-invoicing"
    incumbent = "FreshBooks"
    cohort = "small agencies managing client invoice disputes"
    pain_hypothesis = "Agencies will pay to cut invoice dispute resolution time and recover more cash without manual email loops."
    kill_condition = @{
      description = "No durable market for invoice dispute tooling"
      gate_name = "parent_market_exists"
    }
    evidence_ids = @("sig-1", "sig-2", "sig-3", "sig-4")
    search_queries = @("invoice dispute software agencies", "accounts receivable dispute complaints")
    origin = "manual"
    gate_profile = "consumer_app"
    gate_profile_source = "explicit"
    parent_idea_id = $null
  }

  Invoke-RestMethod -Uri "$backendUrl/player" -Method Post -ContentType "application/json" -Body $player | Out-Null

  $tournament = @{
    tournament_id = "demo-tournament-2026-04-28"
    player_id = "agency-a"
    ideas = @($idea)
    gate_profile = "consumer_app"
  } | ConvertTo-Json -Depth 8

  Invoke-RestMethod -Uri "$backendUrl/tournament" -Method Post -ContentType "application/json" -Body $tournament | Out-Null

  $boardUrl = "$frontendUrl/tournament/demo-tournament-2026-04-28"
  $memoUrl = "$frontendUrl/tournament/demo-tournament-2026-04-28/memo"
  $playerUrl = "$frontendUrl/player"
  $builderUrl = "$frontendUrl/tournament/new"

  $boardStatus = (Invoke-WebRequest -Uri $boardUrl -UseBasicParsing -TimeoutSec 5).StatusCode
  $memoStatus = (Invoke-WebRequest -Uri $memoUrl -UseBasicParsing -TimeoutSec 5).StatusCode
  $playerStatus = (Invoke-WebRequest -Uri $playerUrl -UseBasicParsing -TimeoutSec 5).StatusCode
  $builderStatus = (Invoke-WebRequest -Uri $builderUrl -UseBasicParsing -TimeoutSec 5).StatusCode

  [pscustomobject]@{
    backend = $backendUrl
    backend_root = "$backendUrl/"
    backend_health = "$backendUrl/health"
    frontend = $frontendUrl
    tournament_board = $boardUrl
    tournament_board_status = $boardStatus
    tournament_memo = $memoUrl
    tournament_memo_status = $memoStatus
    player_editor = $playerUrl
    player_editor_status = $playerStatus
    tournament_builder = $builderUrl
    tournament_builder_status = $builderStatus
    keep_running = [bool]$KeepRunning
    backend_pid = $backend.Id
    frontend_pid = $frontend.Id
  }

  if ($KeepRunning) {
    Write-Host ""
    Write-Host "Demo stack is running. Press Ctrl+C to stop this launcher."
    while ($true) {
      Start-Sleep -Seconds 5
    }
  }
}
finally {
  if ($backend -and !$backend.HasExited) {
    Stop-Process -Id $backend.Id -Force
  }
  if ($frontend -and !$frontend.HasExited) {
    Stop-Process -Id $frontend.Id -Force
  }
}
