import os
import json
from collections import OrderedDict
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class GroupedJSONTableWidget(QTableWidget):
    def __init__(self, json_file, parent=None, styles=None):
        super().__init__(parent)
        self.json_file = json_file
        self.styles = styles or {}
        self.row_to_group = {}
        self.group_colors = {
            "pracownik": "#D0F0C0",
            "pracodawca": "#FFD6D6",
            "parametry_podatkowe": "#FFF5E1",
            "potrącenia_zasiłki": "#E6E6FA",
            "PPK_i_koszty_pracownicze": "#E6E6FA"
        }

        self.setStyleSheet(f"""
                   QHeaderView::section {{
                       background-color: {self.styles.get('header_bg', '#2C3E50')};
                       color: {self.styles.get('header_color', '#ECF0F1')};
                       padding: 4px;
                       border: 1px solid {self.styles.get('gridline', '#D0D8E0')};
                   }}
               """)

        self.load_grouped_json()
        self.auto_resize_columns()

        self.cellChanged.connect(self.cell_modified)

    def load_grouped_json(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f, object_pairs_hook=OrderedDict)
        else:
            raw_data = {}

        rows = []
        r_index = 0
        for group, params in raw_data.items():
            for param_name, info in params.items():
                rows.append([
                    info.get("data_od", ""),
                    info.get("data_do", ""),
                    param_name,
                    info.get("wartosc", "")
                ])
                self.row_to_group[r_index] = group
                r_index += 1

        # Wypełnienie tabeli
        self.setColumnCount(4)
        self.setRowCount(len(rows))
        self.setHorizontalHeaderLabels(["Data od", "Data do", "Nazwa parametru", "Wartość"])

        for i in range(self.columnCount()):
            item = self.horizontalHeaderItem(i)
            if item:
                item.setBackground(QColor(self.styles.get("header_bg", "#2C3E50")))
                item.setForeground(QColor(self.styles.get("header_color", "#ECF0F1")))

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.setItem(r, c, QTableWidgetItem(str(val)))

        self.update_row_colors()
        self.resizeColumnsToContents()

    def lighter_color(self, color, factor=0.7):
        if not isinstance(color, QColor):
            color = QColor(color)
        r = color.red() + (255 - color.red()) * factor
        g = color.green() + (255 - color.green()) * factor
        b = color.blue() + (255 - color.blue()) * factor
        return QColor(int(r), int(g), int(b))

    def update_row_colors(self):
        for r in range(self.rowCount()):
            group = self.row_to_group.get(r)
            base_color = QColor(self.group_colors.get(group, self.styles.get('table_bg', "#FFFFFF")))
            bg_color = self.lighter_color(base_color, 0.6) if r % 2 == 0 else base_color

            for c in range(self.columnCount()):
                item = self.item(r, c)
                if not item:
                    item = QTableWidgetItem("")
                    self.setItem(r, c, item)
                item.setBackground(bg_color)
                item.setForeground(QColor("#000000"))

    def cell_modified(self, row, col):
        """Zapis zmiany do JSON przy edycji kolumny 'Wartość'"""
        if col != 3:
            return

        param_item = self.item(row, 2)
        if not param_item:
            return
        param_name = param_item.text()
        group = self.row_to_group.get(row)
        if not group:
            return

        if os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f, object_pairs_hook=OrderedDict)
        else:
            data = OrderedDict()

        data.setdefault(group, OrderedDict())
        data[group][param_name] = {
            "data_od": self.item(row, 0).text(),
            "data_do": self.item(row, 1).text(),
            "wartosc": float(self.item(row, 3).text()) if self.item(row, 3).text() else ""
        }

        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.update_row_colors()
    def auto_resize_columns(self):
        header = self.horizontalHeader()
        num_cols = self.columnCount()
        if num_cols == 0:
            return

        # Liczymy minimalną szerokość każdej kolumny na podstawie nagłówka i zawartości
        min_widths = []
        for c in range(num_cols):
            header_item = self.horizontalHeaderItem(c)
            max_width = 60  # minimalna szerokość
            if header_item:
                max_width = self.fontMetrics().boundingRect(header_item.text()).width() + 20
            for r in range(self.rowCount()):
                item = self.item(r, c)
                if item:
                    w = self.fontMetrics().boundingRect(item.text()).width() + 20
                    if w > max_width:
                        max_width = w
            min_widths.append(max_width)

        total_min = sum(min_widths)
        scrollbar_w = self.verticalScrollBar().width() if self.verticalScrollBar().isVisible() else 0
        frame_w = self.frameWidth() * 2
        available = self.width() - scrollbar_w - frame_w

        if total_min < available:
            # rozdzielamy dodatkową przestrzeń proporcjonalnie
            extra = available - total_min
            per_col_extra = extra / num_cols
            for i in range(num_cols):
                header.setSectionResizeMode(i, header.Interactive)
                header.resizeSection(i, int(min_widths[i] + per_col_extra))
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            # kolumny minimalne + scrollbar
            for i in range(num_cols):
                header.setSectionResizeMode(i, header.Interactive)
                header.resizeSection(i, min_widths[i])
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.auto_resize_columns()
