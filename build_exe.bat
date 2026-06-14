@echo off
setlocal

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

pyinstaller --noconfirm --windowed --onefile --name FrameCutter frame_cutter_gui.py

echo.
echo Build finished. EXE is in dist\FrameCutter.exe
pause
