import random
from typing import List

from path_loss import Position, FreeSpacePathLossModel, AbstractPathLossModel
from sir_constraint import create_and_solve_constraint_problem
from transmitter import Channels, Transmitter
from matplotlib import pyplot as plt

def create_transmitters(max_x: int, max_y: int, seed: int, num_transmitters: int,
                        path_loss: AbstractPathLossModel, tx_power: float, chs: Channels, ref_power: float) -> List[Transmitter]:
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

    for i in range(num_transmitters):
        # Ensure that each router has a unique position
        position = Position(random.uniform(0, max_x), random.uniform(0, max_y))
        while position in used_positions:
            position = Position(random.randint(0, max_x), random.randint(0, max_y))
        used_positions.append(position)

        transmitters.append(Transmitter(1, tx_power, position, chs, path_loss, ref_power))

    return transmitters

def visualize(transmitters: List[Transmitter]):
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

    for i in range(len(transmitters) - 1):
        for j in range(i + 1, len(transmitters)):
            tx1 = transmitters[i]
            tx2 = transmitters[j]
            if tx1.get_signal_interference_ratio(tx2) < 1:
                ax.plot((tx1.position.x, tx2.position.x), (tx1.position.y, tx2.position.y), 'ro-')
                diff_x, diff_y = tx1.position.x - tx2.position.x, tx1.position.y - tx2.position.y
                ax.annotate(str(round(tx1.get_signal_interference_ratio(tx2), 3)), xy=(tx2.position.x + diff_x/2, tx2.position.y + diff_y/2), fontsize=7)

    ax.grid(True)
    plt.show()

if __name__ == "__main__":
    path_loss_exponent = 2.5
    # Determines how far from a transmitter the signal-interference-ratio is calculated
    reference_power = -40
    # The (length, width) of the area in meters
    room_size = (200, 200)
    # The minimum SIR between any given pair of routers
    # In this case 0 means maximally interfered and 1 means no interference.
    # If `average` is true then this becomes the minimum average SIR of all transmitters.
    minimum_sir = 0.055
    # Set to true to use total average SIR instead of pairwise minimum
    average = False
    # The random seed used to generate transmitter positions
    seed = 1
    # The number of transmitters to place in the room
    number_of_transmitters = 15
    # The transmission power of each transmitter
    transmission_power = 10

    path_loss = FreeSpacePathLossModel(path_loss_exponent)
    channels = Channels(2402, 11, 20, 5)
    transmitters = create_transmitters(room_size[0], room_size[1], seed, number_of_transmitters, path_loss, transmission_power, channels, reference_power)

    solution = create_and_solve_constraint_problem(transmitters, channels, minimum_sir, average)
    if solution is None:
        print("No solution found")
        exit(0)
    visualize(solution)

