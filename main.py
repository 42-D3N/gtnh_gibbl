import sys
import numpy as np
from dataclasses import dataclass
from simulation import simulate

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSpinBox,
    QPushButton,
    QSlider,
    QScrollArea,
)
from PyQt6.QtCore import (Qt, pyqtSignal)

from source_widget import SourceWidget
from initial_pollution import InitialPollutionWidget
from models import (PollutionSource, InitialPollution, SimulationParameters)

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.image as mpimg
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from enum import Enum

DEFAULT_SIMULATION_RADIUS = 16

class HeatmapCanvas(FigureCanvasQTAgg):
    radius_changed = pyqtSignal(int)
    chunk_clicked = pyqtSignal(int, int)
    def __init__(self):
        self.figure = Figure(figsize=(7, 7))
        super().__init__(self.figure)

        self.history = None
        self.current_frame = 0
        self.vmax = 1
        self.map_radius = 16
        self.view_radius = 6
        self.map_size = self.map_radius * 2 + 1
        self.selected_chunk = None
        self.selection = None
        self.source_markers = None

        self.sources = []
        self.initial_pollutions = []
        self.source_scatter = None
        self.initial_scatter = None

        self.ax = self.figure.add_subplot(111)

        self.background = None
        self.image = None
        self.colorbar = None

        self.ax.set_title("Heatmap")

        self.mpl_connect("scroll_event", self.on_scroll)
        self.mpl_connect("button_press_event", self.on_click)
        self.mpl_connect("motion_notify_event", self.on_mouse_move)

    def create_hover(self):
        self.hover = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(0, 0),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="white"),
            zorder=1000,
        )
        self.hover.set_visible(False)

    def on_mouse_move(self, event):
        if event.inaxes != self.ax:
            if self.hover.get_visible():
                self.hover.set_visible(False)
                self.draw_idle()
            return

        if event.xdata is None or event.ydata is None:
            return

        x = round(event.xdata)
        y = round(event.ydata)

        if x > self.map_radius:
            offset = (-120, 15)
        else:
            offset = (15, 15)
        self.hover.set_position(offset)

        if not (0 <= x < self.map_size and 0 <= y < self.map_size):
            if self.hover.get_visible():
                self.hover.set_visible(False)
                self.draw_idle()
            return

        if self.history is None:
            return

        value = self.history[self.current_frame, y, x]

        self.hover.xy = (x, y)
        self.hover.set_text(
            f"Chunk : ({x}, {y})\nPollution : {value:,.0f}"
        )
        self.hover.set_visible(True)

        self.draw_idle()

    def initialize(self):
        self.ax.clear()
        self.background = mpimg.imread("map.png")
        self.ax.imshow(
            self.background,
            origin="lower",
            extent=(-0.5, self.map_size-0.5, -0.5, self.map_size-0.5)
        )
        empty = np.zeros((self.map_size, self.map_size))
        red_alpha = LinearSegmentedColormap.from_list(
            "RedAlpha",
            [
                (1, 0, 0, 0.0),
                (1, 0, 0, 0.8),
            ]
        )
        self.image = self.ax.imshow(
            empty,
            cmap=red_alpha,
            origin="lower",
            interpolation="nearest",
            vmin=0,
            vmax=1,
            extent=(-0.5, self.map_size-0.5, -0.5, self.map_size-0.5),
        )
        self.colorbar = self.figure.colorbar(
            self.image,
            ax=self.ax
        )
        self.create_hover()
        self.draw()

    def set_view_radius(self, radius):
        if radius == self.view_radius:
            return
        self.view_radius = radius
        self.radius_changed.emit(radius)
        center = self.map_radius
        self.ax.set_xlim(
            center - radius - 0.5,
            center + radius + 0.5
        )
        self.ax.set_ylim(
            center - radius - 0.5,
            center + radius + 0.5
        )

        if self.history is not None:
            self.show_frame(self.current_frame)
        else:
            self.draw()

    def show_frame(self, frame):
        if self.history is None:
            return
        self.current_frame = frame
        visible = self.get_visible_frame(frame)
        self.image.set_data(visible)

        center = self.map_radius
        r = self.view_radius
        self.image.set_extent( (center - r - 0.5, center + r + 0.5, center - r - 0.5, center + r + 0.5 ) )
        self.draw()

    def set_history(self, history):
        self.history = history
        if history is None or len(history) == 0:
            return

        self.vmax = max(history.max(), 400000)
        self.image.set_clim(
            vmin=0,
            vmax=self.vmax
        )
        self.show_frame(0)

    def get_visible_frame(self, frame):
        data = self.history[frame]

        center = self.map_radius
        radius = self.view_radius

        return data[
            center-radius:center+radius+1,
            center-radius:center+radius+1
        ]

    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == "up":
            new_radius = max(1, self.view_radius - 1)
        elif event.button == "down":
            new_radius = min(self.map_radius, self.view_radius + 1)
        else:
            return
        self.set_view_radius(new_radius)

    def update_selection(self):
        if self.selection is not None:
            self.selection.remove()
            self.selection = None
        if self.selected_chunk is None:
            self.draw_idle()
            return
        x, y = self.selected_chunk
        self.selection = Rectangle(
            (x - 0.5, y - 0.5),
            1,
            1,
            fill=False,
            edgecolor="cyan",
            linewidth=2,
        )
        self.ax.add_patch(self.selection)
        self.draw_idle()

    def on_click(self, event):
        if event.inaxes != self.ax:
            self.selected_chunk = None
            self.update_selection()
            self.chunk_clicked.emit(-1, -1)
            return
        if event.xdata is None or event.ydata is None:
            return
        x = round(event.xdata)
        y = round(event.ydata)
        if (self.selected_chunk == (x, y)):
            self.selected_chunk = None
            self.update_selection()
            self.chunk_clicked.emit(-1, -1)
            return
        self.selected_chunk = (x, y)
        self.update_selection()
        self.chunk_clicked.emit(x, y)
    
    def set_sources(self, sources):
        self.sources = sources
        self.update_markers()

    def set_initial_pollutions(self, pollutions):
        self.initial_pollutions = pollutions
        self.update_markers()

    def update_markers(self):
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()

        if self.source_scatter:
            self.source_scatter.remove()
            self.source_scatter = None

        if self.initial_scatter:
            self.initial_scatter.remove()
            self.initial_scatter = None
        if self.sources:
            source_xs = [source.x for source in self.sources]
            source_ys = [source.y for source in self.sources]
            self.source_scatter = self.ax.scatter(
                source_xs,
                source_ys,
                marker="o",
                s=70,
                facecolors="white",
                edgecolors="black",
                linewidths=1.5,
                zorder=10,
            )


        if self.initial_pollutions:
            pollution_xs = [pollution.x for pollution in self.initial_pollutions]
            pollution_ys = [pollution.y for pollution in self.initial_pollutions]
            self.initial_scatter = self.ax.scatter(
                pollution_xs,
                pollution_ys,
                marker="s",
                s=70,
                facecolors="deepskyblue",
                edgecolors="white",
                linewidths=1.5,
                zorder=9,
            )

        self.ax.set_xlim(current_xlim)
        self.ax.set_ylim(current_ylim)
        self.draw_idle()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("GTNH Pollution Simulator")
        self.resize(1200, 800)
        self.sources = []
        self.source_widgets = []
        self.initial_pollutions = []
        self.initial_pollution_widgets = []

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QHBoxLayout()
        self.central.setLayout(self.layout)

        self.left_panel = QWidget()
        self.right_panel = QWidget()
        self.layout.addWidget(self.left_panel)
        self.layout.addWidget(self.right_panel)
        self.left_panel.setFixedWidth(350)

        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)
        self.right_layout = QVBoxLayout()
        self.right_panel.setLayout(self.right_layout)

        self.left_layout.addWidget(QLabel("Nombre de cycles"))
        self.nb_rounds = QSpinBox()
        self.nb_rounds.setRange(1, 100_000_000)
        self.nb_rounds.setValue(1000)
        self.left_layout.addWidget(self.nb_rounds)

        self.left_layout.addWidget(QLabel("Rayon visible"))
        self.view_radius = QSpinBox()
        self.view_radius.setRange(1, 16)
        self.view_radius.setValue(6)
        self.left_layout.addWidget(self.view_radius)

        self.left_layout.addWidget(QLabel("Sources"))
        self.sources_scroll = QScrollArea()
        self.sources_scroll.setWidgetResizable(True)
        self.sources_widget = QWidget()
        self.sources_layout = QVBoxLayout(self.sources_widget)
        self.sources_scroll.setWidget(self.sources_widget)
        self.left_layout.addWidget(self.sources_scroll)

        self.left_layout.addWidget(QLabel("Init Pollution"))
        self.initial_pollutions_scroll = QScrollArea()
        self.initial_pollutions_scroll.setWidgetResizable(True)
        self.initial_pollutions_widget = QWidget()
        self.initial_pollutions_layout = QVBoxLayout(self.initial_pollutions_widget)
        self.initial_pollutions_scroll.setWidget(self.initial_pollutions_widget)
        self.left_layout.addWidget(self.initial_pollutions_scroll)

        self.add_source_button = QPushButton("Ajouter une source")
        self.left_layout.addWidget(self.add_source_button)
        self.add_pollution_button = QPushButton("Ajouter une pollution")
        self.left_layout.addWidget(self.add_pollution_button)

        self.simulate_b = QPushButton("Simuler")
        self.left_layout.addWidget(self.simulate_b)

        self.canvas = HeatmapCanvas()
        self.canvas.radius_changed.connect(self.view_radius.setValue)
        self.right_layout.addWidget(self.canvas)
        self.canvas.initialize()
        self.canvas.set_view_radius(self.view_radius.value())

        empty_history = np.zeros( (1, 33, 33) )
        self.canvas.set_history(empty_history)

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(0)
        self.right_layout.addWidget(self.time_slider)

        self.left_layout.addStretch()
        self.simulate_b.clicked.connect(self.run_simulation)
        self.view_radius.valueChanged.connect(self.canvas.set_view_radius)
        self.time_slider.valueChanged.connect(self.canvas.show_frame)
        self.add_source_button.clicked.connect(self.add_source)
        self.add_pollution_button.clicked.connect(self.add_initial_pollution)
        self.update_sources_height()
        self.update_init_pollution_height()

    def get_parameters(self):
        return SimulationParameters(
            sources=self.sources,
            initial_pollutions=self.initial_pollutions,
            display_radius=self.view_radius.value(),
            simulation_radius=DEFAULT_SIMULATION_RADIUS,
            nb_rounds=self.nb_rounds.value(),
        )

    def run_simulation(self):
        params = self.get_parameters()
        self.canvas.set_view_radius(params.display_radius)
        history = simulate(params)
        self.set_history(history)

    def set_history(self, history):
        self.canvas.set_history(history)
        self.time_slider.setMaximum(len(history)-1)
        self.time_slider.setValue(0)

    def update_sources_height(self):
        max_height = 250
        row_height = 55
        margin = 10
        wanted = len(self.source_widgets) * row_height + margin
        self.sources_scroll.setFixedHeight(min(max_height, max(60, wanted)))

    def update_init_pollution_height(self):
        max_height = 250
        row_height = 55
        margin = 10
        wanted = len(self.initial_pollution_widgets) * row_height + margin
        self.initial_pollutions_scroll.setFixedHeight(min(max_height, max(60, wanted)))

    def add_source(self):
        if self.canvas.selected_chunk is None:
            return

        x, y = self.canvas.selected_chunk

        source = PollutionSource(name=f"Source {len(self.sources)+1}", x=x, y=y, gain=800,)
        self.sources.append(source)
        self.canvas.selected_chunk = None
        self.canvas.update_selection()
        self.canvas.set_sources(self.sources)
        widget = SourceWidget(source)
        self.source_widgets.append(widget)
        self.sources_layout.addWidget(widget)
        widget.delete_requested.connect(self.remove_source)
        self.update_sources_height()

    def remove_source(self, widget):
        self.sources.remove(widget.source)
        self.source_widgets.remove(widget)
        widget.setParent(None)
        widget.deleteLater()
        self.canvas.set_sources(self.sources)
        self.update_sources_height()

    def add_initial_pollution(self):
        if self.canvas.selected_chunk is None:
            return

        x, y = self.canvas.selected_chunk

        pollution = InitialPollution(
            x=x,
            y=y,
            amount=125000,
        )

        self.initial_pollutions.append(pollution)

        self.canvas.selected_chunk = None
        self.canvas.update_selection()

        widget = InitialPollutionWidget(pollution)
        self.initial_pollution_widgets.append(widget)
        self.initial_pollutions_layout.addWidget(widget)

        widget.changed.connect(self.on_initial_pollutions_changed)
        widget.delete_requested.connect(self.remove_initial_pollution)

        self.canvas.set_initial_pollutions(self.initial_pollutions)
        self.update_init_pollution_height()

    def remove_initial_pollution(self, widget):
        pollution = widget.pollution
    
        self.initial_pollutions.remove(pollution)
        self.initial_pollution_widgets.remove(widget)
    
        widget.deleteLater()
    
        self.canvas.set_initial_pollutions(
            self.initial_pollutions
        )

    def on_initial_pollutions_changed(self):
        self.canvas.set_initial_pollutions(self.initial_pollutions)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
