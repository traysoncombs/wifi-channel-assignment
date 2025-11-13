import random
from typing import Dict

from src.path_loss import Position, PartitionedPathLossModel, FreeSpacePathLossModel
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
    #path_loss_exponents = crate_random_pl_exponents(100, 100, 20, 20, 2, 3, 1)
    path_loss = FreeSpacePathLossModel(2.5)
    ref_power = -40
    channels = Channels(2402, 11, 20, 5)
    transmitter1 = Transmitter(1, 10, Position(0, 0), channels, path_loss, ref_power)
    transmitter2 = Transmitter(1, 10, Position(1, 1), channels, path_loss, ref_power)
    powa = transmitter1.get_received_power(Position(1, 1))
    print(powa)
    inter= transmitter1.get_signal_interference(transmitter2)
    print(inter)

    #rx_pos = Position(30, 30)
    #rx_power = transmitter1.get_received_power(rx_pos)
    #pos_at_power = path_loss.position_from_received_power(10, rx_power, Position(0, 0), rx_pos, channels.get_channel_center(1))
    #print(f"rx_power: {rx_power}, estimated rx_position: {pos_at_power}")
