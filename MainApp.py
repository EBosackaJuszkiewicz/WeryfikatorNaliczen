import os.path
import sys

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QApplication, QTabWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ColoredTabBar import ColoredTabBar
from ComponentConfigWidget import ComponentConfigWidget
from DBTableWidget import DBTableWidget
from JSONTableWidget import JSONTableWidget

CONFIG_FOLDER = "konfiguracje"
KONFIGURACJE_PRAWNE = os.path.join(CONFIG_FOLDER, "konfiguracje_prawne.json")
DEFINICJE_SKŁADNIKÓW = os.path.join(CONFIG_FOLDER, "definicje_składników.json")

class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weryfikator naliczeń")
        self.setFixedSize(1800,950)

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.outer_tabs_colors = [
            "#E8E8ED",  # jasny szary
            "#FFFFFF",  # pastelowy błękit
            "#F2F2F2",  # szary
            "#E3EAF3",  # niebiesko-szary
        ]
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

        konfiguracje_prawne_tab = QWidget()
        konfiguracje_prawne_tab.setLayout(QVBoxLayout())
        self.setup_konfiguracje_prawne_tab(konfiguracje_prawne_tab)

        inner_tabs.addTab(konfiguracje_prawne_tab, "Konfiguracje prawne")
        self.apply_tab_colors(inner_tabs, self.inner_tabs_colors)

    def setup_konfiguracje_prawne_tab(self, parent_widget):
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

        table = JSONTableWidget(json_file=KONFIGURACJE_PRAWNE, stretch_columns=False, styles=custom_styles)
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
        """
        Konfiguruje zakładkę 'Definicje składników' używając pionowego układu Master-Detail.
        Master (Góra): Lista KodSL (MasterListWidget).
        Detail (Dół): Tabela parametrów dla wybranego KodSL (DetailTableWidget).
        """

        # 1. Tworzenie kontenera zakładki
        definicje_skladnikow = QWidget()
        self.tabs.addTab(definicje_skladnikow, "Definicje składników")

        # 2. Tworzenie folderu konfiguracji (jeśli nie istnieje)
        if not os.path.exists(CONFIG_FOLDER):
            os.makedirs(CONFIG_FOLDER)

        # 3. Definicja stylów dla tabel (Custom Styles)
        custom_styles = {
            'table_bg': "#FFFFFF",
            'alternate_bg': "#F7F7F7",
            'row_highlight': "#DBEAFE",
            'row_highlight_color': "#111827",
            'header_bg': "#F3F4F6",
            'header_color': "#111827",
            'button_bg': "#F3F4F6",
            'button_border': "#D1D5DB",
            'button_text': "#111827",
            'button_hover': "#E5E7EB"
        }

        # 4. Tworzenie widżetu kontenera Master-Detail
        # Master-Detail Container jest instancją ComponentConfigWidget,
        # która wewnętrznie zarządza MasterListWidget (Góra) i DetailTableWidget (Dół)
        master_detail_container = ComponentConfigWidget(styles=custom_styles)

        # 5. Ustawienie głównego układu dla zakładki
        main_layout = QVBoxLayout(definicje_skladnikow)

        # Usuwamy marginesy, aby widżet Master-Detail wypełnił całą przestrzeń zakładki
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 6. Dodanie kontenera Master-Detail do zakładki
        main_layout.addWidget(master_detail_container)

        # Uwaga: Logika przycisków "Dodaj definicję składnika" i "Usuń konfigurację"
        # została PRZENIESIONA do klasy ComponentConfigWidget (lub MasterListWidget),
        # aby znajdowała się bezpośrednio pod listą składników, którą modyfikuje.
        # W tym miejscu nie dodajemy już żadnych przycisków.



if __name__== "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

