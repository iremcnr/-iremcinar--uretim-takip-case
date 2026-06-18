#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> Backend başlatılıyor..."
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt -q
else
  source .venv/bin/activate
fi

if [ ! -f production.db ]; then
  echo "==> Test verisi import ediliyor..."
  python -c "
from database import init_db, SessionLocal
from services.import_service import import_csv
init_db()
with open('$ROOT/data/production_data.csv','rb') as f:
    import_csv(SessionLocal(), f.read(), 'production_data.csv')
"
fi

uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

echo "==> Frontend başlatılıyor..."
cd "$ROOT/frontend"
[ -d node_modules ] || npm install -q
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Uygulama: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo "Durdurmak için: kill $BACKEND_PID $FRONTEND_PID"

wait
