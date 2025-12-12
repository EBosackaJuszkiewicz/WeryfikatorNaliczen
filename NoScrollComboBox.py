from PyQt5.QtWidgets import QComboBox
from PyQt5.QtGui import QWheelEvent # Wymagane, ale nie używane wewnątrz metody

class NoScrollComboBox(QComboBox):
    """
    QComboBox, który ignoruje zdarzenia kółka myszy,
    pozwalając nadrzędnej tabeli na przewijanie.
    """
    def wheelEvent(self, event):
        pass