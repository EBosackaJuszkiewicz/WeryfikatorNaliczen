import os
import json
from collections import OrderedDict

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QInputDialog, QMessageBox, QDialog, QLineEdit,
    QHBoxLayout, QVBoxLayout, QLabel, QComboBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QTimer

from NoScrollComboBox import NoScrollComboBox


class JSONTableWidget(QTableWidget):
    def __init__(self, json_file, boolean_headers = None, stretch_columns=True, styles=None, parent=None):
        super().__init__(parent)
        self.json_file = json_file
        self.data_before_conversion = OrderedDict()
        self.variant_names = []
        self.boolean_headers = boolean_headers if boolean_headers is not None else []
        self.stretch_columns = stretch_columns

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

        # W klasie JSONTableWidget
        # ----------------- Obsługa ComboBox -----------------

    def combo_box_modified(self, row, col, text):
        """Obsługuje zmianę wartości w QComboBox i aktualizuje styl."""
        combo_box = self.cellWidget(row, col)
        self.style_combo_box_by_text(combo_box, text)
        header = self.horizontalHeaderItem(col).text()
        variant = self.variant_names[row]
        self.data_before_conversion[variant][header] = text
        self.item(row, col).setText(text)

        self.save_json()
        self.update_row_colors()

    def style_combo_box_by_text(self, combo_box, text):
        """Ustawia tło QComboBox na podstawie wybranego tekstu ('tak', 'nie', 'puste')."""
        style = "QComboBox { "

        if text.lower() == "tak":
            # Zielone tło, biały tekst
            style += "background-color: #D0F0C0; color: #154360; }"
        elif text.lower() == "nie":
            # Czerwone tło, biały tekst
            style += "background-color: #FFD6D6; color: #641E16; }"
        else:
            # Neutralne tło, czarny tekst
            style += "background-color: #FFFFFF; color: #000000; }"
        combo_box.setStyleSheet(style)
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
                if key in self.boolean_headers:
                    combo_box = NoScrollComboBox(self)
                    combo_box.addItems(["tak", "nie", ""])
                    self.style_combo_box_by_text(combo_box, str(value))

                    if value.lower() in ["tak", "nie"]:
                        combo_box.setCurrentText(value)
                    else:
                        combo_box.setCurrentIndex(combo_box.findText(""))
                    self.setCellWidget(r, c, combo_box)
                    combo_box.currentTextChanged.connect(
                        lambda text, row=r, col=c: self.combo_box_modified(row, col, text)
                    )
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.setItem(r, c, item)
                else:
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

    def add_row_dialog(self,
                       title="Dodaj nową konfigurację",
                       label_text="Podaj unikalną nazwę konfiguracji:",
                       placeholder_text="Nazwa konfiguracji (np. 'UOP 2026')"):

        dialog = QDialog(self)
        dialog.setWindowTitle(title)  # Użycie parametru
        dialog.setFixedSize(650, 150)
        main_layout = QVBoxLayout(dialog)

        label = QLabel(label_text)  # Użycie parametru
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder_text)  # Użycie parametru

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
            item_type = title.lower().replace('dodaj nową ', '').replace('dodaj ', '')

            if new_variant_name in self.variant_names:
                QMessageBox.warning(self, "Błąd",
                                    f"{item_type.capitalize()} o nazwie '{new_variant_name}' już istnieje.")
                return
            self.add_row(new_variant_name)

    def add_row(self, new_variant_name):
        """Dodaje nowy wiersz do wewnętrznego modelu danych i do tabeli z obsługą QComboBox."""

        new_variant_data = OrderedDict()
        headers = [self.horizontalHeaderItem(c).text() for c in range(self.columnCount())]

        for header in headers:
            new_variant_data[header] = ""
        new_variant_name = new_variant_name.upper()

        self.data_before_conversion[new_variant_name] = new_variant_data
        self.variant_names.append(new_variant_name)

        row_count = self.rowCount()
        self.insertRow(row_count)
        self.setVerticalHeaderLabels(self.variant_names)

        for c, key in enumerate(headers):

            if key in self.boolean_headers:
                combo_box = NoScrollComboBox(self)
                combo_box.addItems(["tak", "nie", ""])
                combo_box.setCurrentText("")  # Ustawienie pustej wartości
                self.setCellWidget(row_count, c, combo_box)
                self.style_combo_box_by_text(combo_box, "")

                combo_box.currentTextChanged.connect(
                    lambda text, row=row_count, col=c: self.combo_box_modified(row, col, text)
                )

                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.setItem(row_count, c, item)

            else:
                self.setItem(row_count, c, QTableWidgetItem(str(new_variant_data.get(key, ""))))

        self.save_json()
        self.update_row_colors()
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
                                     f"Czy na pewno chcesz usunąć '{variant_to_remove}'?",
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

        if self.stretch_columns:
            for i in range(self.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Stretch)
                self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        else:
            for i in range(self.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.Interactive)
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
                # Jeśli wszystko się mieści, rozdziel nadmiar przestrzeni
                extra = available - total_min
                per_col_extra = extra / self.columnCount()
                for i in range(self.columnCount()):
                    header.resizeSection(i, int(min_widths[i] + per_col_extra))
                self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            else:
                # Jeśli jest za mało miejsca, ustaw minimalne szerokości i włącz scrollbar
                for i in range(self.columnCount()):
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

