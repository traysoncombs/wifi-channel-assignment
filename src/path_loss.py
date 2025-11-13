import abc
import math
from collections import defaultdict
from math import sqrt, log10
from typing import List, Dict

from numpy import arange


class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance(self, position) -> float:
        return sqrt((self.x - position.x) ** 2 + (self.y - position.y) ** 2)

    def mag(self):
        return sqrt(self.x ** 2 + self.y ** 2)

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


"""
Base class for creating a path loss model
"""


class AbstractPathLossModel(abc.ABC):
    @abc.abstractmethod
    def received_power_at_position(self, tx_power: float, tx_pos: Position, rx_pos: Position, frequency: float):
        """
        Return the path loss [DBm] between the two positions
        :param frequency: The center frequency of the signal in MHz
        :param tx_power: Transmitter power in dbm
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver
        :return: The path loss between the two positions in dbm
        """
        pass

    @abc.abstractmethod
    def position_from_received_power(self, tx_power: float, rx_power: float, tx_pos: Position, rx_pos: Position,
                                     frequency: float) -> float:
        pass


"""
An implementation of the partitioned path loss model.

This model operates under a lot of assumptions.
   1. The room being modelled is `room_length` x `room_width`
   2. The exponents are somewhat evenly distributed.
"""


class PartitionedPathLossModel(AbstractPathLossModel):
    def __init__(self, exponent_positions: Dict[Position, float], room_length: float,
                 room_width: float):
        # self.exponent_positions[`position`] = path loss exponent at `position`
        self.exponent_positions = exponent_positions
        self.room_length = room_length
        self.room_width = room_width
        self.chunk_size = 3
        pass

    def _get_path_loss_near_position(self, position: Position) -> float:
        """
        Internal function to inefficiently retrieve the position of the
        nearest path loss exponent to `position`.
        :param position:
        :return:
        """

        smallest_dist = 2 ** 32
        smallest_pos = Position(position.x, position.y)

        for e_pos in self.exponent_positions.keys():
            tmp_dist = e_pos.distance(position)
            if tmp_dist < smallest_dist:
                smallest_dist = tmp_dist
                smallest_pos = e_pos

        return self.exponent_positions[smallest_pos]

    def received_power_at_position(self, tx_power: float, tx_pos: Position, rx_pos: Position,
                                   frequency: float) -> Position:
        """
        Computes the path loss between the two positions by breaking it into chunks and using the nearest
        path loss exponent for each chunk.
        :param frequency: The center frequency of the signal in MHz
        :param tx_power: transmission power in DBm
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver
        :return:
        """
        ref_distance = 0.1
        step = Position((rx_pos.x - tx_pos.x) / self.chunk_size, (rx_pos.y - tx_pos.y) / self.chunk_size)
        step_size = step.mag()
        tmp_pos = Position(tx_pos.x, tx_pos.y)

        # P_r = P_tx + +G_tx + G_rx + 20*log_10(lambda/(4pi*d))
        wavelength = (3 * 10 ** 8) / (frequency * 10 ** 6)
        # Convert tx power to linear and compute rx power at ref distance
        rx_power_at_1_meter = (10 ** (tx_power / 10)) * ((wavelength / (4 * math.pi * ref_distance)) ** 2)
        total_rx_power = rx_power_at_1_meter
        # The reference distance has already been computed so we can add it.
        ref_step = Position(step.x * (ref_distance / step_size), step.y * (ref_distance / step_size))
        tmp_pos + ref_step

        for i in range(1, self.chunk_size + 1):
            pl_near_tmp_pos = self._get_path_loss_near_position(tmp_pos)
            # TODO: Compute path loss for each chunk and add to total

            # total_rx_power += (pl_near_tmp_pos * log10(step_size))
            # Compute power lost along each chunk
            total_rx_power -= (step_size ** pl_near_tmp_pos)

            tmp_pos = tmp_pos + step
        assert abs(tmp_pos.x - rx_pos.x) < 0.00001
        assert abs(tmp_pos.y - rx_pos.y) < 0.00001

        return 0 if total_rx_power < 0 else 10 * log10(total_rx_power)

    def position_from_received_power(self, tx_power: float, rx_power: float, tx_pos: Position, rx_pos: Position,
                                     frequency: float) -> float:
        pass


class FreeSpacePathLossModel(AbstractPathLossModel):
    def __init__(self, pl_exp):
        self.pl_exp = pl_exp

    def received_power_at_position(self, tx_power: float, tx_pos: Position, rx_pos: Position, frequency: float):
        """
        Computes the path loss between the two positions using the free space path loss model.
        :param frequency: The center frequency of the signal in MHz
        :param tx_power: transmission power in DBm
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver
        :return:
        """
        path = Position((rx_pos.x - tx_pos.x), (rx_pos.y - tx_pos.y))
        distance = path.mag()

        # I couldn't get this calculation to work in db scale
        # so we convert to linear and back... very efficient
        wavelength = (3 * 10 ** 8) / (frequency * 10 ** 6)
        rx_power_linear = (10**(tx_power/10)) * (wavelength / (4 * math.pi * distance)) ** self.pl_exp
        return 10 * log10(rx_power_linear)

    def position_from_received_power(self, tx_power: float, rx_power: float, tx_pos: Position, rx_pos: Position,
                                     frequency: float) -> Position:
        path = Position((rx_pos.x - tx_pos.x), (rx_pos.y - tx_pos.y))
        path_mag = path.mag()

        wavelength = (3 * 10 ** 8) / (frequency * 10 ** 6)
        rx_power_linear = 10 ** (rx_power / 10)
        tx_power_linear = 10 ** (tx_power / 10)
        # Compute distance using FSPL with our exponent
        distance = wavelength / (4 * math.pi * ((rx_power_linear/tx_power_linear) ** (1/self.pl_exp)))

        scale_factor = distance / path_mag
        return Position(path.x * scale_factor, path.y * scale_factor)
