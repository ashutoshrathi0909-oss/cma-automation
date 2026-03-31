# Start Cloudflare Tunnel and auto-update Vercel NEXT_PUBLIC_API_URL
# Usage: Right-click → Run with PowerShell, or run from terminal:
#   powershell -ExecutionPolicy Bypass -File scripts/start-tunnel.ps1

$cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"

Write-Host "Starting Cloudflare Tunnel..." -ForegroundColor Cyan

# Start cloudflared and capture output
$process = Start-Process -FilePath $cloudflared -ArgumentList "tunnel", "--url", "http://localhost:8000" -PassThru -RedirectStandardError "$env:TEMP\cloudflared.log" -NoNewWindow

# Wait for the tunnel URL to appear in the log
$tunnelUrl = $null
$maxWait = 30
$waited = 0

while (-not $tunnelUrl -and $waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++
    if (Test-Path "$env:TEMP\cloudflared.log") {
        $content = Get-Content "$env:TEMP\cloudflared.log" -Raw
        if ($content -match "https://[a-z0-9-]+\.trycloudflare\.com") {
            $tunnelUrl = $Matches[0]
        }
    }
}

if (-not $tunnelUrl) {
    Write-Host "ERROR: Could not detect tunnel URL after ${maxWait}s" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Tunnel URL: $tunnelUrl" -ForegroundColor Green
Write-Host ""

# Update .env file
$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    $envContent = $envContent -replace "BACKEND_URL=https://[^\s]+", "BACKEND_URL=$tunnelUrl"
    Set-Content $envFile $envContent -NoNewline
    Write-Host "Updated .env BACKEND_URL" -ForegroundColor Green
}

# Try to update Vercel env var if vercel CLI is available
$vercelInstalled = Get-Command vercel -ErrorAction SilentlyContinue
if ($vercelInstalled) {
    Write-Host "Updating Vercel NEXT_PUBLIC_API_URL..." -ForegroundColor Cyan
    vercel env rm NEXT_PUBLIC_API_URL production -y 2>$null
    echo $tunnelUrl | vercel env add NEXT_PUBLIC_API_URL production
    Write-Host "Vercel env updated. Run 'vercel --prod' to redeploy." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ACTION NEEDED: Update Vercel manually:" -ForegroundColor Yellow
    Write-Host "  1. Go to Vercel Dashboard -> Settings -> Environment Variables" -ForegroundColor Yellow
    Write-Host "  2. Set NEXT_PUBLIC_API_URL = $tunnelUrl" -ForegroundColor Yellow
    Write-Host "  3. Redeploy (Deployments -> latest -> Redeploy, no cache)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Tunnel is running. Press Ctrl+C to stop." -ForegroundColor Cyan
Write-Host "Keep this window open while your team uses the app." -ForegroundColor Cyan

# Wait for the process to exit
Wait-Process -Id $process.Id
