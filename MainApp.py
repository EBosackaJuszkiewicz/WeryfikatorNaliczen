import os.path
import sys

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QApplication, QTabWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, \
    QHeaderView, QPushButton

from ColoredTabBar import ColoredTabBar
from GroupedJSONTableWidget import GroupedJSONTableWidget
from JSONTableWidget import JSONTableWidget

CONFIG_FOLDER = "konfiguracje"
PARAMETRY_SYSTEMOWE = os.path.join(CONFIG_FOLDER, "parametry_systemowe.json")
KONFIGURACJE_PRAWNE = os.path.join(CONFIG_FOLDER, "konfiguracje_prawne.json")

class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weryfikator naliczeń")
        self.setFixedSize(1800,950)

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.outer_tabs_colors = [
            "#E8E8ED",  # jasny szary
            "#DDE7F0",  # bardzo jasny pastelowy błękit
            "#F2F2F2",  # ultra neutralny szary
            "#E3EAF3",  # delikatny zimny niebiesko-szary
        ] # kolory nagłówków
        outer_bar = ColoredTabBar(self.outer_tabs_colors)
        self.tabs.setTabBar(outer_bar)
        main_layout.addWidget(self.tabs)

        self.setup_parameter_tab()
        self.setup_definicje_skladnikow_tab()
        self.apply_tab_colors(self.tabs, self.outer_tabs_colors)

        self.tabs.currentChanged.connect(lambda idx: self.update_tab_background(self.tabs, self.outer_tabs_colors, idx))

    def apply_tab_colors(self, tab_widget, colors):
        for i in range(tab_widget.count()):
            tab_widget.widget(i).setStyleSheet(f"background-color: {colors[i % len(colors)]};")
            tab_widget.tabBar().setTabTextColor(i, QColor('black'))

    def update_tab_background(self, tab_widget, colors, index):
        tab_widget.widget(index).setStyleSheet(f"background-color: {colors[index % len(colors)]};")

    def setup_parameter_tab(self):
        parameters_tab = QWidget()
        self.tabs.addTab(parameters_tab, "Parametry")

        layout = QVBoxLayout(parameters_tab)

        inner_tabs = QTabWidget()
        self.inner_tabs_colors =  [
            "#F2F2F2",  # jasny szary
            "#F2F2F2",  # bardzo jasny pastelowy błękit
            "#F2F2F2",  # ultra neutralny szary
            "#F2F2F2",  # delikatny zimny niebiesko-szary
        ]
        self.inner_tab_headers_colors = [
            "#008000",  # jasny szary
            "#F2F2F2",  # bardzo jasny pastelowy błękit
            "#F2F2F2",  # ultra neutralny szary
            "#F2F2F2",  # delikatny zimny niebiesko-szary
        ]
        coloredTabBar = ColoredTabBar(self.inner_tabs_colors)
        inner_tabs.setTabBar(coloredTabBar)
        inner_tabs.setTabPosition(QTabWidget.West)

        layout.addWidget(inner_tabs)


        systemowe_tab = QWidget()
        systemowe_tab.setLayout(QVBoxLayout())
        self.setup_systemowe_tab(systemowe_tab)

        konfiguracje_prawne_tab = QWidget()
        konfiguracje_prawne_tab.setLayout(QVBoxLayout())
        self.setup_konfiguracje_prawne_tab(konfiguracje_prawne_tab)

        inner_tabs.addTab(systemowe_tab, "Systemowe")
        inner_tabs.addTab(konfiguracje_prawne_tab, "Konfiguracje prawne")
        self.apply_tab_colors(inner_tabs, self.inner_tabs_colors)

    def setup_systemowe_tab(self, parent_widget):
        if not os.path.exists(CONFIG_FOLDER):
            os.makedirs(CONFIG_FOLDER)

        custom_styles = {
            "table_bg": "#FDFDFD",
            "alternate_bg": "#F3F7FA",
            "gridline": "#D0D8E0",
            "header_bg": "#2C3E50",
            "header_color": "#ECF0F1",
            "button_bg": "#2C3E50",
            "button_hover": "#5c7996",
            "button_border": "#5c7996",
            "button_text": "#FFFFFF",
            "row_highlight": "#D6EAF8",
            "row_highlight_color": "#1B2631",
        }

        table = GroupedJSONTableWidget(PARAMETRY_SYSTEMOWE, styles=custom_styles)

        parent_widget.layout().addWidget(table)
        table.load_grouped_json()

    def setup_konfiguracje_prawne_tab(self, parent_widget):
        os.makedirs(CONFIG_FOLDER, exist_ok=True)
        custom_styles = {
            "table_bg": "#FDFDFD",
            "alternate_bg": "#F3F7FA",
            "gridline": "#D0D8E0",
            "header_bg": "#2C3E50",
            "header_color": "#ECF0F1",
            "button_bg": "#2C3E50",
            "button_hover": "#5c7996",
            "button_border": "#5c7996",
            "button_text": "#FFFFFF",
            "row_highlight": "#D6EAF8",
            "row_highlight_color": "#1B2631",
        }

        # Tworzymy tabelę
        table = JSONTableWidget(json_file=KONFIGURACJE_PRAWNE, styles=custom_styles)

        # Przyciski
        from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QInputDialog

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        add_configuration_btn = table.create_styled_button("Dodaj konfigurację", width=200, height=35)
        add_configuration_btn.clicked.connect(table.add_row_dialog)

        remove_configuration_btn = table.create_styled_button("Usuń konfigurację", width=200, height=35)
        remove_configuration_btn.clicked.connect(table.remove_configuration)

        btn_layout.addWidget(add_configuration_btn)
        btn_layout.addWidget(remove_configuration_btn)
        layout.addLayout(btn_layout)

        parent_widget.layout().addWidget(container)

    def setup_definicje_skladnikow_tab(self):
        definicje_skladnikow = QWidget()
        self.tabs.addTab(definicje_skladnikow, "Definicje składników")



if __name__== "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

