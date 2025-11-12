import random
from typing import Dict

from src.path_loss import Position, PartitionedPathLossModel
from src.transmitter import Channels, Transmitter


def crate_random_pl_exponents(room_length: float, room_width: float, rows: int, cols: int, exp_min: float,
                              exp_max: float, seed: int) -> Dict[Position, int]:
    random.seed(seed)
    path_loss_exponents = {}
    x_step = room_length / cols
    y_step = room_width / rows
    tmp_pos = Position(0, 0)
    for row in range(rows):
        for col in range(cols):
            path_loss_exponents[Position(tmp_pos.x, tmp_pos.y)] = random.uniform(exp_min, exp_max)
            tmp_pos.x = tmp_pos.x + x_step
        tmp_pos.y += y_step

    return path_loss_exponents

if __name__ == "__main__":
    path_loss_exponents = crate_random_pl_exponents(100, 100, 20, 20, 2, 3, 1)
    path_loss = PartitionedPathLossModel(path_loss_exponents, 100, 100)
    channels = Channels(2402, 11, 20, 5)
    transmitter = Transmitter(1, 8, Position(0, 0), channels, path_loss)
    rx_pos = Position(10, 10)
    rx_power = transmitter.get_received_power(rx_pos)
    print(rx_power)
