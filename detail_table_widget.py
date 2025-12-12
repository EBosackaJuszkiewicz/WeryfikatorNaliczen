# detail_table_widget.py (Wersja z poprawnym filtrowaniem)

import pyodbc
from collections import OrderedDict
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QWheelEvent
from db_utils import load_db_config, get_db_connection, ALL_EXPECTED_HEADERS, HEADER_MAPPING, REVERSE_HEADER_MAPPING


class NoScrollComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def wheelEvent(self, event: QWheelEvent):
        event.ignore()


class DetailTableWidget(QTableWidget):
    """
    Tabela Detail: Wyświetla parametry dla JEDNEGO KodSL jako lista (wiersze),
    z filtrowaniem (tylko 'tak' lub puste są widoczne).
    """

    def __init__(self, styles, parent=None):
        super().__init__(parent)
        self.styles = styles
        self.db_config = load_db_config()
        self.reverse_header_mapping = REVERSE_HEADER_MAPPING
        self.data_before_conversion = OrderedDict()
        self.current_kod_sl = None

        self.setSelectionBehavior(QTableWidget.SelectItems)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setAlternatingRowColors(True)
        self.setObjectName("MyDataTable")

        # --- Stylizacja (Skrócona) ---
        header_bg = self.styles['header_bg']
        header_color = self.styles['header_color']
        table_bg = self.styles.get('table_bg', '#FFFFFF')

        self.setStyleSheet(f"""
                                #MyDataTable {{ background-color: {table_bg}; border: none; }}
                                QHeaderView::section:horizontal {{ background-color: {header_bg}; color: {header_color}; border: none; padding: 6px; font-weight: bold; }}
                                QHeaderView::section:vertical {{ background-color: {header_bg}; color: {header_color}; border: none; padding: 6px; font-weight: bold; }}
                                QScrollBar:vertical {{ width: 10px; }}
                                QScrollBar::handle:vertical {{ background-color: "#A0AEC0"; border-radius: 5px; }}
                                """)
        # --- Koniec Stylizacji ---

        self.init_table_structure()

    def get_db_connection(self):
        return get_db_connection(self.db_config)

    def init_table_structure(self):
        """Konfiguruje stałe nagłówki kolumn tabeli (Parametr | Wartość)."""
        # Ustawiamy tylko stałe kolumny i czyścimy wiersze
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Parametr", "Wartość"])
        self.verticalHeader().setVisible(False)
        self.setRowCount(0)  # Kluczowe: zawsze zaczynamy od zera wierszy
        self.auto_resize_columns()

    def clear_table(self):
        """Wyczyść wszystkie wiersze i widżety."""
        self.setRowCount(0)
        self.clearContents()

    def auto_resize_columns(self):
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def load_variant_data(self, kod_sl):
        """SLOT: Ładuje, filtruje i wyświetla dane dla JEDNEGO wariantu (KodSL).

        Parametry są wyświetlane TYLKO, jeśli ich wartość w bazie to 'tak'.
        """
        if kod_sl == self.current_kod_sl:
            return

        self.clear_table()
        self.current_kod_sl = kod_sl

        conn = self.get_db_connection()
        if not conn:
            return

        # POBIERANIE DANYCH Z BAZY
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT Parametr, Wartosc 
                FROM wer_t_Skladniki_Parametry 
                WHERE KodSL = ? AND Data_Od IS NULL AND Data_Do IS NULL 
                ORDER BY Parametr
            """, (kod_sl,))
            rows = cursor.fetchall()
            conn.close()
        except pyodbc.Error as ex:
            QMessageBox.critical(self, "Błąd SQL", f"Błąd odczytu danych dla {kod_sl}: {ex}")
            conn.close()
            return

        new_params = OrderedDict()
        for Parametr, Wartosc in rows:
            new_params[Parametr] = str(Wartosc).lower()

        # --- ZMIENIONA LOGIKA FILTROWANIA PARAMETRÓW ---
        # Usuwamy warunek 'wartosc == ""', aby wyświetlać TYLKO te, które mają 'tak'.

        self.display_headers = []

        for expected_header in ALL_EXPECTED_HEADERS:
            wartosc = new_params.get(expected_header, "").strip()

            # Dodajemy parametr TYLKO, gdy ma ustawioną wartość 'tak'
            if wartosc == 'tak':
                self.display_headers.append(expected_header)

            # Upewnienie się, że wszystkie klucze są w modelu, nawet jeśli są puste
            # (aby zachować informację o parametrach ustawionych na 'nie')
            if expected_header not in new_params:
                new_params[expected_header] = ""

        self.data_before_conversion = {kod_sl: new_params}

        # Wypełnienie widżetu QTableWidget (TYLKO tymi filtrowanymi)
        self._fill_table_widgets(kod_sl, self.display_headers)
        self.update_row_colors()

    def _fill_table_widgets(self, kod_sl, headers):
        """Wypełnia wiersze Parametrami i ComboBoxami Wartości."""

        self.setRowCount(len(headers))  # Teraz wierszy jest TYLE, ile jest pozycji na filtrowanej liście
        variant_data = self.data_before_conversion.get(kod_sl, {})

        for r, key in enumerate(headers):
            # A. KOLUMNA 0: NAZWA PARAMETRU (Tekst statyczny)
            display_name = HEADER_MAPPING.get(key, key)
            item_param = QTableWidgetItem(display_name)
            item_param.setFlags(item_param.flags() & ~Qt.ItemIsEditable)
            self.setItem(r, 0, item_param)

            # B. KOLUMNA 1: WARTOŚĆ (ComboBox)
            value = variant_data.get(key, "")
            combo_box = NoScrollComboBox(self)
            combo_box.addItems(["tak", "nie", ""])
            combo_box.setCurrentText(str(value))

            self.style_combo_box_by_text(combo_box, str(value), row_bg=self._get_row_color(r))
            self.setCellWidget(r, 1, combo_box)

            combo_box.currentTextChanged.connect(
                lambda text, row=r, db_key=key: self.combo_box_modified(row, 1, text, db_key)
            )

            item_value = QTableWidgetItem(str(value))
            item_value.setFlags(item_value.flags() & ~Qt.ItemIsEditable)
            self.setItem(r, 1, item_value)

    def _get_row_color(self, row):
        """Zwraca kolor tła dla wiersza."""
        default_bg = self.styles.get('table_bg', '#FFFFFF')
        alternate_bg = self.styles.get('alternate_bg', '#F7F7F7')
        return default_bg if row % 2 == 0 else alternate_bg

    def style_combo_box_by_text(self, combo_box, text, row_bg="#FAFBFC"):
        COLOR_TAK_BG = "#EAF7E8"
        COLOR_TAK_TEXT = "#1C743C"
        COLOR_NIE_BG = "#FDF0F0"
        COLOR_NIE_TEXT = "#B85C5C"
        COLOR_DEFAULT_TEXT = "#000000"

        if text.lower() == "tak":
            bg = COLOR_TAK_BG
            fg = COLOR_TAK_TEXT
        elif text.lower() == "nie":
            bg = COLOR_NIE_BG
            fg = COLOR_NIE_TEXT
        else:
            bg = self.styles.get('table_bg', '#FAFBFC') if row_bg == "#FAFBFC" else row_bg
            fg = COLOR_DEFAULT_TEXT

        combo_box.setStyleSheet(f"""
            QComboBox {{
                background-color: {bg};
                color: {fg};
                border: none;
                padding: 6px 4px;
                text-align: center;
            }}
            QComboBox::drop-down {{ border: none; width: 1px; }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                selection-background-color: {self.styles.get('row_highlight', '#D7E1F2')};
                selection-color: #000000;
                text-align: center;
            }}
        """)

    def update_row_colors(self):
        for r in range(self.rowCount()):
            bg_color_hex = self._get_row_color(r)
            widget = self.cellWidget(r, 1)
            if widget and isinstance(widget, QComboBox):
                self.style_combo_box_by_text(widget, widget.currentText(), bg_color_hex)

    def combo_box_modified(self, row, col, text, db_key):
        """Obsługa zmiany wartości w ComboBox i aktualizacja modelu/DB."""

        normalized_text = text.strip().lower()

        # 1. Aktualizacja stylu i modelu wewnętrznego
        self.style_combo_box_by_text(self.cellWidget(row, col), normalized_text, self._get_row_color(row))

        variant = self.current_kod_sl
        header_key = db_key

        if variant in self.data_before_conversion:
            self.data_before_conversion[variant][header_key] = normalized_text

        if self.item(row, col):
            self.item(row, col).setText(normalized_text)

        # 2. Zapis do bazy
        self.save_single_variant(variant)

        # 3. UKRYWANIE WIERSZA, JEŚLI WARTOŚĆ ZMIENIONA NA 'nie'
        if normalized_text == 'nie':
            self.load_variant_data(self.current_kod_sl)

    def save_single_variant(self, variant_name):
        """Zapisuje zmiany tylko dla jednego, podanego wariantu (KodSL)."""
        conn = self.get_db_connection()
        if not conn:
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM dbo.wer_t_Skladniki_Parametry 
                WHERE KodSL = ? AND Data_Od IS NULL AND Data_Do IS NULL
            """, (variant_name,))

            insert_query = """
                INSERT INTO dbo.wer_t_Skladniki_Parametry (KodSL, Parametr, Wartosc, Data_Od, Data_Do)
                VALUES (?, ?, ?, NULL, NULL)
            """
            batch_data = []
            params = self.data_before_conversion.get(variant_name, {})

            for Parametr, Wartosc in params.items():
                normalized_value = str(Wartosc).strip().lower()

                if normalized_value == 'tak' or normalized_value == 'nie':
                    batch_data.append((variant_name, Parametr, normalized_value))

            if batch_data:
                cursor.executemany(insert_query, batch_data)

            conn.commit()
            print(f"Sukces zapisu wariantu {variant_name} do bazy.")

        except pyodbc.Error as ex:
            conn.rollback()
            QMessageBox.critical(self, "Błąd Zapisu", f"Błąd podczas zapisu do bazy danych: {ex}")
        finally:
            conn.close()