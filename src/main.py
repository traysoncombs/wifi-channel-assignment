import random
from typing import Dict, List

from matplotlib.lines import Line2D

from src.path_loss import Position, PartitionedPathLossModel, FreeSpacePathLossModel, AbstractPathLossModel
from src.sir_constraint import create_and_solve_constraint_problem
from src.transmitter import Channels, Transmitter
from matplotlib import pyplot as plt


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


def create_transmitters(max_x: int, max_y: int, seed: int, num_transmitters: int,
                        path_loss: AbstractPathLossModel, tx_power: float, chs: Channels, ref_power: float) -> List[Transmitter]:
    random.seed(seed)
    transmitters = []
    used_positions = []

    for i in range(num_transmitters):
        # Ensure that each router has a unique position
        position = Position(random.uniform(0, max_x), random.uniform(0, max_y))
        while position in used_positions:
            position = Position(random.randint(0, max_x), random.randint(0, max_y))
        used_positions.append(position)

        transmitters.append(Transmitter(1, tx_power, position, chs, path_loss, ref_power))

    return transmitters

def visualize(transmitters: List[Transmitter], max_line_dist: float):
    x_coords = [tx.position.x for tx in transmitters]
    y_coords = [tx.position.y for tx in transmitters]
    channels = [tx.channel for tx in transmitters]

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_coords, y_coords, 'o')
    for i in range(0, len(transmitters)):
        ax.annotate(str(channels[i]), (x_coords[i], y_coords[i]), color='b')

    for i in range(len(transmitters) - 1):
        for j in range(i + 1, len(transmitters)):
            tx1 = transmitters[i]
            tx2 = transmitters[j]
            if tx1.position.distance(tx2.position) <= max_line_dist:
                ax.plot((tx1.position.x, tx2.position.x), (tx1.position.y, tx2.position.y), 'ro-')
                diff_x, diff_y = tx1.position.x - tx2.position.x, tx1.position.y - tx2.position.y
                ax.annotate(str(round(tx1.get_signal_interference_ratio(tx2), 3)), xy=(tx2.position.x + diff_x/2, tx2.position.y + diff_y/2), fontsize=7)

    ax.grid(True)
    plt.show()

if __name__ == "__main__":
    # path_loss_exponents = crate_random_pl_exponents(100, 100, 20, 20, 2, 3, 1)
    path_loss = FreeSpacePathLossModel(2.5)
    ref_power = -40
    channels = Channels(2402, 11, 20, 5)
    transmitters = create_transmitters(200, 200, 6, 10, path_loss, 10, channels, ref_power)

    problem = create_and_solve_constraint_problem(transmitters, channels, 0.1)

    visualize(problem.__next__(), 100)


    #transmitter1 = Transmitter(1, 10, Position(0, 0), channels, path_loss, ref_power)
    #transmitter2 = Transmitter(1, 10, Position(1, 1), channels, path_loss, ref_power)
    #powa = transmitter1.get_received_power(Position(1, 1))
    #print(powa)
    #inter = transmitter1.get_signal_interference_ratio(transmitter2)
    #print(inter)

    # rx_pos = Position(30, 30)
    # rx_power = transmitter1.get_received_power(rx_pos)
    # pos_at_power = path_loss.position_from_received_power(10, rx_power, Position(0, 0), rx_pos, channels.get_channel_center(1))
    # print(f"rx_power: {rx_power}, estimated rx_position: {pos_at_power}")
