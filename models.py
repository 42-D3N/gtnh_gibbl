from dataclasses import dataclass

@dataclass
class PollutionSource:
    x: int
    y: int
    gain: int
    name: str = "Source"

@dataclass
class InitialPollution:
    x: int
    y: int
    amount: int

@dataclass
class SimulationParameters:
    sources: list[PollutionSource]
    initial_pollutions: list[InitialPollution]
    threshold: int = 400000
    diffusion: float = 0.05
    loss: float = 0.9945
    display_radius: int = 6
    simulation_radius: int = 16
    nb_rounds: int = 1000
