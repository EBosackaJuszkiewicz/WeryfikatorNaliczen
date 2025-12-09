# Aplikacja WeryfikatorNaliczeń

Aplikacja desktopowa weryfikacji naliczeń

## Wymagania
- Python 3.10 lub nowszy
- Zainstalowany sterownik ODBC dla SQL Server:
  - Windows: `ODBC Driver 17 for SQL Server`

## Instalacja Pythona (jeśli nie masz)

1. Wejdź na stronę: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Pobierz najnowszą wersję Python 3.x dla swojego systemu.
3. Uruchom instalator i **zaznacz opcję „Add Python to PATH”**.
4. Po zakończeniu instalacji sprawdź w terminalu:
```bash
python --version

# 1. Utwórz wirtualne środowisko
python -m venv venv

# 2. Aktywuj wirtualne środowisko
    # Windows:
    venv\Scripts\activate
    # Linux/macOS:
    source venv/bin/activate

# 3. Zainstaluj zależności
python -m pip install -r requirements.txt

# 4. Uruchom aplikację 
python script.py