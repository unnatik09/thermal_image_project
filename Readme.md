# TC001 Thermal Scanner

## Run directly
```bash
pip install -r requirements.txt
python main.py
```

## Build Windows .exe
```bash
pip install pyinstaller
pyinstaller build_exe.spec
# Output: dist/TC001_ThermalScanner.exe
```

## Run on Raspberry Pi
```bash
sudo apt install python3-pyqt5
pip install opencv-python numpy scipy
python main.py
```

## Key bindings
| Key | Action |
|-----|--------|
| R   | Start recording |
| T   | Stop recording  |
| D   | Toggle detection |
| P   | Snapshot |
| Q   | Quit |

## Settings
Click ⚙ SETTINGS to adjust:
- Entropy threshold (Good/Bad boundary)
- Min/Max fruit area (px²)

Settings saved to `tc001_settings.json`.