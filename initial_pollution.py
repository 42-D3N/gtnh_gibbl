from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
)

from models import InitialPollution


class InitialPollutionWidget(QWidget):
    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)

    def __init__(self, pollution: InitialPollution):
        super().__init__()

        self.pollution = pollution

        main_layout = QHBoxLayout(self)

        info_layout = QHBoxLayout()

        self.coords = QLabel(
            f"Chunk ({pollution.x}, {pollution.y})"
        )

        info_layout.addWidget(self.coords)

        self.amount = QSpinBox()
        self.amount.setRange(0, 10_000_000)
        self.amount.setValue(pollution.amount)
        self.amount.setFixedWidth(80)

        self.delete = QPushButton("🗑")

        main_layout.addLayout(info_layout)
        main_layout.addWidget(self.amount)
        main_layout.addWidget(self.delete)

        self.amount.valueChanged.connect(self.on_amount_changed)
        self.delete.clicked.connect(self.on_delete)

    def on_amount_changed(self, value):
        self.pollution.amount = value
        self.changed.emit()

    def on_delete(self):
        self.delete_requested.emit(self)
