# component_config_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from master_list_widget import MasterListWidget
from detail_table_widget import DetailTableWidget


class ComponentConfigWidget(QWidget):
    def __init__(self, styles, parent=None):
        super().__init__(parent)
        self.styles = styles

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Ustawienie marginesów na 0

        # UTWORZENIE SPLITTERA PIONOWEGO (Góra/Dół)
        splitter = QSplitter(Qt.Vertical)

        # 1. Master: Lista KodSL (Góra)
        self.master_widget = MasterListWidget(self.styles)

        # 2. Detail: Tabela Parametrów (Dół)
        self.detail_widget = DetailTableWidget(self.styles)
        self.detail_widget.init_table_structure()

        # Dodanie obu widżetów do Splittera
        splitter.addWidget(self.master_widget)
        splitter.addWidget(self.detail_widget)

        # Ustawienie proporcji
        splitter.setSizes([200, 500])

        # 3. Dodanie przycisków do Master (Zarządzanie Składnikami)
        # Przenosimy przyciski tu, bo to Master zarządza listą KodSL.
        # MasterListWidget musi mieć metody add_component/remove_component.

        # --- Przyciski (Kontrola Mastera) ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        # Używamy metody create_styled_button z DetailTableWidget jako pomocniczej
        # Wymaga importu jakiejś klasy bazowej (np. DBTableWidget/JSONTableWidget)
        # jeśli zdefiniowałaś tę metodę tylko tam. Zakładam, że możesz to przenieść
        # do klasy pomocniczej lub użyjemy tu prostego QPushButton.

        # Aby uniknąć problemów z importami, użyjemy zwykłych przycisków
        add_component_btn = QPushButton("Dodaj definicję składnika")
        remove_component_btn = QPushButton("Usuń konfigurację")

        # Musisz zaimplementować te metody w MasterListWidget
        # add_component_btn.clicked.connect(self.master_widget.add_component_dialog)
        # remove_component_btn.clicked.connect(self.master_widget.remove_component)

        btn_layout.addWidget(add_component_btn)
        btn_layout.addWidget(remove_component_btn)

        # Dodajemy Master i przyciski do układu
        master_container = QVBoxLayout()
        master_container.setContentsMargins(0, 0, 0, 0)
        master_container.addWidget(self.master_widget)
        master_container.addLayout(btn_layout)

        # 4. Połączenie sygnału Master-Detail
        self.master_widget.variantSelected.connect(self.detail_widget.load_variant_data)

        # Wymiana Master_widget na master_container w splitterze,
        # ale QSplitter nie przyjmuje layoutów bezpośrednio.
        # Musimy opakować master_container w QWidget.

        master_wrapper = QWidget()
        master_wrapper.setLayout(master_container)

        # Nowy Splitter:
        splitter_final = QSplitter(Qt.Vertical)
        splitter_final.addWidget(master_wrapper)
        splitter_final.addWidget(self.detail_widget)
        splitter_final.setSizes([250, 450])

        main_layout.addWidget(splitter_final)

        # Uruchomienie ładowania dla pierwszego elementu
        if self.master_widget.rowCount() > 0:
            initial_kod_sl = self.master_widget.variant_names[0]
            self.detail_widget.load_variant_data(initial_kod_sl)