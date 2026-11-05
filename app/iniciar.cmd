@echo off
pushd "%~dp0"
python app.py --port 8765
popd
pause
