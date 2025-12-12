import pyodbc
import json
import os
from collections import OrderedDict
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QWidget,
    QComboBox, QMessageBox, QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QWheelEvent, QColor, QPainter, QPainterPath

from NoScrollComboBox import NoScrollComboBox

CONFIG_FOLDER = "konfiguracje"
CONFIG_FILE_NAME = os.path.join(CONFIG_FOLDER, "db_config.json")
SQL_DATA_KEY = 'DefinicjeSkladnikow'

ALL_EXPECTED_HEADERS = [
    "do_podstawa_zus",
    "do_podstawa_podatek",
    "do_podstawa_zdrowotna",
    "do_potracenie",
    "do_zasilek",
    "do_nie_podlega_zajęciu_przez_komornika",
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

class DBTableWidget(QTableWidget):
    def __init__(self, styles, parent=None):
        super().__init__(parent)
        self.styles = styles
        self.reverse_header_mapping = {v: k for k, v in HEADER_MAPPING.items()}
        self.data_before_conversion = OrderedDict()
        self.variant_names = []
        self.setSelectionBehavior(QTableWidget.SelectRows)
        header_bg = self.styles['header_bg']
        header_color = self.styles['header_color']
        table_bg = self.styles.get('table_bg', '#FFFFFF')
        alternate_bg = self.styles.get('alternate_bg', '#F7F7F7')
        highlight_bg = self.styles.get('row_highlight', '#D7E1F2')
        highlight_color = self.styles.get('row_highlight_color', '#000000')
        self.setAlternatingRowColors(True)
        self.setObjectName("MyDataTable")

        self.setStyleSheet(f"""
                                #MyDataTable {{
                                    background-color: {table_bg};
                                    border: none;
                                    alternate-background-color: {alternate_bg}; 
                                    gridline-color: #EAEAEA; 
                                    selection-background-color: {highlight_bg};
                                    selection-color: {highlight_color};
                                }}
                                #MyDataTable::item {{
                                    border: none;
                                }}
                    
                                QHeaderView::section:horizontal {{
                                    background-color: {header_bg};
                                    color: {header_color};
                                    border: none;
                                    border-bottom: 1px solid #D1D5DB; 
                                    padding: 6px;
                                    font-weight: bold;
                                    text-align: left; 
                                }}
                                QHeaderView::section:vertical {{
                                    background-color: {header_bg};
                                    color: {header_color};
                                    border: none;
                                    padding: 6px;
                                    font-weight: bold;
                                    text-align: left; 
                                    border-right: 1px solid #D1D5DB; 
                                }}
                                QComboBox {{
                                    border-radius: 4px;
                                    text-align: center;
                                }}

                                QScrollBar::corner {{
                                    background-color: transparent; /* Kluczowe: Przezroczyste tło narożnika */
                                    border: none;
                                }}
                        
                        /* A. Stylizacja Paska Pionowego (QScrollBar:vertical) */
                        QScrollBar:vertical {{
                            border: none;
                            background-color: transparent; /* Tło paska jest przezroczyste */
                            width: 10px; /* Użyteczna, widoczna szerokość */
                        }}

                        /* B. Stylizacja Uchwytu (QScrollBar::handle) */
                        QScrollBar::handle:vertical {{
                            background-color: "#A0AEC0"; /* Kolor uchwytu */
                            min-height: 20px;
                            border-radius: 5px; /* Zaokrąglone końce uchwytu */
                            margin: 2px 0 2px 0; /* Marginalizuje uchwyt od krawędzi, aby zmieścił się w 10px */
                        }}
                        
                        /* C. Stylizacja strzałek (można je ukryć lub zostawić domyślne) */
                        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                            border: none;
                            background: none;
                        }}
                        """)
        self.load_db_config()
        self.load_data()

        self.stretch_columns = True
        self.auto_resize_columns()

        if self.selectionModel():
            self.selectionModel().selectionChanged.connect(self.update_row_colors)

    def _handle_vertical_header_click(self, row_index):
        """
        Wymusza zaznaczenie całego wiersza i odświeżenie kolorów po kliknięciu
        w nagłówek pionowy (nazwę wariantu).
        """
        self.selectRow(row_index)
        self.update_row_colors()

    def load_db_config(self):
        """Wczytuje parametry połączenia z pliku JSON."""
        self.db_config = {
            "migration_server": "",
            "migration_db": "",
            "odbc_driver": "ODBC Driver 17 for SQL Server"
        }

        if os.path.exists(CONFIG_FILE_NAME):
            try:
                with open(CONFIG_FILE_NAME, 'r') as f:
                    config = json.load(f)
                    self.db_config.update(config)
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Błąd Konfiguracji",
                                     f"Błąd odczytu pliku {CONFIG_FILE_NAME}. Sprawdź składnię JSON.")
        else:
            print(f"Brak pliku konfiguracji bazy danych: {CONFIG_FILE_NAME}. Działanie na pustej konfiguracji.")

    def get_db_connection(self):
        """Tworzy i zwraca połączenie pyodbc do SQL Server."""
        server = self.db_config.get("migration_server")
        database = self.db_config.get("migration_db")
        driver = self.db_config.get("odbc_driver")
        if not server or not database:
            QMessageBox.critical(self, "Błąd Połączenia",
                                 "Brak konfiguracji serwera/bazy danych w pliku JSON.")
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
            QMessageBox.critical(self, "Błąd Połączenia SQL",
                                 f"Nie można nawiązać połączenia z serwerem. SQL State: {sqlstate}")
            return None

    # -----------------------------------------------------
    # II. KOMUNIKACJA Z BAZĄ DANYCH
    # -----------------------------------------------------

    def load_data(self):
        """
        Ładuje dane z wer_t_Skladniki_Parametry, uzupełnia brakujące kolumny
        i buduje model słownikowy.
        """
        conn = self.get_db_connection()
        if not conn:
            self.data_before_conversion = OrderedDict()
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT KodSL, Parametr, Wartosc 
                FROM wer_t_Skladniki_Parametry 
                WHERE Data_Od IS NULL AND Data_Do IS NULL 
                ORDER BY KodSL, Parametr
            """)
            rows = cursor.fetchall()
            conn.close()
        except pyodbc.Error as ex:
            QMessageBox.critical(self, "Błąd SQL", f"Błąd odczytu danych: {ex}")
            conn.close()
            return

        new_data = OrderedDict()

        for KodSL, Parametr, Wartosc in rows:
            if KodSL not in new_data:
                new_data[KodSL] = OrderedDict()
            new_data[KodSL][Parametr] = str(Wartosc)

        headers_to_use = ALL_EXPECTED_HEADERS
        display_headers = [HEADER_MAPPING.get(h, h) for h in headers_to_use]
        # --------------------------------------------------------------------

        if not new_data:
            self.setColumnCount(len(headers_to_use))
            self.setHorizontalHeaderLabels(display_headers)
            self.setRowCount(0)
            return

        for KodSL, params in new_data.items():
            for expected_header in headers_to_use:
                if expected_header not in params:
                    params[expected_header] = ""

        self.data_before_conversion = new_data
        self.variant_names = list(self.data_before_conversion.keys())

        self.setColumnCount(len(headers_to_use))
        self.setHorizontalHeaderLabels(display_headers)
        self.setRowCount(len(self.variant_names))
        self.setVerticalHeaderLabels(self.variant_names)

        self._fill_table_widgets(headers_to_use)
        self.auto_resize_columns()
        self.update_row_colors()

    def _fill_table_widgets(self, headers):
        """Pomocnicza funkcja do wypełniania komórek, używana przez load_data i add_row."""
        for r, variant in enumerate(self.variant_names):
            for c, key in enumerate(headers):
                value = self.data_before_conversion[variant].get(key, "")

                if key in ALL_EXPECTED_HEADERS:
                    combo_box = NoScrollComboBox(self)
                    combo_box.addItems(["tak", "nie", ""])
                    combo_box.setCurrentText(str(value))

                    self.style_combo_box_by_text(combo_box, str(value))

                    self.setCellWidget(r, c, combo_box)

                    combo_box.currentTextChanged.connect(
                        lambda text, row=r, col=c: self.combo_box_modified(row, col, text)
                    )

                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.setItem(r, c, item)
                else:
                    self.setItem(r, c, QTableWidgetItem(str(value)))

    def save_data(self):
        """
        Zapisuje model danych do SQL Server. Usuwa stare parametry logiczne i wstawia nowe,
        ALE FILTRUJE DANE, ZAPISUJĄC TYLKO TE Z WARTOSCIĄ 'tak' lub 'nie'.
        """
        conn = self.get_db_connection()
        if not conn:
            return

        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM wer_t_Skladniki_Parametry 
                WHERE Data_Od IS NULL AND Data_Do IS NULL
            """)

            insert_query = """
                INSERT INTO wer_t_Skladniki_Parametry (KodSL, Parametr, Wartosc, Data_Od, Data_Do)
                VALUES (?, ?, ?, NULL, NULL)
            """
            batch_data = []

            for KodSL, params in self.data_before_conversion.items():
                for Parametr, Wartosc in params.items():

                    normalized_value = str(Wartosc).strip().lower()

                    if normalized_value == 'tak' or normalized_value == 'nie':
                        batch_data.append((KodSL, Parametr, normalized_value))

            if batch_data:
                cursor.executemany(insert_query, batch_data)

            conn.commit()

        except pyodbc.Error as ex:
            conn.rollback()
            QMessageBox.critical(self, "Błąd Zapisu", f"Błąd podczas zapisu do bazy danych: {ex}")
        finally:
            conn.close()


    def auto_resize_columns(self):
        """Wymusza rozciągnięcie wszystkich kolumn do pełnej szerokości tabeli, zapewniając równe proporcje."""
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def style_combo_box_by_text(self, combo_box, text, row_bg="#FAFBFC"):
        COLOR_TAK_BG = "#EAF7E8"  # Bardzo jasna, delikatna zieleń
        COLOR_TAK_TEXT = "#1C743C"  # Ciemna, czytelna zieleń
        COLOR_NIE_BG = "#FDF0F0"  # Bardzo jasna, delikatna czerwień/róż
        COLOR_NIE_TEXT = "#B85C5C"
        COLOR_DEFAULT_TEXT = "#000000"

        highlight_bg = self.styles.get('row_highlight', '#D7E3F3').upper()

        is_row_selected = (row_bg.upper() == highlight_bg)

        if text.lower() == "tak":
            bg = COLOR_TAK_BG if not is_row_selected else highlight_bg
            fg = COLOR_TAK_TEXT
        elif text.lower() == "nie":
            bg = COLOR_NIE_BG if not is_row_selected else highlight_bg
            fg = COLOR_NIE_TEXT
        else:
            bg = row_bg
            fg = COLOR_DEFAULT_TEXT

        combo_box.setStyleSheet(f"""
            QComboBox {{
                background-color: {bg};
                color: {fg};
                border: none;
                padding: 6px 4px;
                text-align: center;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 1px; /* Ukrywa strzałkę, jeśli jest zbędna */
                text-align: center;
            }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                selection-background-color: {highlight_bg};
                selection-color: #000000;
                text-align: center;
            }}
        """)

    def combo_box_modified(self, row, col, text):
        """
        Obsługuje zmianę wartości, aktualizuje styl, zapisuje do modelu
        używając klucza bazodanowego (a nie nazwy wyświetlanej).
        """

        combo_box = self.cellWidget(row, col)

        # 1. Uaktualnij styl wizualny
        self.style_combo_box_by_text(combo_box, text)

        # 2. Zapisz dane do modelu
        display_header = self.horizontalHeaderItem(col).text()

        # --- KLUCZOWA ZMIANA: KONWERSJA NA KLUCZ BAZODANOWY ---
        header_key = self.reverse_header_mapping.get(display_header, display_header)
        # ------------------------------------------------------

        variant = self.variant_names[row]
        self.data_before_conversion[variant][header_key] = text

        # 3. Zapisz do QTableWidgetItem pod spodem
        self.item(row, col).setText(text)

        print(f"Zmieniono wariant: {variant}, parametr (DB): {header_key}, nowa wartość: {text}")
        # 4. Zapisz do bazy danych
        self.save_single_variant(variant)
        self.update_row_colors()

    def save_single_variant(self, variant_name):
        """
        Zapisuje zmiany tylko dla jednego, podanego wariantu (KodSL).
        Wykonuje transakcję: USUŃ wszystkie stare parametry tego wariantu BEZ DAT i WSTAW nowe, przefiltrowane.
        """
        conn = self.get_db_connection()
        if not conn:
            return

        cursor = conn.cursor()

        try:
            # 1. Usuń WSZYSTKIE stare parametry DLA TEGO JEDNEGO wariantu (KodSL)
            cursor.execute("""
                DELETE FROM dbo.wer_t_Skladniki_Parametry 
                WHERE KodSL = ? AND Data_Od IS NULL AND Data_Do IS NULL
            """, (variant_name,))
            print(f"DEBUG: DELETE dla {variant_name} wykonane. Usunięto wierszy: {cursor.rowcount}")

            # 2. Przygotowanie danych do wstawienia (FILTROWANIE)
            insert_query = """
                INSERT INTO dbo.wer_t_Skladniki_Parametry (KodSL, Parametr, Wartosc, Data_Od, Data_Do)
                VALUES (?, ?, ?, NULL, NULL)
            """
            batch_data = []

            # Pobieramy dane TYLKO dla zmienionego wariantu
            params = self.data_before_conversion.get(variant_name, {})

            for Parametr, Wartosc in params.items():
                # Filtrowanie: zapisujemy tylko 'tak' lub 'nie'
                normalized_value = str(Wartosc).strip().lower()

                if normalized_value == 'tak' or normalized_value == 'nie':
                    batch_data.append((variant_name, Parametr, normalized_value))

            # 3. Wstawienie przefiltrowanych danych
            if batch_data:
                cursor.executemany(insert_query, batch_data)
                print(f"DEBUG: INSERT dla {variant_name} wykonane. Wstawiono wierszy: {len(batch_data)}")

            # 4. Zatwierdź transakcję
            conn.commit()
            print(f"Sukces zapisu wariantu {variant_name} do bazy.")

        except pyodbc.Error as ex:
            conn.rollback()
            QMessageBox.critical(self, "Błąd Zapisu", f"Błąd podczas zapisu do bazy danych: {ex}")
        finally:
            conn.close()

    # -----------------------------------------------------
    # IV. OBSŁUGA WIERSZY (DODAJ/USUŃ)
    # -----------------------------------------------------

    def create_styled_button(self, text):
        """Pomocnicza metoda do tworzenia przycisków."""
        btn = QPushButton(text)
        btn.setMinimumWidth(150)
        btn.setFixedHeight(30)
        btn.setStyleSheet(f"""
                   QPushButton {{
                       background-color: {self.styles['button_bg']};
                       border: 1px solid {self.styles['button_border']};
                       color: {self.styles['button_text']};
                       padding: 4px 10px;
                   }}
                   QPushButton:hover {{
                       background-color: {self.styles['button_hover']};
                   }}
               """)
        return btn

    def add_row_dialog(self,
                       title="Dodaj nową konfigurację",
                       label_text="Podaj unikalną nazwę konfiguracji:",
                       placeholder_text="Nazwa konfiguracji (np. 'UOP 2026')"):

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(650, 150)
        main_layout = QVBoxLayout(dialog)

        label = QLabel(label_text)
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder_text)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("Dodaj")
        cancel_button = QPushButton("Anuluj")

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        main_layout.addWidget(label)
        main_layout.addWidget(input_field)
        main_layout.addLayout(button_layout)

        ok_button.clicked.connect(lambda: dialog.accept())
        cancel_button.clicked.connect(lambda: dialog.reject())
        input_field.returnPressed.connect(lambda: dialog.accept())

        if dialog.exec_() == QDialog.Accepted:
            new_variant_name = input_field.text().strip().upper()

            if not new_variant_name:
                QMessageBox.warning(self, "Błąd", "Nazwa nie może być pusta.")
                return

            item_type = title.lower().replace('dodaj nową ', '').replace('dodaj ', '')

            if new_variant_name in self.variant_names:
                QMessageBox.warning(self, "Błąd",
                                    f"{item_type.capitalize()} o nazwie '{new_variant_name}' już istnieje.")
                return

            self.add_row(new_variant_name)

    def add_row(self, new_row_name):
        """Dodaje nowy wiersz do modelu danych i do tabeli."""

        new_row_name = new_row_name.upper()

        # 1. Dodanie wariantu do wewnętrznego modelu danych
        new_variant_data = OrderedDict()
        current_headers = [self.horizontalHeaderItem(c).text() for c in range(self.columnCount())]

        for header in ALL_EXPECTED_HEADERS:  # Używamy kluczy bazodanowych do inicjalizacji modelu
            new_variant_data[header] = ""

        self.data_before_conversion[new_row_name] = new_variant_data
        self.variant_names.append(new_row_name)

        # 2. Aktualizacja widżetu QTableWidget
        row_count = self.rowCount()
        self.insertRow(row_count)

        # Ustawienie nagłówka pionowego
        self.setVerticalHeaderLabels(self.variant_names)

        # 3. Wypełnienie nowej kolumny
        self._fill_table_widgets(ALL_EXPECTED_HEADERS)  # Używamy kluczy bazodanowych do wypełnienia widżetów

        # 4. Zapis do bazy (nowy wariant, który na początku ma tylko puste wartości)
        self.save_single_variant(new_row_name)
        self.update_row_colors()
        self.selectRow(row_count)
        self.scrollToBottom()

    def remove_configuration(self):
        """Usuwa aktualnie zaznaczony wiersz (wariant) z tabeli, danych i bazy."""
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Błąd Usuwania", "Proszę zaznaczyć cały wiersz.")
            return

        row_index = selected_rows[0].row()
        variant_to_remove = self.variant_names[row_index]

        reply = QMessageBox.question(self, 'Potwierdzenie Usunięcia',
                                     f"Czy na pewno chcesz usunąć wariant '{variant_to_remove}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.remove_row(row_index, variant_to_remove)

    def remove_row(self, row_index, variant_name):
        """Wykonuje faktyczne usunięcie wariantu z modelu i widoku."""

        # Usuwamy wiersz z widoku tabeli
        self.removeRow(row_index)

        # Usuwamy dane z wewnętrznego modelu
        if variant_name in self.data_before_conversion:
            del self.data_before_conversion[variant_name]

        if self.variant_names and row_index < len(self.variant_names):
            del self.variant_names[row_index]

        self.setVerticalHeaderLabels(self.variant_names)

        # Usuwamy wariant z bazy
        self._delete_variant_from_db(variant_name)
        self.update_row_colors()

        QMessageBox.information(self, "Sukces", f"Wariant '{variant_name}' został usunięty.")

    def _delete_variant_from_db(self, variant_name):
        """Usuwa wszystkie wpisy danego wariantu z bazy danych."""
        conn = self.get_db_connection()
        if not conn: return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM dbo.wer_t_Skladniki_Parametry 
                WHERE KodSL = ? AND Data_Od IS NULL AND Data_Do IS NULL
            """, (variant_name,))
            conn.commit()
        except pyodbc.Error as ex:
            conn.rollback()
            QMessageBox.critical(self, "Błąd Usuwania", f"Błąd podczas usuwania wariantu: {ex}")
        finally:
            conn.close()

    def update_row_colors(self):
        """
        Aktualizuje kolory tła wierszy, w tym podświetlenie.
        Przekazuje poprawny kolor tła (zaznaczone lub naprzemienne) do widżetów.
        """

        selected_rows = [index.row() for index in self.selectionModel().selectedRows()]

        # Użycie czystej, minimalistycznej palety
        default_bg = self.styles.get('table_bg', '#FFFFFF')
        alternate_bg = self.styles.get('alternate_bg', '#FFFFFF')
        highlight_bg = self.styles.get('row_highlight', "#D7E1F2")
        highlight_color = self.styles.get('row_highlight_color', '#000000')

        for r in range(self.rowCount()):
            # 1. Określenie koloru bazowego wiersza
            if r in selected_rows:
                # Kolor zaznaczonego wiersza (błękit)
                bg_color_hex = highlight_bg
                text_color_hex = highlight_color
            else:
                # Kolory naprzemienne (paski)
                bg_color_hex = default_bg if r % 2 == 0 else alternate_bg
                text_color_hex = "#000000"

            bg_color_qt = QColor(bg_color_hex)
            text_color_qt = QColor(text_color_hex)

            for c in range(self.columnCount()):
                item = self.item(r, c)
                if not item:
                    item = QTableWidgetItem("")
                    self.setItem(r, c, item)

                # 2. Ustawienie kolorów dla QTableWidgetItem (pod widżetem)
                item.setBackground(bg_color_qt)
                item.setForeground(text_color_qt)

                # 3. Zastosowanie koloru bazowego do WIDŻETU komórki
                widget = self.cellWidget(r, c)
                if widget and isinstance(widget, QComboBox):
                    # Przekazujemy kolor tła wiersza/podświetlenia do funkcji stylującej
                    self.style_combo_box_by_text(widget, widget.currentText(), bg_color_hex)

