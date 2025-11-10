import abc
from collections import defaultdict
from math import sqrt
from typing import List, Dict
from numpy import arange

class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance(self, position: Position) -> float:
        return sqrt((self.x - position.x) ^ 2 + (self.y - position.y) ^ 2)

    def __hash__(self):
        return hash((self.x, self.y))

"""
Base class for creating a path loss model
"""


class AbstractPathLossModel(abc.ABC):
    @abc.abstractmethod
    def path_loss_between_positions(self, tx_power: float, tx_pos: Position, rx_pos: Position) -> float:
        """
        Return the path loss between the two positions
        :param tx_power: Transmitter power in dbm
        :param tx_pos: The position of the transmitter
        :param rx_pos: The position of the receiver
        :return: The path loss between the two positions in dbm
        """
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
        self.dx = room_length / 50
        self.dy = room_width / 30
        pass

    def _build_path_loss_table(self, dx: float, dy: float) -> Dict[Position, float]:
        """
        Create a lookup table for interpolated path loss exponents.
        :return:
        """

        table = {}
        for y in arange(0, dy, self.room_width):
            nearest_pl_pos_x = self._get_path_loss_key_near_position(Position(0, y))
            # initially the path loss in the negative x-direction is unknown
            # so we're just assuming it's 10% less than the nearest
            nearest_pl_val_x = self.exponent_positions[nearest_pl_pos_x] * 0.9

            next_pl_pos_x = self._get_path_loss_in_direction(nearest_pl_pos_x, False)
            next_pl_val_x = self.exponent_positions[nearest_pl_pos_x]
            for x in arange(0, dx, self.room_length):
                if x >= nearest_pl_pos_x.x:
                    nearest_pl_pos_x = self._get_path_loss_key_near_position(Position(x, y))
                    nearest_pl_val_x = self.exponent_positions[nearest_pl_pos_x]

                    next_pl_pos_x = self._get_path_loss_in_direction(nearest_pl_pos_x, False)
                    next_pl_val_x = self.exponent_positions[nearest_pl_pos_x]

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


    def path_loss_between_positions(self, tx_power: float, tx_pos: Position, rx_pos: Position):
        pass

    def get_nearest_path_loss_exponent(self, pos: Position) -> float:


