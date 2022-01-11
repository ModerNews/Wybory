@echo off
echo This will wipe all uncommited changes, do you want to continue?
pause
call git reset --hard --quiet
call git pull https://github.com/ModerNews/Wybory --quiet
pip list
echo Everything setup, just continue to start the overlay
pause
call venv\Scripts\activate.bat
cd overlay\app
call cmd.exe /c uvicorn main:app --reload --host 127.0.0.1 --port 8080
