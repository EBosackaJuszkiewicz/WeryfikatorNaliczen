
import pyodbc
import json
import os
from PyQt5.QtWidgets import QMessageBox

CONFIG_FOLDER = "konfiguracje"
CONFIG_FILE_NAME = os.path.join(CONFIG_FOLDER, "db_config.json")

ALL_EXPECTED_HEADERS = [
    "do_podstawa_zus", "do_podstawa_podatek", "do_podstawa_zdrowotna",
    "do_potracenie", "do_zasilek", "do_nie_podlega_zajęciu_przez_komornika",
    "do_koszty_autorskie"
]

HEADER_MAPPING = {
    "do_podstawa_zus": "ZUS",
    "do_podstawa_podatek": "Podatek",
    "do_podstawa_zdrowotna": "Zdrowotna",
    "do_potracenie": "Potrącenie",
    "do_zasilek": "Zasiłek",
    "do_nie_podlega_zajęciu_przez_komornika": "Nie podlega zajęciu\n (komornik)",
    "do_koszty_autorskie": "Koszty Autorskie"
}
REVERSE_HEADER_MAPPING = {v: k for k, v in HEADER_MAPPING.items()}

def load_db_config():
    """Wczytuje parametry połączenia z pliku JSON."""
    db_config = {
        "migration_server": "",
        "migration_db": "",
        "odbc_driver": "ODBC Driver 17 for SQL Server"
    }
    if os.path.exists(CONFIG_FILE_NAME):
        try:
            with open(CONFIG_FILE_NAME, 'r') as f:
                db_config.update(json.load(f))
        except json.JSONDecodeError:
            QMessageBox.critical(None, "Błąd Konfiguracji",
                                 f"Błąd odczytu pliku {CONFIG_FILE_NAME}.")
    else:
        print(f"Brak pliku konfiguracji: {CONFIG_FILE_NAME}")
    return db_config


def get_db_connection(db_config):
    """Tworzy i zwraca połączenie pyodbc do SQL Server."""
    server = db_config.get("migration_server")
    database = db_config.get("migration_db")
    driver = db_config.get("odbc_driver")

    if not server or not database:
        QMessageBox.critical(None, "Błąd Połączenia",
                             "Brak konfiguracji serwera/bazy danych.")
        return None

    connection_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
        f"Pooling=no;"
    )
    try:
        return pyodbc.connect(connection_str, autocommit=False)
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        QMessageBox.critical(None, "Błąd Połączenia SQL",
                             f"Nie można nawiązać połączenia. SQL State: {sqlstate}")
        return None