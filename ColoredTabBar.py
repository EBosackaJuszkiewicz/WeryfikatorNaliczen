from PyQt5.QtCore import Qt, QRect
from PyQt5.QtWidgets import QTabBar, QStylePainter, QStyleOptionTab
from PyQt5.QtGui import QColor, QPen, QFontMetrics, QPainter


class ColoredTabBar(QTabBar):
    def __init__(self, colors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colors = colors

    def tabColor(self, index):
        return self.colors[index % len(self.colors)]

    from PyQt5.QtWidgets import QTabBar, QStyleOptionTab
    from PyQt5.QtGui import QPainter, QColor, QFontMetrics, QPen
    from PyQt5.QtCore import Qt, QRect

    class ColoredTabBar(QTabBar):
        def __init__(self, colors, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.colors = colors

        def paintEvent(self, event):
            painter = QPainter(self)
            for i in range(self.count()):
                rect = self.tabRect(i)
                color = QColor(self.colors[i % len(self.colors)])
                painter.fillRect(rect, color)

                # Tekst poziomo, wyśrodkowany
                painter.save()
                painter.setPen(QPen(Qt.black))
                font_metrics = QFontMetrics(self.font())
                text = self.tabText(i)
                text_width = font_metrics.horizontalAdvance(text)
                text_height = font_metrics.height()
                x = rect.x() + (rect.width() - text_width) / 2
                y = rect.y() + (rect.height() + text_height) / 2 - font_metrics.descent()
                painter.drawText(QRect(int(x), int(y - text_height), text_width, text_height), Qt.AlignCenter, text)
                painter.restore()

    def setTabBackgroundColor(self, index, color):
        self.setStyleSheet(f"QTabBar::tab:nth-child({index+1}) {{ background: {color.name()}; }}")
