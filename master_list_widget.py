# master_list_widget.py

import pyodbc
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5.QtCore import pyqtSignal
from db_utils import load_db_config, get_db_connection


class MasterListWidget(QTableWidget):
    """
    Tabela Master: Wyświetla listę KodSL.
    Emituje KodSL po kliknięciu.
    """
    variantSelected = pyqtSignal(str)

    def __init__(self, styles, parent=None):
        super().__init__(parent)
        self.styles = styles
        self.db_config = load_db_config()
        self.variant_names = []

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["Składnik (KodSL)"])
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.styles.get('table_bg', '#FFFFFF')};
                border: 1px solid #D1D5DB;
                selection-background-color: {self.styles.get('row_highlight', '#D7E1F2')};
                selection-color: {self.styles.get('row_highlight_color', '#000000')};
            }}
            QHeaderView::section:horizontal {{
                background-color: {self.styles['header_bg']};
                color: {self.styles['header_color']};
                border: none;
                border-bottom: 1px solid #D1D5DB; 
                padding: 6px;
                font-weight: bold;
            }}
        """)

        self.load_data()
        self.itemSelectionChanged.connect(self._emit_selected_variant)

    def get_db_connection(self):
        return get_db_connection(self.db_config)

    def load_data(self):
        """Ładuje unikalne KodSL z bazy i wypełnia tabelę."""
        conn = self.get_db_connection()
        if not conn:
            self.setRowCount(0)
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT KodSL 
                FROM wer_t_Skladniki_Parametry 
                ORDER BY KodSL
            """)
            rows = cursor.fetchall()
            conn.close()
        except pyodbc.Error as ex:
            QMessageBox.critical(self, "Błąd SQL", f"Błąd odczytu listy składników: {ex}")
            conn.close()
            return

        self.variant_names = [row[0] for row in rows]

        self.setRowCount(len(self.variant_names))
        for r, name in enumerate(self.variant_names):
            item = QTableWidgetItem(name)
            self.setItem(r, 0, item)

        if self.rowCount() > 0:
            self.selectRow(0)

    def _emit_selected_variant(self):
        """Emituje sygnał z nazwą wybranego wariantu."""
        selected_rows = self.selectedItems()
        if selected_rows:
            kod_sl = selected_rows[0].text()
            self.variantSelected.emit(kod_sl)