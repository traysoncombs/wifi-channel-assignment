import abc
from collections import defaultdict
from math import sqrt
from typing import List, Dict
from numpy import arange

class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance(self, position) -> float:
        return sqrt((self.x - position.x) ^ 2 + (self.y - position.y) ^ 2)

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
    def received_power_at_position(self, tx_power: float, tx_pos: Position, rx_pos: Position) -> float:
        """
        Return the path loss [DBm] between the two positions
        :param tx_power: Transmitter power in dbm
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver
        :return: The path loss between the two positions in dbm
        """
        pass

    @abc.abstractmethod
    def position_from_received_power(self, tx_power: float, tx_pos: Position, rx_pos: Position) -> float:
        pass

"""
An implementation of the partitioned path loss model.

This model operates under a lot of assumptions.
   1. The room being modelled is `room_length` x `room_width`
   2. The exponents are somewhat evenly distributed.
"""
class PartitionedPathLossModel(AbstractPathLossModel):
    def __init__(self, ref_path_loss: float, exponent_positions: Dict[Position, float], room_length: float,
                 room_width: float):
        self.ref_path_loss = ref_path_loss
        self.exponent_positions = exponent_positions
        self.room_length = room_length
        self.room_width = room_width
        self.chunk_size = 1000
        pass

    def _get_path_loss_key_near_position(self, position: Position) -> Position:
        """
        Internal function to inefficiently retrieve the position of the
        nearest path loss exponent to `position`.
        :param position:
        :return:
        """

        smallest_dist = 0
        smallest_pos = Position(position.x,position.y)

        for e_pos in self.exponent_positions.keys():
            tmp_dist = e_pos.distance(position)
            if tmp_dist < smallest_dist:
                smallest_dist = tmp_dist
                smallest_pos = e_pos

        return smallest_pos

    def _get_path_loss_in_direction(self, position: Position, in_y_direction: bool) -> Position:
        """
        Internal function to retrieve the next nearest path loss exponent in the positive direction.

        This should only be called once position.[x,y] > the [x,y] position of the nearest path loss exponent.
        :param position: The position from which you want to find the next path loss exponent.
        :param in_y_direction: Set to true to go in the y-direction
        :return:
        """
        nearest = self._get_path_loss_key_near_position(position)

        # Ensure the function is being called correctly
        if in_y_direction:
            assert abs(nearest.y - position.y) < self.dy
        else:
            assert abs(nearest.x - position.x) < self.dx
        # Will point to the position of the PL exponent in the given direction
        direction = nearest
        # I forget how python objects work so thi may or may not be necessary
        # TODO: figure out if this is needed
        tmp_position = Position(position.x, position.y)

        max_iters = round(self.room_length / self.dx)
        if in_y_direction:
            max_iters = round(self.room_width / self.dy)

        for _ in range(max_iters):
            if in_y_direction:
                tmp_position.y += self.dy
            else:
                tmp_position.x += self.dx
            direction = self._get_path_loss_key_near_position(nearest)

        return direction


    def received_power_at_position(self, tx_power: float, tx_pos: Position, rx_pos: Position):
        """
        Computes the path loss between the two positions by breaking it into chunks and using the nearest
        path loss exponent for each chunk.
        :param tx_power:
        :param tx_pos:
        :param rx_pos:
        :return:
        """
        step = Position((tx_pos.x - rx_pos.x) / self.chunk_size, (tx_pos.y - rx_pos.y) / self.chunk_size)

        tmp_pos = Position(tx_pos.x, tx_pos.y)

        total_path_loss = 0
        while tmp_pos.x != rx_pos:
            pl_near_tmp_pos = self._get_path_loss_key_near_position(tmp_pos)
            # TODO: Compute path loss for each chunk and add to total

            tmp_pos = tmp_pos + step


