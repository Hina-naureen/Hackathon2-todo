@echo off
cd /d C:\Users\pc\Desktop\Hackathon2-todo\backend
.venv\Scripts\python.exe -m pytest tests\test_agent.py tests\test_chat.py -v --tb=short
echo EXIT_CODE=%ERRORLEVEL%
