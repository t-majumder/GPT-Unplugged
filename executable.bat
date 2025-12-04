@echo off
cd /d %~dp0
cmd /k "streamlit run main.py --server.fileWatcherType none"