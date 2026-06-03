# News Analyser - startet alle drei Services (Windows)

$BASE = $PSScriptRoot
$VENV = "$BASE\.venv\Scripts"

# .env laden
if (Test-Path "$BASE\.env") {
    Get-Content "$BASE\.env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}

if ($env:CHROMA_HOST) { $CHROMA_HOST = $env:CHROMA_HOST } else { $CHROMA_HOST = "localhost" }
if ($env:CHROMA_PORT) { $CHROMA_PORT = $env:CHROMA_PORT } else { $CHROMA_PORT = "8001" }

# ChromaDB starten
Write-Host "[1/3] ChromaDB starten ($CHROMA_HOST`:$CHROMA_PORT) ..."
$chromaArgs = "run --host $CHROMA_HOST --port $CHROMA_PORT --path $BASE\data\chroma_db"
$chromaProc = Start-Process -FilePath "$VENV\chroma.exe" -ArgumentList $chromaArgs -PassThru -NoNewWindow

# Warten bis ChromaDB antwortet (bis zu 60s)
for ($i = 1; $i -le 60; $i++) {
    if ($i -eq 1) { Write-Host "    (Erster Start laedt Embedding-Modell - bitte warten...)" }
    try {
        Invoke-WebRequest -Uri "http://$CHROMA_HOST`:$CHROMA_PORT/api/v2/heartbeat" -TimeoutSec 1 -ErrorAction Stop | Out-Null
        break
    } catch { Start-Sleep 1 }
}
Write-Host "    ChromaDB bereit (PID $($chromaProc.Id))"

# Backend starten
Write-Host "[2/3] FastAPI Backend starten (Port 8000) ..."
$backendProc = Start-Process -FilePath "$VENV\uvicorn.exe" -ArgumentList "main:app --host 0.0.0.0 --port 8000" -WorkingDirectory "$BASE\backend" -PassThru -NoNewWindow
Start-Sleep 2
Write-Host "    Backend bereit (PID $($backendProc.Id))"

# Frontend starten
Write-Host "[3/3] Angular Frontend starten (Port 4200) ..."
$frontendProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npx ng serve --port 4200" -WorkingDirectory "$BASE\frontend" -PassThru -NoNewWindow
Start-Sleep 2
Write-Host "    Frontend bereit (PID $($frontendProc.Id))"

Write-Host ""
Write-Host "News Analyser laeuft:"
Write-Host "  ChromaDB  -> http://$CHROMA_HOST`:$CHROMA_PORT"
Write-Host "  Backend   -> http://localhost:8000"
Write-Host "  Frontend  -> http://localhost:4200"
Write-Host ""
Write-Host "Alle Services mit Ctrl+C beenden."

try {
    Wait-Process -Id $chromaProc.Id, $backendProc.Id, $frontendProc.Id -ErrorAction SilentlyContinue
} finally {
    Write-Host ""
    Write-Host "Beende..."
    Stop-Process -Id $chromaProc.Id, $backendProc.Id, $frontendProc.Id -Force -ErrorAction SilentlyContinue
}
