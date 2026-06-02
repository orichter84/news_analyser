#!/bin/bash
# News Analyser — startet alle drei Services

BASE="$(cd "$(dirname "$0")" && pwd)"
VENV="$BASE/.venv/bin"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

export PATH="$HOME/.local/bin:$PATH"

# .env laden
set -a; [ -f "$BASE/.env" ] && source "$BASE/.env"; set +a

CHROMA_HOST="${CHROMA_HOST:-localhost}"
CHROMA_PORT="${CHROMA_PORT:-8001}"

echo "[1/3] ChromaDB starten (${CHROMA_HOST}:${CHROMA_PORT}) ..."
"$VENV/chroma" run --host "$CHROMA_HOST" --port "$CHROMA_PORT" --path "$BASE/data/chroma_db" &
CHROMA_PID=$!

# Warten bis ChromaDB antwortet
for i in {1..20}; do
    curl -s "http://${CHROMA_HOST}:${CHROMA_PORT}/api/v2/heartbeat" > /dev/null 2>&1 && break
    sleep 1
done
echo "    ChromaDB bereit (PID $CHROMA_PID)"

echo "[2/3] FastAPI Backend starten (Port 8000) ..."
cd "$BASE/backend"
"$VENV/uvicorn" main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 2
echo "    Backend bereit (PID $BACKEND_PID)"

echo "[3/3] Angular Frontend starten (Port 4200) ..."
cd "$BASE/frontend"
npx ng serve --port 4200 &
FRONTEND_PID=$!
sleep 2
echo "    Frontend bereit (PID $FRONTEND_PID)"

echo ""
echo "News Analyser läuft:"
echo "  ChromaDB  → http://${CHROMA_HOST}:${CHROMA_PORT}"
echo "  Backend   → http://localhost:8000"
echo "  Frontend  → http://localhost:4200"
echo ""
echo "Alle Services mit Ctrl+C beenden."

trap "echo ''; echo 'Beende...'; kill $CHROMA_PID $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
