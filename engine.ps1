Write-Host "🚀 Starting ResearchGPT (Backend + Frontend)"

# -----------------------------
# Activate virtual environment
# -----------------------------
Write-Host "🐍 Activating Python environment"
& "gpt\Scripts\Activate.ps1"  # or ->>>> "Your_env_name\Scripts\Activate.ps1"

# -----------------------------
# Start Backend
# -----------------------------
Write-Host "⚙️ Starting Backend (FastAPI)"
Start-Process powershell `
    -ArgumentList `
    "cd 'backend'; uvicorn main:app --host 0.0.0.0 --port 8000 --reload" `
    -NoNewWindow

# -----------------------------
# Start Frontend
# -----------------------------
Write-Host "🌐 Starting Frontend (HTTP Server)"
Start-Process powershell `
    -ArgumentList `
    "cd 'frontend'; python -m http.server 5173" `
    -NoNewWindow

# -----------------------------
# Info
# -----------------------------
Write-Host ""
Write-Host "✅ Backend running at  http://localhost:8000"
Write-Host "✅ Frontend running at http://localhost:5173"
Write-Host "🛑 Close the PowerShell window to stop everything"