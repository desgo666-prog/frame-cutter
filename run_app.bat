@echo off
setlocal

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate
pip install -r requirements.txt
python frame_cutter_gui.py
