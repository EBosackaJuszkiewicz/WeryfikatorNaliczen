import os
import json
from collections import OrderedDict

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QInputDialog, QMessageBox, QDialog, QLineEdit,
    QHBoxLayout, QVBoxLayout, QLabel
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QTimer




class JSONTableWidget(QTableWidget):
    def __init__(self, json_file, styles=None, parent=None):
        super().__init__(parent)
        self.json_file = json_file
        self.data_before_conversion = OrderedDict()
        self.variant_names = []

        # Domyślne style
        default_styles = {
            "table_bg": "#FDFDFD",
            "alternate_bg": "#F3F7FA",
            "gridline": "#D0D8E0",
            "header_bg": "#2C3E50",
            "header_color": "#ECF0F1",
            "row_highlight": "#D6EAF8",
            "row_highlight_color": "#1B2631",
            "button_bg": "#3498DB",
            "button_hover": "#5DADE2",
            "button_border": "#2980B9",
            "button_text": "#FFFFFF"
        }
        if styles:
            default_styles.update(styles)
        self.styles = default_styles

        # Styl tabeli
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.styles['table_bg']};
                gridline-color: {self.styles['gridline']};
                selection-background-color: none;
                selection-color: none;
            }}
            QHeaderView::section {{
                background-color: {self.styles['header_bg']};
                color: {self.styles['header_color']};
            }}
        """)

        # Zachowanie zaznaczenia
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.verticalHeader().setVisible(True)
        self.horizontalHeader().setHighlightSections(False)
        self.selectionModel().selectionChanged.connect(self.update_row_colors)

        # Wczytanie danych z JSON
        self.load_json()
        self.horizontalHeader().sectionClicked.connect(self.select_column)
        self.cellChanged.connect(self.cell_modified)

    # ----------------- JSON -----------------
    def load_json(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as f:
                self.data_before_conversion = json.load(f, object_pairs_hook=OrderedDict)
        else:
            self.data_before_conversion = OrderedDict()

        if not self.data_before_conversion:
            return

        # Kolumny = klucze pierwszego wariantu
        first_variant = next(iter(self.data_before_conversion.values()))
        headers = list(first_variant.keys())

        # Wiersze = nazwy wariantów
        self.variant_names = list(self.data_before_conversion.keys())
        self.setColumnCount(len(headers))
        self.setRowCount(len(self.variant_names))
        self.setHorizontalHeaderLabels(headers)
        self.setVerticalHeaderLabels(self.variant_names)

        # Wypełnienie tabeli
        for r, variant in enumerate(self.variant_names):
            for c, key in enumerate(headers):
                value = self.data_before_conversion[variant].get(key, "")
                self.setItem(r, c, QTableWidgetItem(str(value)))

        self.update_row_colors()
        self.auto_resize_columns()

    def save_json(self):
        # Zapis do pliku w tym samym formacie wierszowym
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.data_before_conversion, f, ensure_ascii=False, indent=2)

    # ----------------- Edycja tabeli -----------------
    def cell_modified(self, row, col):
        header = self.horizontalHeaderItem(col).text()
        variant = self.variant_names[row]
        value = self.item(row, col).text()

        # Spróbuj zamienić na liczbę, jeśli się da
        try:
            if "." in value or value.isdigit():
                value = float(value)
        except:
            pass

        self.data_before_conversion[variant][header] = value
        self.save_json()

    def add_row_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Dodaj nową konfigurację")
        dialog.setFixedSize(650, 150)
        main_layout = QVBoxLayout(dialog)

        label = QLabel("Podaj unikalną nazwę konfiguracji:")
        input_field = QLineEdit()
        input_field.setPlaceholderText("Nazwa konfiguracji (np. 'UOP 2026')")
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
            new_variant_name = input_field.text().strip()

            if not new_variant_name:
                QMessageBox.warning(self, "Błąd", "Nazwa nie może być pusta.")
                return

            if new_variant_name in self.variant_names:
                QMessageBox.warning(self, "Błąd", f"Konfiguracja o nazwie '{new_variant_name}' już istnieje.")
                return

            self.add_row(new_variant_name)

    def add_row(self, new_variant_name):
        """Dodaje nowy wiersz do wewnętrznego modelu danych i do tabeli."""

        # 1. Dodanie wariantu do wewnętrznego modelu danych
        # Nowy wariant musi zawierać klucze kolumn (nagłówki) z pustymi wartościami.
        new_variant_data = OrderedDict()

        # Pobranie nagłówków kolumn z istniejącej tabeli
        headers = [self.horizontalHeaderItem(c).text() for c in range(self.columnCount())]

        for header in headers:
            new_variant_data[header] = ""  # Ustawienie pustej wartości

        self.data_before_conversion[new_variant_name] = new_variant_data
        self.variant_names.append(new_variant_name)

        # 2. Aktualizacja widżetu QTableWidget
        row_count = self.rowCount()
        self.insertRow(row_count)

        # Ustawienie nagłówka pionowego (nazwa wariantu)
        self.setVerticalHeaderLabels(self.variant_names)

        # Wypełnienie komórek w nowym wierszu
        for c, key in enumerate(headers):
            # Wstawienie pustego QTableWidgetItem
            self.setItem(row_count, c, QTableWidgetItem(str(new_variant_data.get(key, ""))))

        # 3. Zapis i aktualizacja widoku
        self.save_json()
        self.update_row_colors()

        # Opcjonalnie: Przewinięcie i zaznaczenie nowego wiersza
        self.selectRow(row_count)
        self.scrollToBottom()

    def remove_configuration(self):
        """Usuwa aktualnie zaznaczony wiersz (wariant) z tabeli i z danych JSON."""
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Błąd Usuwania",
                                "Proszę zaznaczyć cały wiersz, który ma zostać usunięty.")
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
        self.removeRow(row_index)
        if variant_name in self.data_before_conversion:
            del self.data_before_conversion[variant_name]
        if self.variant_names and row_index < len(self.variant_names):
            del self.variant_names[row_index]
        self.setVerticalHeaderLabels(self.variant_names)
        self.save_json()
        self.update_row_colors()

        QMessageBox.information(self, "Sukces", f"Wariant '{variant_name}' został usunięty.")

    # ----------------- Kolory -----------------
    def update_row_colors(self):
        selected_rows = [index.row() for index in self.selectionModel().selectedRows()]
        for r in range(self.rowCount()):
            bg_color = self.styles['table_bg'] if r % 2 == 0 else self.styles['alternate_bg']
            text_color = "#000000"
            if r in selected_rows:
                bg_color = self.styles['row_highlight']
                text_color = self.styles['row_highlight_color']
            for c in range(self.columnCount()):
                item = self.item(r, c)
                if not item:
                    item = QTableWidgetItem("")
                    self.setItem(r, c, item)
                item.setBackground(QColor(bg_color))
                item.setForeground(QColor(text_color))

    # ----------------- Resizing -----------------
    def auto_resize_columns(self):
        header = self.horizontalHeader()
        min_widths = []
        for i in range(self.columnCount()):
            item = self.horizontalHeaderItem(i)
            if item:
                w = self.fontMetrics().boundingRect(item.text()).width() + 40
            else:
                w = 60
            min_widths.append(w)

        total_min = sum(min_widths)
        scrollbar_w = self.verticalScrollBar().width() if self.verticalScrollBar().isVisible() else 0
        frame_w = self.frameWidth() * 2
        available = self.width() - scrollbar_w - frame_w

        if total_min <= available:
            extra = available - total_min
            per_col_extra = extra / self.columnCount()
            for i in range(self.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                header.resizeSection(i, int(min_widths[i] + per_col_extra))
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            for i in range(self.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                header.resizeSection(i, min_widths[i])
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def select_column(self, index):
        self.clearSelection()
        self.setSelectionBehavior(QTableWidget.SelectColumns)
        self.selectColumn(index)
        self.setSelectionBehavior(QTableWidget.SelectRows)

    # ----------------- Przyciski -----------------
    def create_styled_button(self, text, width=120, height=40):
        btn = QPushButton(text)
        btn.setFixedSize(width, height)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.styles['button_bg']};
                border: 1px solid {self.styles['button_border']};
                color: {self.styles['button_text']};
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.styles['button_hover']};
            }}
        """)
        btn.setAutoFillBackground(True)
        btn.setFlat(False)
        btn.setAttribute(Qt.WA_StyledBackground, True)
        return btn

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.auto_resize_columns()
