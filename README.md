# GAMESEED Participant Checker

Desktop app untuk memverifikasi peserta GAMESEED 2026 berdasarkan data submission CSV.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python gameseed_checker.py
```

Atau untuk development mode (Flask server):

```bash
python backend.py
```

## Build Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "assets:assets" --name "GAMESEED Checker" gameseed_checker.py
```

## Features

- Load CSV Mobile dan PC secara terpisah
- Fuzzy name matching dengan typo tolerance (rapidfuzz)
- Fuzzy matches ditandai dengan background kuning
- Team name otomatis dari CSV
- Persistensi path CSV antar session
- Copy hasil verifikasi ke clipboard
