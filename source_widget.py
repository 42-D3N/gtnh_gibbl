from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
)

from models import PollutionSource


class SourceWidget(QWidget):
    gain_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)

    def __init__(self, source: PollutionSource):
        super().__init__()

        self.source = source

        main_layout = QHBoxLayout(self)

        info_layout = QHBoxLayout()

        self.name = QLineEdit()
        self.name.setText(source.name)
        self.name.setMaximumWidth(80)

        self.coords = QLabel(
            f"({source.x}, {source.y})"
        )

        info_layout.addWidget(self.name)
        info_layout.addWidget(self.coords)

        self.gain = QSpinBox()
        self.gain.setRange(0, 10_000_000)
        self.gain.setValue(source.gain)
        self.gain.setFixedWidth(80)

        self.delete = QPushButton("🗑")

        main_layout.addLayout(info_layout)
        main_layout.addWidget(self.gain)
        main_layout.addWidget(self.delete)

        self.name.textChanged.connect(self.on_name_changed)
        self.gain.valueChanged.connect(self.on_gain_changed)
        self.delete.clicked.connect(self.on_delete)

    def on_gain_changed(self, value):
        self.source.gain = value
        self.gain_changed.emit()

    def on_name_changed(self, value):
        self.source.name = value
        self.gain_changed.emit()

    def on_delete(self):
        self.delete_requested.emit(self)
