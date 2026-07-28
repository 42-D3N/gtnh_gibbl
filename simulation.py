import numpy as np

def create_grid(radius):
    size = radius * 2 + 1
    return np.zeros((size, size))

def propagation_step(grid, x, y, nx, ny, params):
    size = grid.shape[0]

    if 0 <= nx < size and 0 <= ny < size:
        if grid[nx][ny] < grid[x][y] * 5 / 6:
            amount = (
                grid[x][y] - grid[nx][ny]
            ) * params.diffusion

            grid[nx][ny] += amount
            grid[x][y] -= amount

def simulation_step(grid, round_number, params):
    center = params.simulation_radius

    for source in params.sources:
        grid[source.y][source.x] += source.gain

    if round_number % 60 == 0:
        size = grid.shape[0]

        for x in range(size):
            for y in range(size):
                grid[x][y] *= params.loss

                if grid[x][y] >= params.threshold:
                    propagation_step(grid, x, y, x, y - 1, params)
                    propagation_step(grid, x, y, x, y + 1, params)
                    propagation_step(grid, x, y, x - 1, y, params)
                    propagation_step(grid, x, y, x + 1, y, params)

def simulate(params):
    grid = create_grid(params.simulation_radius)
    for pollution in params.initial_pollutions:
        grid[pollution.y][pollution.x] += pollution.amount

    history = [grid.copy()]

    for round_number in range(params.nb_rounds):
        simulation_step(grid, round_number, params)
        history.append(grid.copy())

    return np.array(history)
