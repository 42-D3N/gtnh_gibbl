from copy import deepcopy
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.image as mpimg
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np

THRESHOLD = 400000
DIFF = 0.05
LOSS = 0.9945
GAIN = 800
DEPTH = 6
SIZE = DEPTH * 2 + 1
CENTER = DEPTH
GRID = [[0.0 for _ in range(SIZE)] for _ in range(SIZE)]
NB_ROUNDS = 64 * 16 * 60
DIRECTIONS = [ (0, -1), (0, 1), (-1, 0), (1, 0) ]

def propagation_step(grid, x, y, nx, ny):
    if nx < SIZE and nx >= 0 and ny < SIZE and ny >= 0:
        if grid[nx][ny] < grid[x][y] * 5/6:
            amount = (grid[x][y] - grid[nx][ny]) * DIFF
            grid[nx][ny] += amount
            grid[x][y] -= amount

def simulation_step(grid, round_number):
    if round_number < 3840:
        grid[CENTER][CENTER] += GAIN
    if round_number % 60 == 0:
        for i in range(SIZE):
            for j in range(SIZE):
                grid[i][j] *= LOSS
                if grid[i][j] >= 400000:
                    propagation_step(grid, i, j, i, j - 1)
                    propagation_step(grid, i, j, i, j + 1)
                    propagation_step(grid, i, j, i - 1, j)
                    propagation_step(grid, i, j, i + 1, j)

def update(value):
    frame = int(slider.val)
    image.set_data(history[frame])
    ax.set_title(f"Seconde {frame}")
    fig.canvas.draw_idle()

def format_value(value):
    if value == 0:
        return f"{0:10.0f}"
    if value >= 1_000_000:
        if value < 2000000:
            return f"\033[38;2;255;0;0m{value/1_000_000:9.1f}M\033[0m"
        else:
            return f"\033[38;2;179;0;255m{value/1_000_000:9.1f}M\033[0m"
    if value >= 1_000:
        if value < 400000:
            return f"{value/1_000:9.1f}k"
        elif value < 500000:
            return f"\033[38;2;0;255;0m{value/1_000:9.1f}k\033[0m"
        elif value < 750000:
            return f"\033[38;2;255;255;0m{value/1_000:9.1f}k\033[0m"
        else:
            return f"\033[38;2;255;157;0m{value/1_000:9.1f}k\033[0m"
    if value > 0:
        return f"{value:10.0f}"
    print(value)
    return f"         {str(int(value))}"

def print_map(GRID):
    for row in GRID:
        print(" ".join(format_value(v) for v in row))
    print("-" * (DEPTH * 11 * 2 + 10))

history = [deepcopy(GRID)]

for round_number in range(NB_ROUNDS):
    simulation_step(GRID, round_number)
    history.append(deepcopy(GRID))

red_alpha = LinearSegmentedColormap.from_list(
    "RedAlpha",
    [ (1, 0, 0, 0.0), (1, 0, 0, 0.8), ]
)
background = mpimg.imread("map.png")
history = np.array(history)
fig, ax = plt.subplots(figsize=(7,7))
plt.subplots_adjust(bottom=0.20)
vmax = history.max()
ax.imshow(
    background,
    origin="lower",
    extent=(-0.5, SIZE-0.5, -0.5, SIZE-0.5)
)
image = ax.imshow(
    history[0],
    cmap=red_alpha,
    origin="lower",
    interpolation="nearest",
    vmin=0,
    vmax=vmax
)

def format_cursor_data(value):
    return f""

def format_coord(x, y):
    ix = int(round(x))
    iy = int(round(y))
    if 0 <= ix < SIZE and 0 <= iy < SIZE:
        value = int(history[int(slider.val), iy, ix])
        return f"Chunk ({ix}, {iy}) | Pollution : {value:,} gibbl".replace(",", " ")
    return ""

ax.format_coord = format_coord
image.format_cursor_data = format_cursor_data
plt.colorbar(image)
ax_slider = plt.axes([0.15, 0.05, 0.7, 0.03])
slider = Slider(
    ax_slider,
    "Seconde",
    0,
    len(history)-1,
    valinit=0,
    valstep=1
)
slider.on_changed(update)
plt.show()
