echo "🚀 Starting ResearchGPT (Backend + Frontend)"

# -----------------------------
# Activate Python venv (bash)
# -----------------------------
source "/gpt/Scripts/activate"   # or ->>>> "Your_env_name\Scripts\activate"

# -----------------------------
# Start Backend
# -----------------------------
echo "⚙️ Starting Backend (FastAPI)"
cd "/backend"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# -----------------------------
# Start Frontend
# -----------------------------
echo "🌐 Starting Frontend"
cd "/frontend"
python -m http.server 5173 &
FRONTEND_PID=$!

# -----------------------------
# Graceful shutdown
# -----------------------------
trap "echo '🛑 Stopping servers'; kill $BACKEND_PID $FRONTEND_PID" SIGINT SIGTERM

echo "✅ Backend:  http://localhost:8000"
echo "✅ Frontend: http://localhost:5173"

wait