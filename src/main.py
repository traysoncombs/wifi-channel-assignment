import random
from typing import List

from src.path_loss import Position, FreeSpacePathLossModel, AbstractPathLossModel
from src.transmitter import Channels, Transmitter

from src.sir_constraint import create_and_solve_constraint_problem
from matplotlib import pyplot as plt


def create_transmitters(max_x: int, max_y: int, seed: int, num_transmitters: int,
                        path_loss: AbstractPathLossModel, tx_power: float, chs: Channels, ref_power: float,
                        min_distance: float) -> List[Transmitter]:
    """
    This function creates a pseudorandom list of routers according to the given seed and parameters.
    :param max_x:
    :param max_y:
    :param seed:
    :param num_transmitters:
    :param path_loss:
    :param tx_power:
    :param chs:
    :param ref_power:
    :return:
    """
    random.seed(seed)
    transmitters = []
    used_positions = []
    num_iters = 0

    while len(used_positions) < num_transmitters:
        if num_iters >= 10_000 * num_transmitters:
            raise Exception("Transmitter placement took too long, try a shorter minimum distance, larger room, or less transmitters")
        num_iters += 1
        position = Position(random.uniform(0, max_x), random.uniform(0, max_y))
        continue_flag = False

        for used_position in used_positions:
            if position.distance(used_position) < min_distance:
                continue_flag = True
                break

        if continue_flag:
            continue

        used_positions.append(position)
        transmitters.append(Transmitter(1, tx_power, position, chs, path_loss, ref_power))

    return transmitters


def visualize(transmitters: List[Transmitter], draw_lines: bool):
    """
    This function visualizes the given list of transmitters.
    :param transmitters:
    :return:
    """
    x_coords = [tx.position.x for tx in transmitters]
    y_coords = [tx.position.y for tx in transmitters]
    channels = [tx.channel for tx in transmitters]

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_coords, y_coords, 'o')
    for i in range(0, len(transmitters)):
        ax.annotate(str(channels[i]), (x_coords[i], y_coords[i]), color='b')

    if draw_lines:
        for i in range(len(transmitters) - 1):
            for j in range(i + 1, len(transmitters)):
                tx1 = transmitters[i]
                tx2 = transmitters[j]
                if tx1.get_signal_interference_ratio(tx2) < 1:
                    ax.plot((tx1.position.x, tx2.position.x), (tx1.position.y, tx2.position.y), 'ro-')
                    diff_x, diff_y = tx1.position.x - tx2.position.x, tx1.position.y - tx2.position.y
                    ax.annotate(str(round(tx1.get_signal_interference_ratio(tx2), 3)),
                                xy=(tx2.position.x + diff_x / 2, tx2.position.y + diff_y / 2), fontsize=7)

    ax.grid(True)
    plt.show()


def print_average_sir(transmitters: List):
    total_avg_sir = 0
    print("Transmitter Position        avg_sir")
    for i in range(len(transmitters)):
        tx_avg_sir = 0
        tx1 = transmitters[i]
        for j in range(len(transmitters)):
            if i != j:
                tx2 = transmitters[j]
                tx_avg_sir += tx1.get_signal_interference_ratio(tx2)
        tx_avg_sir = tx_avg_sir / (len(transmitters) - 1)
        print(f"{str(tx1.position):<20}{tx_avg_sir:>12.2f}")
        total_avg_sir += tx_avg_sir
    print(f"total average SIR: {total_avg_sir / len(transmitters)}")

def print_tx_pos_and_channels_for_testing(transmitters: List[Transmitter]):
    positions = "["
    channels = "["
    for tx in transmitters:
        positions += f"{tx.position.x:.2f}, {tx.position.y:.2f};"
        channels += f"{tx.channel},"
    channels += "]"
    positions += "]"
    print(positions)
    print(channels)

if __name__ == "__main__":
    path_loss_exponent = 2.5
    # Determines how far from a transmitter the signal-interference-ratio is calculated
    reference_power = -40
    # The (length, width) of the area in meters
    room_size = (200, 200)
    # The minimum distance between the positions of the randomly generated transmitters.
    min_tx_distance = 20
    # The minimum SIR between any given pair of routers
    # In this case 0 means maximally interfered and 1 means no interference.
    minimum_sir = 0.03
    # If `average` is true then this becomes the minimum average SIR of all transmitters.
    minimum_avg_sir = 0.95
    # Set to true to use total average SIR instead of pairwise minimum
    average = True
    # The random seed used to generate transmitter positions
    seed = 6
    # The number of transmitters to place in the room
    number_of_transmitters = 15
    # The transmission power of each transmitter in DBm
    transmission_power = 10
    # Set to false to skip drawing lines between interfering transmitters within the visualization.
    draw_lines = True

    path_loss = FreeSpacePathLossModel(path_loss_exponent)
    channels = Channels(2402, 11, 20, 5)
    transmitters = create_transmitters(room_size[0], room_size[1], seed, number_of_transmitters, path_loss,
                                       transmission_power, channels, reference_power, min_tx_distance)

    solution = create_and_solve_constraint_problem(transmitters, channels, minimum_sir, average, minimum_avg_sir)
    if solution is None:
        print("No solution found")
        exit(0)
    visualize(solution, draw_lines)
    print_tx_pos_and_channels_for_testing(solution)
    print_average_sir(solution)
